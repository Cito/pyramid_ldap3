
from pyramid.view import view_config, forbidden_view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget

from pyramid_ldap3 import get_ldap_connector


@view_config(route_name='sampleapp.root', permission='view')
def logged_in(request):
    return Response('OK')


@view_config(route_name='sampleapp.logout')
def logout(request):
    headers = forget(request)
    return Response('Logged out', headers=headers)


@view_config(route_name='sampleapp.login', renderer='templates/login.pt')
@forbidden_view_config(renderer='templates/login.pt')
def login(request):
    url = request.current_route_url()
    login = ''
    password = ''
    error = ''

    if 'form.submitted' in request.POST:
        login = request.POST['login']
        password = request.POST['password']
        connector = get_ldap_connector(request)
        data = connector.authenticate(login, password)
        if data is not None:
            dn = data[0]
            headers = remember(request, dn)
            return HTTPFound('/', headers=headers)
        error = 'Invalid credentials'

    return dict(
        login_url=url,
        login=login,
        password=password,
        error=error)
