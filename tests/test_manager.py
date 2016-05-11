from . import TestCase, DummyLdap3


class TestConnectionManager(TestCase):

    def _makeOne(
            self, uri,
            bind=None, passwd=None, tls=None, use_pool=True,
            pool_size=10, pool_lifetime=3600):
        from pyramid_ldap3 import ConnectionManager
        ldap3 = DummyLdap3()
        return ConnectionManager(
            uri, bind=bind, passwd=passwd, tls=tls,
            use_pool=use_pool, pool_size=pool_size,
            pool_lifetime=pool_lifetime, ldap3=ldap3)

    def test_uri(self):
        manager = self._makeOne('testhost')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 389)
        manager = self._makeOne('ldap://testhost')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 389)
        manager = self._makeOne('ldap://testhost:432')
        self.assertFalse(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 432)
        manager = self._makeOne('ldaps://testhost')
        self.assertTrue(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 636)
        manager = self._makeOne('ldaps://testhost:987')
        self.assertTrue(manager.server.ssl)
        self.assertEqual(manager.server.host, 'testhost')
        self.assertEqual(manager.server.port, 987)

    def test_use_tls(self):
        manager = self._makeOne('testhost')
        self.assertFalse(manager.server.tls)
        from pyramid_ldap3 import ldap3
        tls = ldap3.Tls()
        manager = self._makeOne('testhost', tls=tls)
        self.assertTrue(manager.server.tls is tls)

    def test_bind(self):
        manager = self._makeOne('testhost', 'fred', 'flint')
        self.assertEqual(manager.bind, 'fred')
        self.assertEqual(manager.passwd, 'flint')

    def test_pool(self):
        manager = self._makeOne('testhost')
        self.assertEqual(manager.pool_size, 10)
        manager = self._makeOne('testhost', pool_size=42)
        self.assertEqual(manager.pool_size, 42)
        manager = self._makeOne('testhost', pool_lifetime=4200)
        self.assertEqual(manager.pool_lifetime, 4200)
        manager = self._makeOne('testhost', use_pool=False)
        self.assertTrue(manager.pool_size is None)

    def test_connection(self):
        manager = self._makeOne('testhost')
        conn = manager.connection()
        self.assertEqual(conn.server.host, 'testhost')
        self.assertTrue(conn.user is None)
        conn = manager.connection('fred', 'flint')
        self.assertEqual(conn.user, 'fred')
        self.assertEqual(conn.password, 'flint')
