from . import TestCase, DummyConfig


class TestIncludeme(TestCase):

    def _callFUT(self, config):
        from pyramid_ldap3 import includeme
        includeme(config)

    def test_it(self):
        config = DummyConfig()
        self._callFUT(config)
        self.assertEqual(config.directives, [
            'ldap_setup', 'ldap_set_login_query', 'ldap_set_groups_query'])
