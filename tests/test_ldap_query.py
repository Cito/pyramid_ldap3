from . import TestCase, DummyConnection


class TestLDAPQuery(TestCase):

    def _makeOne(self, base_dn, filter_tmpl, scope, attributes, cache_period):
        from pyramid_ldap3 import _LDAPQuery
        return _LDAPQuery(
            base_dn, filter_tmpl, scope, attributes, cache_period)

    def test_execute_no_result(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'none', 'attrs', 0)
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, [])

    def test_query_cache_no_rollover(self):
        inst = self._makeOne(None, None, None, None, 1)
        inst.last_timeslice = 1 << 31
        inst.cache['foo'] = 'bar'
        self.assertEqual(inst.query_cache('foo'), 'bar')

    def test_query_cache_with_rollover(self):
        inst = self._makeOne(None, None, None, None, 1)
        inst.cache['foo'] = 'bar'
        self.assertTrue(inst.query_cache('foo') is None)
        self.assertEqual(inst.cache, {})
        self.assertNotEqual(inst.last_timeslice, 0)

    def test_execute_no_cache_period(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 0)
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(inst.cache, {})
        self.assertEqual(result, [('a', {'b': 'c'})])
        self.assertEqual(conn.args, ('DN=Org', '(cn=foo)'))
        self.assertEqual(
            conn.kwargs, {'attributes': 'attrs', 'search_scope': 'scope'})

    def test_execute_with_cache_period_miss(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 1)
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, [('a', {'b': 'c'})])
        self.assertEqual(conn.args, ('DN=Org', '(cn=foo)'))
        self.assertEqual(conn.kwargs, {
            'attributes': 'attrs', 'search_scope': 'scope'})

    def test_execute_with_cache_period_hit(self):
        inst = self._makeOne('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 1)
        inst.last_timeslice = 1 << 31
        inst.cache[('DN=Org', '(cn=foo)')] = ('d', {'e': 'f'})
        conn = DummyConnection([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(conn, login='foo')
        self.assertEqual(result, ('d', {'e': 'f'}))
        self.assertTrue(conn.args is None)
        self.assertTrue(conn.kwargs is None)
