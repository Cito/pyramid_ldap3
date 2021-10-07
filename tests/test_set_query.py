from . import TestCase, DummyConfig


class TestLdapSetGroupsQuery(TestCase):

    def _call_fut(self, config, base_dn, filter_tmpl, **kw):
        from pyramid_ldap3 import ldap_set_groups_query
        return ldap_set_groups_query(config, base_dn, filter_tmpl, **kw)

    def test_it_defaults(self):
        import ldap3
        config = DummyConfig()
        self._call_fut(config, 'dn', 'tmpl')
        ldap_groups_query = getattr(config.registry, 'ldap_groups_query', None)
        self.assertIsNotNone(ldap_groups_query)
        self.assertEqual(ldap_groups_query.base_dn, 'dn')
        self.assertEqual(ldap_groups_query.filter_tmpl, 'tmpl')
        self.assertEqual(ldap_groups_query.scope, ldap3.SUBTREE)
        self.assertEqual(ldap_groups_query.cache_period, 0)

    def test_it_realm(self):
        import ldap3
        config = DummyConfig()
        self._call_fut(config, 'dn_test', 'tmpl_test', realm='test')
        ldap_groups_query = getattr(
            config.registry, 'ldap_groups_query_test', None)
        self.assertIsNotNone(ldap_groups_query)
        self.assertEqual(ldap_groups_query.base_dn, 'dn_test')
        self.assertEqual(ldap_groups_query.filter_tmpl, 'tmpl_test')
        self.assertEqual(ldap_groups_query.scope, ldap3.SUBTREE)
        self.assertEqual(ldap_groups_query.cache_period, 0)


class TestLdapSetLoginQuery(TestCase):

    def _call_fut(self, config, base_dn, filter_tmpl, **kw):
        from pyramid_ldap3 import ldap_set_login_query
        return ldap_set_login_query(config, base_dn, filter_tmpl, **kw)

    def test_it_defaults(self):
        from pyramid_ldap3 import ldap3
        config = DummyConfig()
        self._call_fut(config, 'dn', 'tmpl')
        ldap_login_query = getattr(config.registry, 'ldap_login_query', None)
        self.assertIsNotNone(ldap_login_query)
        self.assertEqual(ldap_login_query.base_dn, 'dn')
        self.assertEqual(ldap_login_query.filter_tmpl, 'tmpl')
        self.assertEqual(ldap_login_query.scope, ldap3.LEVEL)
        self.assertEqual(ldap_login_query.cache_period, 0)

    def test_it_realm(self):
        from pyramid_ldap3 import ldap3
        config = DummyConfig()
        self._call_fut(config, 'dn_test', 'tmpl_test', realm='test')
        ldap_login_query = getattr(
            config.registry, 'ldap_login_query_test', None)
        self.assertIsNotNone(ldap_login_query)
        self.assertEqual(ldap_login_query.base_dn, 'dn_test')
        self.assertEqual(ldap_login_query.filter_tmpl, 'tmpl_test')
        self.assertEqual(ldap_login_query.scope, ldap3.LEVEL)
        self.assertEqual(ldap_login_query.cache_period, 0)
