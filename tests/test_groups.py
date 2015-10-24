from . import TestCase, DummyRequest, DummyLDAPConnector


class TestGetGroups(TestCase):

    def _callFUT(self, dn, request):
        from pyramid_ldap3 import get_groups
        return get_groups(dn, request)

    def test_no_group_list(self):
        request = DummyRequest()
        request.ldap_connector = DummyLDAPConnector(None)
        result = self._callFUT('testdn', request)
        self.assertTrue(result is None)

    def test_with_group_list(self):
        request = DummyRequest()
        request.ldap_connector = DummyLDAPConnector([('a', 'b')])
        result = self._callFUT('testdn', request)
        self.assertEqual(result, [('a', 'b')])


class TestGroupfinder(TestCase):

    def _callFUT(self, dn, request):
        from pyramid_ldap3 import groupfinder
        return groupfinder(dn, request)

    def test_no_group_list(self):
        request = DummyRequest()
        request.ldap_connector = DummyLDAPConnector(None)
        result = self._callFUT('testdn', request)
        self.assertTrue(result is None)

    def test_with_group_list(self):
        request = DummyRequest()
        request.ldap_connector = DummyLDAPConnector([('groupdn', None)])
        result = self._callFUT('testdn', request)
        self.assertEqual(result, ['groupdn'])
