from . import (
    TestCase, ConfigurationError,
    Dummy, DummyRequest, DummyManager, DummySearch)


class TestGetLdapConnector(TestCase):

    def _callFUT(self, request):
        from pyramid_ldap3 import get_ldap_connector
        return get_ldap_connector(request)

    def test_no_connector(self):
        request = DummyRequest()
        self.assertRaises(ConfigurationError, self._callFUT, request)
        
    def test_with_connector(self):
        request = DummyRequest()
        request.ldap_connector = True
        result = self._callFUT(request)
        self.assertEqual(result, True)


class TestConnector(TestCase):

    def _makeOne(self, registry, manager):
        from pyramid_ldap3 import Connector
        return Connector(registry, manager)

    def test_authenticate_no_ldap_login_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.authenticate, None, None)
        self.assertTrue(manager.status is None)

    def test_authenticate_search_returns_no_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate(None, None) is None)
        self.assertEqual(manager.status, 'unbound')

    def test_authenticate_empty_password(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate('foo', '') is None)
        self.assertTrue(manager.status is None)

    def test_authenticate_search_returns_one_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate(None, None), ('a', 'b'))
        self.assertEqual(manager.status, 'unbound')

    def test_authenticate_search_returns_multiple_results(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b'), ('a', 'c')])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate(None, None) is None)
        self.assertEqual(manager.status, 'unbound')

    def test_authenticate_search_bind_raises(self):
        from pyramid_ldap3 import ldap3
        manager = DummyManager([None, ldap3.LDAPException])
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.authenticate(None, None) is None)
        self.assertEqual(manager.status, 'unbound')

    def test_user_groups_no_ldap_groups_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.user_groups, None)
        self.assertTrue(manager.status is None)

    def test_user_groups_search_returns_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.user_groups(None), [('a', 'b')])
        self.assertEqual(manager.status, 'unbound')

    def test_user_groups_execute_raises(self):
        from pyramid_ldap3 import ldap3
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch(
            [('a', 'b')], ldap3.LDAPException)
        inst = self._makeOne(registry, manager)
        self.assertTrue(inst.user_groups(None) is None)
        self.assertEqual(manager.status, 'unbound')

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
        self.assertEqual(manager.status, 'unbound')
