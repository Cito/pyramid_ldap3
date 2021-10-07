from . import TestCase, DummyManager


class TestLDAPQuery(TestCase):

    def _make_one(self, base_dn, filter_tmpl, scope, attributes, cache_period):
        from pyramid_ldap3 import _LDAPQuery
        return _LDAPQuery(
            base_dn, filter_tmpl, scope, attributes, cache_period)

    def _manager(self, with_result):
        return DummyManager(with_result=with_result)

    def test_execute_no_result(self):
        inst = self._make_one('DN=Org', '(cn=%(login)s)', 'none', 'attrs', 0)
        manager = self._manager([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(manager, login='foo')
        self.assertEqual(result, [])

    def test_query_cache_no_rollover(self):
        inst = self._make_one(None, None, None, None, 1)
        inst.last_timeslice = 1 << 31
        inst.cache['foo'] = 'bar'
        self.assertEqual(inst.query_cache('foo'), 'bar')

    def test_query_cache_with_rollover(self):
        inst = self._make_one(None, None, None, None, 1)
        inst.cache['foo'] = 'bar'
        self.assertIsNone(inst.query_cache('foo'))
        self.assertEqual(inst.cache, {})
        self.assertNotEqual(inst.last_timeslice, 0)

    def test_execute_no_cache_period(self):
        inst = self._make_one('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 0)
        manager = self._manager([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(manager, login='foo')
        self.assertEqual(inst.cache, {})
        self.assertEqual(result, [('a', {'b': 'c'})])
        self.assertEqual(manager.search_args, ('DN=Org', '(cn=foo)'))
        self.assertEqual(manager.search_kwargs, {
            'attributes': 'attrs', 'search_scope': 'scope'})

    def test_execute_with_cache_period_miss(self):
        inst = self._make_one('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 1)
        manager = self._manager([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(manager, login='foo')
        self.assertEqual(result, [('a', {'b': 'c'})])
        self.assertEqual(manager.search_args, ('DN=Org', '(cn=foo)'))
        self.assertEqual(manager.search_kwargs, {
            'attributes': 'attrs', 'search_scope': 'scope'})

    def test_execute_with_cache_period_hit(self):
        inst = self._make_one('DN=Org', '(cn=%(login)s)', 'scope', 'attrs', 1)
        inst.last_timeslice = 1 << 31
        inst.cache[('DN=Org', '(cn=foo)')] = ('d', {'e': 'f'})
        manager = self._manager([{'dn': 'a', 'attributes': {'b': 'c'}}])
        result = inst.execute(manager, login='foo')
        self.assertEqual(result, ('d', {'e': 'f'}))
        self.assertIsNone(manager.search_args)
        self.assertIsNone(manager.search_kwargs)
