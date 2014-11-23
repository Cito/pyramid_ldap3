import unittest

from pyramid import testing
from pyramid.exceptions import ConfigurationError


class Test_includeme(unittest.TestCase):

    def _callFUT(self, config):
        from pyramid_ldap3 import includeme
        includeme(config)

    def test_it(self):
        config = DummyConfig()
        self._callFUT(config)
        self.assertEqual(config.directives,
             ['ldap_setup', 'ldap_set_login_query', 'ldap_set_groups_query'])
        

class Test_get_groups(unittest.TestCase):

    def _callFUT(self, dn, request):
        from pyramid_ldap3 import get_groups
        return get_groups(dn, request)

    def test_no_group_list(self):
        request = testing.DummyRequest()
        request.ldap_connector = DummyLDAPConnector('testdn', None)
        result = self._callFUT('testdn', request)
        self.assertTrue(result is None)

    def test_with_group_list(self):
        request = testing.DummyRequest()
        request.ldap_connector = DummyLDAPConnector(
            'testdn', [('a', 'b')])
        result = self._callFUT('testdn', request)
        self.assertEqual(result, [('a', 'b')])


class Test_groupfinder(unittest.TestCase):

    def _callFUT(self, dn, request):
        from pyramid_ldap3 import groupfinder
        return groupfinder(dn, request)

    def test_no_group_list(self):
        request = testing.DummyRequest()
        request.ldap_connector = DummyLDAPConnector('testdn', None)
        result = self._callFUT('testdn', request)
        self.assertTrue(result is None)

    def test_with_group_list(self):
        request = testing.DummyRequest()
        request.ldap_connector = DummyLDAPConnector(
            'testdn', [('groupdn', None)])
        result = self._callFUT('testdn', request)
        self.assertEqual(result, ['groupdn'])


class Test_get_ldap_connector(unittest.TestCase):

    def _callFUT(self, request):
        from pyramid_ldap3 import get_ldap_connector
        return get_ldap_connector(request)

    def test_no_connector(self):
        request = testing.DummyRequest()
        self.assertRaises(ConfigurationError, self._callFUT, request)
        
    def test_with_connector(self):
        request = testing.DummyRequest()
        request.ldap_connector = True
        result = self._callFUT(request)
        self.assertEqual(result, True)


