from . import TestCase, DummyConfig, DummyRequest


class TestLdapSetup(TestCase):

    def _callFUT(self, config, uri, **kw):
        from pyramid_ldap3 import ldap_setup
        return ldap_setup(config, uri, **kw)

    def test_it_defaults_ldap_host(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._callFUT(config, 'ldap://dummyhost')
        self.assertEqual(config.prop_name, 'ldap_connector')
        self.assertEqual(config.prop_reify, True)
        request = DummyRequest()
        connector = config.prop(request)
        self.assertEqual(connector.__class__, Connector)
        server = connector.manager.server
        import ldap3
        self.assertTrue(isinstance(server, ldap3.Server))
        self.assertEqual(server.host, 'dummyhost')
        self.assertEqual(server.port, 389)
        self.assertFalse(server.tls)

    def test_it_defaults_ldaps_host(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._callFUT(config, 'ldaps://dummyhost')
        self.assertEqual(config.prop_name, 'ldap_connector')
        self.assertEqual(config.prop_reify, True)
        request = DummyRequest()
        connector = config.prop(request)
        self.assertEqual(connector.__class__, Connector)
        server = connector.manager.server
        import ldap3
        self.assertTrue(isinstance(server, ldap3.Server))
        self.assertEqual(server.host, 'dummyhost')
        self.assertEqual(server.port, 636)
        self.assertTrue(server.tls)

    def test_it_defaults_ldap_hosts(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._callFUT(config, (
            'ldap://plainhost', 'ldaps://sslhost', 'ldap://custom:8389'))
        self.assertEqual(config.prop_name, 'ldap_connector')
        self.assertEqual(config.prop_reify, True)
        request = DummyRequest()
        connector = config.prop(request)
        self.assertEqual(connector.__class__, Connector)
        server_pool = connector.manager.server
        import ldap3
        self.assertTrue(isinstance(server_pool, ldap3.ServerPool))
        self.assertEqual(len(server_pool), 3)
        server = server_pool[0]
        self.assertEqual(server.host, 'plainhost')
        self.assertEqual(server.port, 389)
        self.assertFalse(server.tls)
        server = server_pool[1]
        self.assertEqual(server.host, 'sslhost')
        self.assertEqual(server.port, 636)
        self.assertTrue(server.tls)
        server = server_pool[2]
        self.assertEqual(server.host, 'custom')
        self.assertEqual(server.port, 8389)
        self.assertFalse(server.tls)
