from . import (
    TestCase, ConfigurationError,
    Dummy, DummyRequest, DummyManager, DummySearch)


class TestGetLdapConnector(TestCase):

    def _callFUT_no_realm(self, request):
        from pyramid_ldap3 import get_ldap_connector
        return get_ldap_connector(request)

    def _callFUT_with_realm(self, request, realm):
        from pyramid_ldap3 import get_ldap_connector
        return get_ldap_connector(request, realm)

    def test_no_connector(self):
        request = DummyRequest()
        self.assertRaises(ConfigurationError, self._callFUT_no_realm, request)

    def test_with_connector(self):
        request = DummyRequest()
        request.ldap_connector = True
        result = self._callFUT_no_realm(request)
        self.assertEqual(result, True)

    def test_with_connector_and_realm(self):
        request = DummyRequest()
        request.ldap_connector_test_realm = True
        self.assertRaises(ConfigurationError, self._callFUT_no_realm, request)
        result = self._callFUT_with_realm(request, 'test_realm')
        self.assertEqual(result, True)


class TestConnectorNoRealm(TestCase):

    def _makeOne(self, registry, manager):
        from pyramid_ldap3 import Connector
        return Connector(registry, manager)

    def test_authenticate_no_ldap_login_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.authenticate, None, None)
        self.assertIsNone(manager.bound)

    def test_authenticate_search_returns_no_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([])
        inst = self._makeOne(registry, manager)
        self.assertIsNone(inst.authenticate(None, None))
        self.assertIsNone(manager.bound)

    def test_authenticate_empty_password(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertIsNone(inst.authenticate('foo', ''))
        self.assertIsNone(manager.bound)

    def test_authenticate_search_returns_one_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate(None, None), ('a', 'b'))
        self.assertIs(manager.bound, False)

    def test_authenticate_search_returns_multiple_results(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b'), ('a', 'c')])
        inst = self._makeOne(registry, manager)
        self.assertIsNone(inst.authenticate(None, None))
        self.assertIsNone(manager.bound)

    def test_authenticate_search_bind_raises(self):
        from pyramid_ldap3 import LDAPException
        manager = DummyManager(with_error=LDAPException)
        registry = Dummy()
        registry.ldap_login_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertIsNone(inst.authenticate(None, None))
        self.assertIsNone(manager.bound)

    def test_authenticate_search_escapes(self):
        manager = DummyManager()
        registry = Dummy()
        search = DummySearch([('a', 'b')])
        registry.ldap_login_query = search
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.authenticate('abc123', 'def456'), ('a', 'b'))
        self.assertEqual(search.kw['login'], 'abc123')
        self.assertEqual(search.kw['password'], 'def456')
        self.assertEqual(inst.authenticate('abc*', 'def*'), ('a', 'b'))
        self.assertEqual(search.kw['login'], 'abc\\2A')
        self.assertEqual(search.kw['password'], 'def\\2A')
        self.assertEqual(inst.authenticate(b'ab\xc3\xa7123', None), ('a', 'b'))
        self.assertEqual(search.kw['login'].encode('latin-1'), b'ab\xe7123')
        self.assertEqual(inst.authenticate(b'ab\xe7123', None), ('a', 'b'))
        self.assertEqual(search.kw['login'], '\\61\\62\\e7\\31\\32\\33')
        self.assertIs(manager.bound, False)

    def test_user_groups_no_ldap_groups_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager)
        self.assertRaises(ConfigurationError, inst.user_groups, None)
        self.assertIsNone(manager.bound)

    def test_user_groups_search_returns_result(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch([('a', 'b')])
        inst = self._makeOne(registry, manager)
        self.assertEqual(inst.user_groups(None), [('a', 'b')])
        self.assertIsNone(manager.bound)

    def test_user_groups_execute_raises(self):
        from pyramid_ldap3 import LDAPException
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query = DummySearch(
            [('a', 'b')], LDAPException)
        inst = self._makeOne(registry, manager)
        self.assertIsNone(inst.user_groups(None))
        self.assertIsNone(manager.bound)

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
        self.assertIsNone(manager.bound)


class TestConnectorWithRealm(TestCase):

    def _makeOne(self, registry, manager, realm):
        from pyramid_ldap3 import Connector
        return Connector(registry, manager, realm)

    def _makeOne_no_realm(self, registry, manager):
        from pyramid_ldap3 import Connector
        return Connector(registry, manager)

    def test_authenticate_no_ldap_login_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager, 'test_realm')
        self.assertRaises(ConfigurationError, inst.authenticate, None, None)
        self.assertIsNone(manager.bound)

    def test_authenticate_search_returns_correct_results(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_login_query_test_realm = DummySearch([('a', 'b')])
        registry.ldap_login_query_another_realm = DummySearch([('c', 'd')])
        inst = self._makeOne_no_realm(None, manager)
        self.assertRaises(ConfigurationError, inst.authenticate, None, None)
        self.assertIsNone(manager.bound)
        inst = self._makeOne(registry, manager, 'test_realm')
        self.assertEqual(inst.authenticate(None, None), ('a', 'b'))
        self.assertIs(manager.bound, False)
        inst = self._makeOne(registry, manager, 'another_realm')
        self.assertEqual(inst.authenticate(None, None), ('c', 'd'))
        self.assertIs(manager.bound, False)

    def test_user_groups_no_ldap_groups_query(self):
        manager = DummyManager()
        inst = self._makeOne(None, manager, 'test_realm')
        self.assertRaises(ConfigurationError, inst.user_groups, None)
        self.assertIsNone(manager.bound)

    def test_user_groups_search_returns_correct_results(self):
        manager = DummyManager()
        registry = Dummy()
        registry.ldap_groups_query_test_realm = DummySearch([('a', 'b')])
        registry.ldap_groups_query_another_realm = DummySearch([('c', 'd')])
        inst = self._makeOne_no_realm(None, manager)
        self.assertRaises(ConfigurationError, inst.user_groups, None)
        self.assertIsNone(manager.bound)
        inst = self._makeOne(registry, manager, 'test_realm')
        self.assertEqual(inst.user_groups(None), [('a', 'b')])
        self.assertIsNone(manager.bound)
        inst = self._makeOne(registry, manager, 'another_realm')
        self.assertEqual(inst.user_groups(None), [('c', 'd')])
        self.assertIsNone(manager.bound)
