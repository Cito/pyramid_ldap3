import ldap3

from pyramid_ldap3 import groupfinder

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Allow, Authenticated


class RootFactory(object):

    __acl__ = [(Allow, Authenticated, 'view')]

    def __init__(self, request):
        pass


def main(global_config, **settings):
    config = Configurator(settings=settings, root_factory=RootFactory)
    config.include('pyramid_ldap3')
    config.include('pyramid_chameleon')
    config.set_authentication_policy(
        AuthTktAuthenticationPolicy('seekr1t', callback=groupfinder))
    config.set_authorization_policy(
        ACLAuthorizationPolicy())
    config.ldap_setup(
        'ldap://ldap.forumsys.com',
        bind='cn=read-only-admin,dc=example,dc=com',
        passwd='password')
    config.ldap_set_login_query(
        'dc=example,dc=com',
        # '(sAMAccountName=%(login)s)',
        '(uid=%(login)s)',
        scope=ldap3.SUBTREE,
        cache_period=0)
    config.ldap_set_groups_query(
        'dc=example,dc=com',
        # '(member:1.2.840.113556.1.4.1941:=%(userdn)s)',
        # '(&(objectCategory=group)(member=%(userdn)s))',
        '(&(objectClass=groupOfUniqueNames)(uniqueMember=%(userdn)s))',
        cache_period=60)
    config.add_route('sampleapp.root', '/')
    config.add_route('sampleapp.login', '/login')
    config.add_route('sampleapp.logout', '/logout')
    config.scan('.views')
    return config.make_wsgi_app()
