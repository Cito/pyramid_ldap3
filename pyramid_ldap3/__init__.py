
import logging

from time import time

from pyramid.exceptions import ConfigurationError

try:
    import ldap3
except ImportError:  # pragma: no cover
    # this is for benefit of being able to build the docs on rtd.org
    class _Ldap3Module(object):
        LDAPException = Exception
        SEARCH_SCOPE_BASE_OBJECT = None
        SEARCH_SCOPE_SINGLE_LEVEL = None
        SEARCH_SCOPE_WHOLE_SUBTREE = None
        STRATEGY_REUSABLE_THREADED = None
    ldap3 = _Ldap3Module()

logger = logging.getLogger(__name__)


_ord = ord if str is bytes else int

_escape_for_search = {
    '*': '\\2A', '(': '\\28', ')': '\\29', '\\': '\\5C', '\0': '\\00'}


def escape_for_search(s):
    """Escape search string for LDAP according to RFC4515 when necessary."""
    if not s:
        return s
    if isinstance(s, bytes):
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError:
            return ''.join('\\%02x' % _ord(b) for b in s)
    return ''.join((_escape_for_search.get(c, c) for c in s))


class _LDAPQuery(object):
    """Represents an LDAP query.

    Provides rudimentary in-RAM caching of query results.
    """

    def __init__(self, base_dn, filter_tmpl, scope, attributes, cache_period):
        self.base_dn = base_dn
        self.filter_tmpl = filter_tmpl
        self.scope = scope
        self.attributes = attributes
        self.cache_period = cache_period
        self.last_timeslice = 0
        self.cache = {}

    def __str__(self):
        return ('base_dn={base_dn}, filter_tmpl={filter_tmpl}, '
                'scope={scope}, attributes={attributes}, '
                'cache_period={cache_period}'.format(**self.__dict__))

    def query_cache(self, cache_key):
        now = time()
        ts = _timeslice(self.cache_period, now)

        if ts > self.last_timeslice:
            logger.debug(
                'dumping cache; now ts: %r, last_ts: %r',
                ts, self.last_timeslice)
            self.cache = {}
            self.last_timeslice = ts

        return self.cache.get(cache_key)

    def execute(self, conn, **kw):
        cache_key = (self.base_dn % kw, self.filter_tmpl % kw)

        logger.debug('searching for %r', cache_key)

        result = self.query_cache(cache_key) if self.cache_period else None
        if result is None:
            ret = conn.search(
                search_scope=self.scope,
                attributes=self.attributes, *cache_key)
            result, ret = conn.get_response(ret)
            if result is None:
                result = []
            else:
                result = [(r['dn'], r['attributes']) for r in result
                          if 'dn' in r]
                if self.cache_period:
                    self.cache[cache_key] = result
        else:
            logger.debug('result for %r retrieved from cache', cache_key)

        logger.debug('search result: %r', result)

        return result


def _timeslice(period, when=None):
    if when is None:  # pragma: no cover
        when = time()
    return when - (when % period)


class ConnectionManager(object):
    """Provides API methods for managing LDAP connections."""

    # noinspection PyShadowingNames
    def __init__(
            self, uri, bind=None, passwd=None, tls=None,
            use_pool=True, pool_size=10, pool_lifetime=3600, ldap3=ldap3):
        self.ldap3 = ldap3
        uris = uri if isinstance(uri, (list, tuple)) else uri.split()
        self.uri = uri[0] if len(uris) == 1 else uris
        servers = []
        for uri in uris:
            try:
                schema, host = uri.split('://', 1)
            except ValueError:
                schema, host = 'ldap', uri
            use_ssl = schema == 'ldaps'
            try:
                host, port = host.split(':', 1)
                port = int(port)
            except ValueError:
                host, port = host, 636 if use_ssl else 389
            server = self.ldap3.Server(
                host, port=port, use_ssl=use_ssl, tls=tls)
            servers.append(server)
        self.server = servers[
            0] if len(servers) == 1 else self.ldap3.ServerPool(servers)
        self.bind, self.passwd = bind, passwd
        if use_pool:
            self.strategy = ldap3.STRATEGY_REUSABLE_THREADED
            self.pool_name = 'pyramid_ldap3'
            self.pool_size = pool_size
            self.pool_lifetime = pool_lifetime
        else:
            self.strategy = ldap3.STRATEGY_ASYNC_THREADED
            self.pool_name = self.pool_size = self.pool_lifetime = None

    def __str__(self):
        return ('uri={uri}, bind={bind}/{passwd},pool={pool_size}'.format(
            **self.__dict__))

    def connection(self, user=None, password=None):
        if user:
            conn = self.ldap3.Connection(
                self.server, user=user, password=password,
                client_strategy=ldap3.STRATEGY_SYNC,
                auto_bind=True, lazy=False, read_only=True)
        else:
            conn = self.ldap3.Connection(
                self.server, user=self.bind, password=self.passwd,
                client_strategy=self.strategy,
                pool_name=self.pool_name, pool_size=self.pool_size,
                pool_lifetime=self.pool_lifetime,
                auto_bind=True, lazy=False, read_only=True)
        return conn


