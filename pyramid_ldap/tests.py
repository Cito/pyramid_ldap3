import contextlib
import unittest
import sys

from pyramid.compat import (
    text_type,
    text_,
    )
from pyramid import testing
from pyramid.exceptions import ConfigurationError

class Test_includeme(unittest.TestCase):
    def _callFUT(self, config):
        from pyramid_ldap import includeme
        includeme(config)

    def test_it(self):
        config = DummyConfig()
        self._callFUT(config)
        self.assertEqual(config.directives,
                         ['ldap_setup', 'ldap_set_login_query',
                          'ldap_set_groups_query'])
        

class Test__ldap_decode(unittest.TestCase):
    def _callFUT(self, val):
        from pyramid_ldap import _ldap_decode
        return _ldap_decode(val)

    def test_decode_str(self):
        result = self._callFUT('abc')
        self.assertEqual(type(result), text_type)
        self.assertEqual(result, text_('abc'))

    def test_decode_list(self):
        result = self._callFUT(['abc', 'def'])
        self.assertEqual(type(result), list)
        self.assertEqual(result[0], text_('abc'))
        self.assertEqual(result[1], text_('def'))

    def test_decode_tuple(self):
        result = self._callFUT(('abc', 'def'))
        self.assertEqual(type(result), tuple)
        self.assertEqual(result[0], text_('abc'))
        self.assertEqual(result[1], text_('def'))

    def test_decode_dict(self):
        import ldap
        result = self._callFUT({'abc':'def'})
        self.assertTrue(isinstance(result, ldap.cidict.cidict))
        self.assertEqual(result[text_('abc')], text_('def'))

    def test_decode_nested(self):
        import ldap
        result = self._callFUT({'abc':['def', 'jkl']})
        self.assertTrue(isinstance(result, ldap.cidict.cidict))
        self.assertEqual(result[text_('abc')], [text_('def'), text_('jkl')])

    def test_undecodeable(self):
        uid = b'\xdd\xafw:PuUO\x8a#\x17\xaa\xc2\xc7\x8e\xf6'
        result = self._callFUT(uid)
        self.assertTrue(isinstance(result, bytes))

class Test_groupfinder(unittest.TestCase):
    def _callFUT(self, dn, request):
        from pyramid_ldap import groupfinder
        return groupfinder(dn, request)

    def test_no_group_list(self):
        request = testing.DummyRequest()
        request.ldap_connector = DummyLDAPConnector('dn', None)
        result = self._callFUT('dn', request)
        self.assertEqual(result, None)

    def test_with_group_list(self):
        request = testing.DummyRequest()
        request.ldap_connector = DummyLDAPConnector('dn', [('groupdn', None)])
        result = self._callFUT('dn', request)
        self.assertEqual(result, ['groupdn'])

class Test_get_ldap_connector(unittest.TestCase):
    def _callFUT(self, request):
        from pyramid_ldap import get_ldap_connector
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
        from pyramid_ldap import ldap_setup
        return ldap_setup(config, uri, **kw)

    def test_it_defaults(self):
        from pyramid_ldap import Connector
        config = DummyConfig()
        self._callFUT(config, 'ldap://')
        self.assertEqual(config.prop_name, 'ldap_connector')
        self.assertEqual(config.prop_reify, True)
        request = testing.DummyRequest()
        self.assertEqual(config.prop(request).__class__, Connector)

class Test_ldap_set_groups_query(unittest.TestCase):
    def _callFUT(self, config, base_dn, filter_tmpl, **kw):
        from pyramid_ldap import ldap_set_groups_query
        return ldap_set_groups_query(config, base_dn, filter_tmpl, **kw)

    def test_it_defaults(self):
        import ldap
        config = DummyConfig()
        self._callFUT(config, 'dn', 'tmpl')
        self.assertEqual(config.registry.ldap_groups_query.base_dn, 'dn')
        self.assertEqual(config.registry.ldap_groups_query.filter_tmpl, 'tmpl')
        self.assertEqual(config.registry.ldap_groups_query.scope,
                         ldap.SCOPE_SUBTREE)
        self.assertEqual(config.registry.ldap_groups_query.cache_period, 0)

