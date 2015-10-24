from unittest import TestCase

from pyramid.testing import DummyRequest
from pyramid.exceptions import ConfigurationError


class DummyLDAPConnector(object):

    def __init__(self, group_list):
        self.group_list = group_list

    # noinspection PyUnusedLocal
    def user_groups(self, userdn):
        return self.group_list


class Dummy(object):

    def __init__(self, *arg, **kw):
        pass


class DummyConfig(object):

    introspectable = Dummy

    def __init__(self):
        self.registry = Dummy()
        self.directives = []
        self.prop_reify = self.prop_name = self.prop = None

    # noinspection PyUnusedLocal
    def add_directive(self, name, directive):
        self.directives.append(name)

    def set_request_property(self, prop, name, reify=False):
        self.prop_reify = reify
        self.prop_name = name
        self.prop = prop

    # noinspection PyUnusedLocal
    @staticmethod
    def action(discriminator, action_task, introspectables=()):
        if action_task:
            action_task()


class DummyManager(object):

    def __init__(self, with_errors=None):
        self.with_errors = with_errors or []
        self.user = self.password = None
        self.status = self.exit_info = None

    def connection(self, user=None, password=None):
        self.user = user
        self.password = password
        if self.with_errors:
            e = self.with_errors.pop(0)
            if e is not None:
                raise e
        self.bind()
        return self

    def __enter__(self):
        pass

    def __exit__(self, *exit_info):
        self.exit_info = exit_info
        self.unbind()

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
        self.conn = conn
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
        if self.kwargs['search_scope'] == 'none':
            return None, result_id
        return self.result, result_id


class DummyLdap3Server(object):

    def __init__(self, host, port=None, use_ssl=False, tls=None):
        self.host = host
        self.port = port
        self.ssl = use_ssl
        self.tls = tls


class DummyLdap3Connection(object):

    def __init__(
            self, server, user=None, password=None,
            auto_bind=False, authentication=None,
            read_only=False, client_strategy=None, lazy=False,
            pool_name='pyramid_ldap3', pool_size=10, pool_lifetime=None):
        self.server = server
        self.user = user
        self.password = password
        self.auto_bind = auto_bind
        self.authentication = authentication
        self.read_only = read_only
        self.client_strategy = client_strategy
        self.lazy = lazy
        self.pool_name = pool_name
        self.pool_size = pool_size
        self.pool_lifetime = pool_lifetime


class DummyLdap3(object):

    STRATEGY_ASYNC_THREADED = 1
    STRATEGY_REUSABLE_THREADED = 2

    Server = DummyLdap3Server
    Connection = DummyLdap3Connection