class Connector(object):
    """Provides API methods for accessing LDAP authentication information."""

    def __init__(self, registry, manager):
        self.registry = registry
        self.manager = manager

    def authenticate(self, login, password):
        """Validate the given login name and password.

        Given a login name and a password, return a tuple of ``(dn,
        attrdict)`` if the matching user if the user exists and his password
        is correct.  Otherwise return ``None``.

        In a ``(dn, attrdict)`` return value, ``dn`` will be the
        distinguished name of the authenticated user.  Attrdict will be a
        dictionary mapping LDAP user attributes to sequences of values.

        A zero length password will always be considered invalid since it
        results in a request for "unauthenticated authentication" which should
        not be used for LDAP based authentication. See `section 5.1.2 of
        RFC-4513 <http://tools.ietf.org/html/rfc4513#section-5.1.2>`_ for a
        description of this behavior.

        If :meth:`pyramid.config.Configurator.ldap_set_login_query` was not
        called, using this function will raise an
        :exc:`pyramid.exceptions.ConfiguratorError`.
        """

        if password == '':
            return None

        search = getattr(self.registry, 'ldap_login_query', None)
        if search is None:
            raise ConfigurationError(
                'ldap_set_login_query was not called during setup')

        with self.manager.connection() as conn:
            result = search.execute(conn, login=login, password=password)

        if not result or len(result) > 1:
            return None
        result = result[0]
        login_dn = result[0]

        try:
            self.manager.connection(login_dn, password).unbind()
        except ldap3.LDAPException:
            logger.debug(
                'Exception in authenticate with login %r', login,
                exc_info=True)
            return None

        return result

    def user_groups(self, userdn):
        """Get the groups the user belongs to.

        Given a user DN, return a sequence of LDAP attribute dictionaries
        matching the groups of which the DN is a member.  If the DN does not
        exist, return ``None``.

        In a return value ``[(dn, attrdict), ...]``, ``dn`` will be the
        distinguished name of the group.  Attrdict will be a dictionary
        mapping LDAP group attributes to sequences of values.

        If :meth:`pyramid.config.Configurator.ldap_set_groups_query` was not
        called, using this function will raise an
        :exc:`pyramid.exceptions.ConfiguratorError`

        """
        search = getattr(self.registry, 'ldap_groups_query', None)
        if search is None:
            raise ConfigurationError(
                'set_ldap_groups_query was not called during setup')
        with self.manager.connection() as conn:
            try:
                result = search.execute(conn, userdn=escape_for_search(userdn))
            except ldap3.LDAPException:
                logger.debug(
                    'Exception in user_groups with userdn %r', userdn,
                    exc_info=True)
                return None

        return result


def ldap_set_login_query(
        config, base_dn, filter_tmpl,
        scope=ldap3.SEARCH_SCOPE_SINGLE_LEVEL, attributes=None,
        cache_period=0):
    """Configurator method to set the LDAP login search.

    ``base_dn`` is the DN at which to begin the search.
    ``filter_tmpl`` is a string which can be used as an LDAP filter:
    it should contain the replacement value ``%(login)s``.
    ``scope`` is any valid LDAP scope value
    (e.g. ``ldap3.SEARCH_SCOPE_SINGLE_LEVEL``).
    ``attributes`` is a list of attributes that shall be returned
    (can also be set to None or ``ldap3.ALL_ATTRIBUTES``).
    ``cache_period`` is the number of seconds to cache login search results;
    if it is 0, login search results will not be cached.

    Example::

        config.set_ldap_login_query(
            base_dn='CN=Users,DC=example,DC=com',
            filter_tmpl='(sAMAccountName=%(login)s)',
            scope=ldap3.SEARCH_SCOPE_SINGLE_LEVEL)

    The registered search must return one and only one value to be considered
    a valid login.
    """

    query = _LDAPQuery(base_dn, filter_tmpl, scope, attributes, cache_period)

    def register():
        config.registry.ldap_login_query = query

    intr = config.introspectable(
        'pyramid_ldap3 login query',
        None,
        str(query),
        'pyramid_ldap3 login query')

    config.action('ldap-set-login-query', register, introspectables=(intr,))