class Test_ldap_set_login_query(unittest.TestCase):
    def _callFUT(self, config, base_dn, filter_tmpl, **kw):
        from pyramid_ldap import ldap_set_login_query
        return ldap_set_login_query(config, base_dn, filter_tmpl, **kw)

    def test_it_defaults(self):
        import ldap
        config = DummyConfig()
        self._callFUT(config, 'dn', 'tmpl')
        self.assertEqual(config.registry.ldap_login_query.base_dn, 'dn')
        self.assertEqual(config.registry.ldap_login_query.filter_tmpl, 'tmpl')
        self.assertEqual(config.registry.ldap_login_query.scope,
                         ldap.SCOPE_ONELEVEL)
        self.assertEqual(config.registry.ldap_login_query.cache_period, 0)

class TestConnector(unittest.TestCase):
    def _makeOne(self, registry, manager):
        from pyramid_ldap import Connector
        return Connector(registry, manager)

    def test_authenticate_no_ldap_login_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.authenticate, None, None)

    def test_authenticate_search_returns_non_one_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate(None, None), None)

    def test_authenticate_empty_password(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate('foo', ''), None)

    def test_authenticate_search_returns_one_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate(None, None), ('a', 'b'))

    def test_authenticate_search_bind_raises(self):
        import ldap
        manager = DummyManager([None, ldap.LDAPError])
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate(None, None), None)

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
        import ldap
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch([('a', 'b')], ldap.LDAPError)
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.user_groups(None), None)

class Test_LDAPQuery(unittest.TestCase):
    def _makeOne(self, base_dn, filter_tmpl, scope, cache_period):
        from pyramid_ldap import _LDAPQuery
        return _LDAPQuery(base_dn, filter_tmpl, scope, cache_period)

    def test_query_cache_no_rollover(self):
        inst = self._makeOne(None, None, None, 1)
        inst.last_timeslice = sys.maxint
        inst.cache['foo'] = 'bar'
        self.assertEqual(inst.query_cache('foo'), 'bar')

    def test_query_cache_with_rollover(self):
        inst = self._makeOne(None, None, None, 1)
        inst.cache['foo'] = 'bar'
        self.assertEqual(inst.query_cache('foo'), None)
        self.assertEqual(inst.cache, {})
        self.assertNotEqual(inst.last_timeslice, 0)

    def test_execute_no_cache_period(self):
        inst = self._makeOne('%(login)s', '%(login)s', None, 0)
        conn = DummyConnection('abc')
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, 'abc')
        self.assertEqual(conn.arg, ('foo', None, 'foo'))

    def test_execute_with_cache_period_miss(self):
        inst = self._makeOne('%(login)s', '%(login)s', None, 1)
        conn = DummyConnection('abc')
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, 'abc')
        self.assertEqual(conn.arg, ('foo', None, 'foo'))

    def test_execute_with_cache_period_hit(self):
        inst = self._makeOne('%(login)s', '%(login)s', None, 1)
        inst.last_timeslice = sys.maxint
        inst.cache[('foo', None, 'foo')] = 'def'
        conn = DummyConnection('abc')
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, 'def')
        
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
    def __init__(self, with_errors=()):
        self.with_errors = with_errors
    @contextlib.contextmanager
    def connection(self, username=None, password=None):
        yield self
        if self.with_errors:
            e = self.with_errors.pop(0)
            if e is not None:
                raise e
        
class DummySearch(object):
    def __init__(self, result, exc=None):
        self.result = result
        self.exc = exc

    def execute(self, conn, **kw):
        if self.exc is not None:
            raise self.exc
        self.kw = kw
        return self.result
    
class DummyConnection(object):
    def __init__(self, result):
        self.result = result

    def search_s(self, *arg):
        self.arg = arg
        return self.result
    
