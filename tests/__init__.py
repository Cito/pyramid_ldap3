from unittest import TestCase

from pyramid.testing import DummyRequest
from pyramid.exceptions import ConfigurationError

__all__ = [
    'ConfigurationError', 'Dummy', 'DummyConfig', 'DummyLdap3',
    'DummyLDAPConnector', 'DummyManager', 'DummyRequest', 'DummySearch',
    'TestCase']


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
        self.req_method = self.req_method_args = None

    # noinspection PyUnusedLocal
    def add_directive(self, name, directive):
        self.directives.append(name)

    def add_request_method(self, method, name, property=False, reify=False):
        self.req_method = method
        self.req_method_args = name, property, reify

    # noinspection PyUnusedLocal
    @staticmethod
    def action(discriminator, action_task, introspectables=()):
        if action_task:
            action_task()


class DummyManager(object):

    def __init__(self, with_error=None, with_result=None):
        self.with_error = with_error
        self.with_result = with_result
        self.user = self.password = None
        self.bound = None
        self.result_id = 0
        self.search_args = self.search_kwargs = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.unbind()

    def connection(self, user=None, password=None):
        self.user = user
        self.password = password
        if self.with_error:
            raise self.with_error
        self.bind()
        return self

    def bind(self):
        self.bound = True
        return False

    def unbind(self):
        self.bound = False

    def search(self, *args, **kwargs):
        if not self.bound:
            raise AssertionError('connection not yet bound')
        self.search_args = args
        self.search_kwargs = kwargs
        self.result_id += 1
        return self.result_id

    def get_response(self, result_id):
        if self.search_kwargs['search_scope'] == 'none':
            return None, result_id
        return self.with_result, result_id


class DummySearch(object):

    def __init__(self, result, exc=None):
        self.result = result
        self.exc = exc
        self.manager = None
        self.kw = None

    def execute(self, manager, **kw):
        if self.exc is not None:
            raise self.exc
        self.manager = manager
        self.kw = kw
        return self.result


class DummyLdap3Server(object):

    def __init__(
            self, host, port=None, use_ssl=False, tls=None, get_info=None):
        self.host = host
        self.port = port
        self.ssl = use_ssl
        self.tls = tls
        self.get_info = get_info


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

    ASYNC = 1
    REUSABLE = 2

    NONE = 'NO_INFO'
    SCHEMA = 'SCHEMA'
    ALL = 'ALL'

    Server = DummyLdap3Server
    Connection = DummyLdap3Connection