class Test_ldap_setup(unittest.TestCase):

    def _callFUT(self, config, uri, **kw):
        from pyramid_ldap3 import ldap_setup
        return ldap_setup(config, uri, **kw)

    def test_it_defaults(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._callFUT(config, 'ldap://')
        self.assertEqual(config.prop_name, 'ldap_connector')
        self.assertEqual(config.prop_reify, True)
        request = testing.DummyRequest()
        self.assertEqual(config.prop(request).__class__, Connector)


class Test_ldap_set_groups_query(unittest.TestCase):

    def _callFUT(self, config, base_dn, filter_tmpl, **kw):
        from pyramid_ldap3 import ldap_set_groups_query
        return ldap_set_groups_query(config, base_dn, filter_tmpl, **kw)

    def test_it_defaults(self):
        import ldap3
        config = DummyConfig()
        self._callFUT(config, 'dn', 'tmpl')
        self.assertEqual(config.registry.ldap_groups_query.base_dn, 'dn')
        self.assertEqual(config.registry.ldap_groups_query.filter_tmpl, 'tmpl')
        self.assertEqual(config.registry.ldap_groups_query.scope,
            ldap3.SEARCH_SCOPE_WHOLE_SUBTREE)
        self.assertEqual(config.registry.ldap_groups_query.cache_period, 0)


class Test_ldap_set_login_query(unittest.TestCase):

    def _callFUT(self, config, base_dn, filter_tmpl, **kw):
        from pyramid_ldap3 import ldap_set_login_query
        return ldap_set_login_query(config, base_dn, filter_tmpl, **kw)

    def test_it_defaults(self):
        from pyramid_ldap3 import ldap3
        config = DummyConfig()
        self._callFUT(config, 'dn', 'tmpl')
        self.assertEqual(config.registry.ldap_login_query.base_dn, 'dn')
        self.assertEqual(config.registry.ldap_login_query.filter_tmpl, 'tmpl')
        self.assertEqual(config.registry.ldap_login_query.scope,
            ldap3.SEARCH_SCOPE_SINGLE_LEVEL)
        self.assertEqual(config.registry.ldap_login_query.cache_period, 0)


class TestConnectionManager(unittest.TestCase):

    def _makeOne(self, uri, bind=None, passwd=None, tls=None,
            use_pool=True, pool_size=10):
        from pyramid_ldap3 import ConnectionManager
        ldap3 = DummyLdap3()
        return ConnectionManager(uri, bind=bind, passwd=passwd, tls=tls,
                use_pool=use_pool, pool_size=pool_size, ldap3=ldap3)

    def test_uri(self):
        manager = self._makeOne('testhost')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 389)
        manager = self._makeOne('ldap://testhost')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 389)
        manager = self._makeOne('ldap://testhost:432')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 432)
        manager = self._makeOne('ldaps://testhost')
        self.assertTrue(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 636)
        manager = self._makeOne('ldaps://testhost:987')
        self.assertTrue(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 987)

    def test_use_tls(self):
        manager = self._makeOne('testhost')
        self.assertFalse(manager.server.tls)
        from pyramid_ldap3 import ldap3
        tls = ldap3.Tls()
        manager = self._makeOne('testhost', tls=tls)
        self.assertTrue(manager.server.tls is tls)

    def test_bind(self):
        manager = self._makeOne('testhost', 'fred', 'flint')
        self.assertEqual(manager.bind, 'fred')
        self.assertEqual(manager.passwd, 'flint')

    def test_pool(self):
        manager = self._makeOne('testhost')
        self.assertEqual(manager.pool_size, 10)
        manager = self._makeOne('testhost', pool_size=42)
        self.assertEqual(manager.pool_size, 42)
        manager = self._makeOne('testhost', use_pool=False)
        self.assertTrue(manager.pool_size is None)

    def test_connection(self):
        manager = self._makeOne('testhost')
        conn = manager.connection()
        self.assertEqual(conn.server.host, 'testhost')
        self.assertTrue(conn.user is None)
        conn = manager.connection('fred', 'flint')
        self.assertEqual(conn.user, 'fred')
        self.assertEqual(conn.password, 'flint')


class TestConnector(unittest.TestCase):

    def _makeOne(self, registry, manager):
        from pyramid_ldap3 import Connector
        return Connector(registry, manager)

    def test_authenticate_no_ldap_login_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.authenticate, None, None)

    def test_authenticate_search_returns_no_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate(None, None) is None)

    def test_authenticate_empty_password(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate('foo', '') is None)

    def test_authenticate_search_returns_one_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate(None, None), ('a', 'b'))

    def test_authenticate_search_returns_multiple_results(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b'), ('a', 'c')])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate(None, None) is None)

    def test_authenticate_search_bind_raises(self):
        from pyramid_ldap3 import ldap3
        manager = DummyManager([None, ldap3.LDAPException])
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate(None, None) is None)

    def test_user_groups_no_ldap_groups_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.user_groups, None)

    def test_user_groups_search_returns_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.user_groups(None), [('a', 'b')])

    def test_user_groups_execute_raises(self):
        from pyramid_ldap3 import ldap3
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch(
            [('a', 'b')], ldap3.LDAPException)
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.user_groups(None) is None)

    def test_user_groups_search_escapes(self):
        manager = DummyManager()
        registry = Dummy()
        search = DummySearch([('a', 'b')])
        registry.ldap_groups_query = search
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.user_groups('abc123'), [('a', 'b')])
        self.assertEqual(search.kw['userdn'], 'abc123')
        self.assertEqual(inst.user_groups('(abc*123)'), [('a', 'b')])
        self.assertEqual(search.kw['userdn'], '\\28abc\\2A123\\29')
        self.assertEqual(inst.user_groups(b'ab\xc3\xa7123'), [('a', 'b')])
        self.assertEqual(search.kw['userdn'].encode('latin-1'), b'ab\xe7123')
        self.assertEqual(inst.user_groups(b'ab\xe7123'), [('a', 'b')])
        self.assertEqual(search.kw['userdn'], '\\61\\62\\e7\\31\\32\\33')


