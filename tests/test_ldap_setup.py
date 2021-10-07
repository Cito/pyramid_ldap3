from . import TestCase, DummyConfig, DummyRequest


class TestLdapSetup(TestCase):

    def _call_fut(self, config, uri, **kw):
        from pyramid_ldap3 import ldap_setup
        return ldap_setup(config, uri, **kw)

    def test_it_defaults_ldap_host(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._call_fut(config, 'ldap://dummyhost')
        self.assertEqual(config.req_method_args,
                         ('ldap_connector', True, True))
        request = DummyRequest()
        connector = config.req_method(request)
        self.assertEqual(connector.__class__, Connector)
        server = connector.manager.server
        import ldap3
        self.assertIsInstance(server, ldap3.Server)
        self.assertEqual(server.host, 'dummyhost')
        self.assertEqual(server.port, 389)
        self.assertFalse(server.tls)
        self.assertEqual(server.get_info, ldap3.NONE)

    def test_it_defaults_ldaps_host(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._call_fut(config, 'ldaps://dummyhost')
        self.assertEqual(config.req_method_args,
                         ('ldap_connector', True, True))
        request = DummyRequest()
        connector = config.req_method(request)
        self.assertEqual(connector.__class__, Connector)
        server = connector.manager.server
        import ldap3
        self.assertIsInstance(server, ldap3.Server)
        self.assertEqual(server.host, 'dummyhost')
        self.assertEqual(server.port, 636)
        self.assertTrue(server.tls)
        self.assertEqual(server.get_info, ldap3.NONE)

    def test_it_defaults_ldap_hosts(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._call_fut(config, (
            'ldap://plainhost', 'ldaps://sslhost', 'ldap://custom:8389'))
        self.assertEqual(config.req_method_args,
                         ('ldap_connector', True, True))
        request = DummyRequest()
        connector = config.req_method(request)
        self.assertEqual(connector.__class__, Connector)
        server_pool = connector.manager.server
        import ldap3
        self.assertIsInstance(server_pool, ldap3.ServerPool)
        self.assertEqual(len(server_pool), 3)
        server = server_pool[0]
        self.assertEqual(server.host, 'plainhost')
        self.assertEqual(server.port, 389)
        self.assertFalse(server.tls)
        self.assertEqual(server.get_info, ldap3.NONE)
        server = server_pool[1]
        self.assertEqual(server.host, 'sslhost')
        self.assertEqual(server.port, 636)
        self.assertTrue(server.tls)
        self.assertEqual(server.get_info, ldap3.NONE)
        server = server_pool[2]
        self.assertEqual(server.host, 'custom')
        self.assertEqual(server.port, 8389)
        self.assertFalse(server.tls)
        self.assertEqual(server.get_info, ldap3.NONE)

    def test_it_defaults_realm(self):
        from pyramid_ldap3 import Connector
        config = DummyConfig()
        self._call_fut(config, 'ldap://dummyhost', realm='test')
        self.assertEqual(config.req_method_args,
                         ('ldap_connector_test', True, True))
        request = DummyRequest()
        connector = config.req_method(request)
        self.assertEqual(connector.__class__, Connector)
        server = connector.manager.server
        import ldap3
        self.assertIsInstance(server, ldap3.Server)
        self.assertEqual(server.host, 'dummyhost')
        self.assertEqual(server.port, 389)
        self.assertFalse(server.tls)
        self.assertEqual(server.get_info, ldap3.NONE)
