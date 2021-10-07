from . import TestCase, DummyLdap3


class TestConnectionManager(TestCase):

    def _make_one(
            self, uri,
            bind=None, passwd=None, tls=None,
            use_pool=True, pool_size=10, pool_lifetime=3600,
            get_info=None, realm=None):
        from pyramid_ldap3 import ConnectionManager
        ldap3 = DummyLdap3()
        return ConnectionManager(
            uri, bind=bind, passwd=passwd, tls=tls,
            use_pool=use_pool, pool_size=pool_size,
            pool_lifetime=pool_lifetime,
            get_info=get_info, ldap3=ldap3, realm=realm)

    def test_uri(self):
        manager = self._make_one('testhost')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 389)
        manager = self._make_one('ldap://testhost')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 389)
        manager = self._make_one('ldap://testhost:432')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 432)
        manager = self._make_one('ldaps://testhost')
        self.assertTrue(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 636)
        manager = self._make_one('ldaps://testhost:987')
        self.assertTrue(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 987)

    def test_use_tls(self):
        manager = self._make_one('testhost')
        self.assertFalse(manager.server.tls)
        from pyramid_ldap3 import ldap3
        tls = ldap3.Tls()
        manager = self._make_one('testhost', tls=tls)
        self.assertIs(manager.server.tls, tls)

    def test_get_info(self):
        manager = self._make_one('testhost')
        from pyramid_ldap3 import ldap3
        self.assertEqual(manager.server.get_info, ldap3.NONE)
        manager = self._make_one('testhost', get_info=ldap3.ALL)
        self.assertEqual(manager.server.get_info, ldap3.ALL)

    def test_bind(self):
        manager = self._make_one('testhost', 'fred', 'flint')
        self.assertEqual(manager.bind, 'fred')
        self.assertEqual(manager.passwd, 'flint')

    def test_pool(self):
        manager = self._make_one('testhost')
        self.assertEqual(manager.pool_size, 10)
        manager = self._make_one('testhost', pool_size=42)
        self.assertEqual(manager.pool_size, 42)
        manager = self._make_one('testhost', pool_lifetime=4200)
        self.assertEqual(manager.pool_lifetime, 4200)
        manager = self._make_one('testhost', use_pool=False)
        self.assertIsNone(manager.pool_size)

    def test_connection(self):
        manager = self._make_one('testhost')
        conn = manager.connection()
        self.assertEqual(conn.server.host, 'testhost')
        self.assertIsNone(conn.user)
        conn = manager.connection('fred', 'flint')
        self.assertEqual(conn.user, 'fred')
        self.assertEqual(conn.password, 'flint')

    def test_connection_with_realm(self):
        manager = self._make_one('testhost', realm='test_realm')
        conn = manager.connection()
        self.assertEqual(conn.server.host, 'testhost')
        self.assertIsNone(conn.user)
        conn = manager.connection('fred', 'flint')
        self.assertEqual(conn.user, 'fred')
        self.assertEqual(conn.password, 'flint')