class Test_LDAPQuery(unittest.TestCase):

    def _makeOne(self, base_dn, filter_tmpl, scope, attributes, cache_period):
        from pyramid_ldap3 import _LDAPQuery
        return _LDAPQuery(
            base_dn, filter_tmpl, scope, attributes, cache_period)

    def test_query_cache_no_rollover(self):
        inst = self._makeOne(None, None, None, None, 1)
        inst.last_timeslice = 1 << 31
        inst.cache['foo'] = 'bar'
        self.assertEqual(inst.query_cache('foo'), 'bar')

    def test_query_cache_with_rollover(self):
        inst = self._makeOne(None, None, None, None, 1)
        inst.cache['foo'] = 'bar'
        self.assertTrue(inst.query_cache('foo') is None)
        self.assertEqual(inst.cache, {})
        self.assertNotEqual(inst.last_timeslice, 0)

    def test_execute_no_cache_period(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 0)
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, [('a', {'b': 'c'})])
        self.assertEqual(conn.args, ('DN=Org', '(cn=foo)'))
        self.assertEqual(conn.kwargs,
            {'attributes': 'attrs', 'search_scope': 'scope'})

    def test_execute_with_cache_period_miss(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 1)
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, [('a', {'b': 'c'})])
        self.assertEqual(conn.args, ('DN=Org', '(cn=foo)'))
        self.assertEqual(conn.kwargs, {
            'attributes': 'attrs', 'search_scope': 'scope'})

    def test_execute_with_cache_period_hit(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 1)
        inst.last_timeslice = 1 << 31
        inst.cache[('DN=Org', '(cn=foo)')] = ('d', {'e': 'f'})
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, ('d', {'e': 'f'}))
        self.assertTrue(conn.args is None)
        self.assertTrue(conn.kwargs is None)


class DummyLDAPConnector(object):

    def __init__(self, dn, group_list):
        self.dn = dn
        self.group_list = group_list

    def user_groups(self, dn):
        return self.group_list


class Dummy(object):
    def __init__(self, *arg, **kw):
        pass


class DummyConfig(object):

    introspectable = Dummy

    def __init__(self):
        self.registry = Dummy()
        self.directives = []

    def add_directive(self, name, fn):
        self.directives.append(name)
        
    def set_request_property(self, prop, name, reify=False):
        self.prop_reify = reify
        self.prop_name = name
        self.prop = prop

    def action(self, discriminator, callable, introspectables=()):
        if callable:
            callable()


class DummyManager(object):

    def __init__(self, with_errors=None):
        self.with_errors = with_errors or []
        self.status = self.user = self.password = None

    def connection(self, user=None, password=None):
        self.user = user
        self.password = password
        if self.with_errors:
            e = self.with_errors.pop(0)
            if e is not None:
                raise e
        self.bind()
        return self

    def bind(self):
        self.status = 'bound'
        return

    def unbind(self):
        self.status = 'unbound'


class DummySearch(object):

    def __init__(self, result, exc=None):
        self.result = result
        self.exc = exc
        self.conn = None
        self.kw = None

    def execute(self, conn, **kw):
        if self.exc is not None:
            raise self.exc
        self.conn = None
        self.kw = kw
        return self.result


class DummyConnection(object):

    def __init__(self, result):
        self.result = result
        self.result_id = 0
        self.args = None
        self.kwargs = None

    def search(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.result_id += 1
        return self.result_id

    def get_response(self, result_id):
        return self.result, result_id


class DummyLdap3Server(object):

    def __init__(self, host, port=None, use_ssl=False, tls=None):
        self.host = host
        self.port = port
        self.ssl = use_ssl
        self.tls = tls


class DummyLdap3Connection(object):

    def __init__(self, server, user=None, password=None,
            auto_bind=False, lazy=False, read_only=False,
            client_strategy=None, pool_name='oyramid_ldap3', pool_size=10):
        self.server = server
        self.user = user
        self.password = password
        self.pool_size = pool_size


class DummyLdap3(object):

    STRATEGY_ASYNC_THREADED = 1
    STRATEGY_REUSABLE_THREADED = 2

    Server = DummyLdap3Server
    Connection = DummyLdap3Connection