def ldap_set_groups_query(
        config, base_dn, filter_tmpl,
        scope=ldap3.SEARCH_SCOPE_WHOLE_SUBTREE, attributes=None,
        cache_period=0):
    """ Configurator method to set the LDAP groups search.

    ``base_dn`` is the DN at which to begin the search.
    ``filter_tmpl`` is a string which can be used as an LDAP filter:
    it should contain the replacement value ``%(userdn)s``.
    ``scope`` is any valid LDAP scope value
    (e.g. ``ldap3.SEARCH_SCOPE_SINGLE_LEVEL``).
    ``attributes`` is a list of attributes that shall be returned
    (can also be set to None or ``ldap3.ALL_ATTRIBUTES``).
    ``cache_period`` is the number of seconds to cache groups search results;
    if it is 0, groups search results will not be cached.

    Example::

        config.set_ldap_groups_query(
            base_dn='CN=Users,DC=example,DC=com',
            filter_tmpl='(&(objectCategory=group)(member=%(userdn)s))'
            scope=ldap3.SEARCH_SCOPE_WHOLE_SUBTREE)

    """

    query = _LDAPQuery(base_dn, filter_tmpl, scope, attributes, cache_period)

    def register():
        config.registry.ldap_groups_query = query

    intr = config.introspectable(
        'pyramid_ldap3 groups query',
        None,
        str(query),
        'pyramid_ldap3 groups query')

    config.action('ldap-set-groups-query', register, introspectables=(intr,))


def ldap_setup(
        config, uri,
        bind=None, passwd=None, use_tls=False,
        use_pool=True, pool_size=10, pool_lifetime=3600):
    """Configurator method to set up an LDAP connection pool.

    - **uri**: ldap server uri(s) **[mandatory]**
    - **bind**: default bind that will be used to bind a connector.
      **default: None**
    - **passwd**: default password that will be used to bind a connector.
      **default: None**
    - **use_tls**: activate TLS when connecting. **default: False**
    - **use_pool**: activates the connection pool. If False, will recreate a
       connector each time. **default: True**
    - **pool_size**: connection pool size. **default: 10**
    - **pool_lifetime**: number of seconds before recreating a new connection
       when using a connection pool.  **default: 3600**
    """

    manager = ConnectionManager(
        uri, bind, passwd, use_tls, use_pool,
        pool_size if use_pool else None, pool_lifetime if use_pool else None)

    def get_connector(request):
        return Connector(request.registry, manager)

    config.set_request_property(get_connector, 'ldap_connector', reify=True)

    intr = config.introspectable(
        'pyramid_ldap3 setup',
        None,
        str(manager),
        'pyramid_ldap3 setup')
    config.action('ldap-setup', None, introspectables=(intr,))


def get_ldap_connector(request):
    """Return the LDAP connector attached to the request.

    If :meth:`pyramid.config.Configurator.ldap_setup` was not called, using
    this function will raise an :exc:`pyramid.exceptions.ConfigurationError`.
    """
    connector = getattr(request, 'ldap_connector', None)
    if connector is None:
        if ldap3.LDAPException is Exception:  # pragma: no cover
            raise ImportError(
                'You must install ldap3 to use an LDAP connector.')
        raise ConfigurationError(
            'You must call Configurator.ldap_setup during setup '
            'to use an LDAP connector.')
    return connector


def get_groups(userdn, request):
    """Raw groupfinder function returning the complete group query result."""
    connector = get_ldap_connector(request)
    return connector.user_groups(userdn)


def groupfinder(userdn, request):
    """Groupfinder function for Pyramid.

    A groupfinder implementation useful in conjunction with out-of-the-box
    Pyramid authentication policies.  It returns the DN of each group
    belonging to the user specified by ``userdn`` to as a principal
    in the list of results; if the user does not exist, it returns None.
    """
    groups = get_groups(userdn, request)
    if groups:
        groups = [r[0] for r in groups]
    return groups


def includeme(config):
    """Set up Configurator methods for pyramid_ldap3."""
    config.add_directive('ldap_setup', ldap_setup)
    config.add_directive('ldap_set_login_query', ldap_set_login_query)
    config.add_directive('ldap_set_groups_query', ldap_set_groups_query)
