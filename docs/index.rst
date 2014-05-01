pyramid_ldap
============

Overview
--------

:mod:`pyramid_ldap` provides LDAP authentication services to your Pyramid
application.  Thanks to the ever-awesome `SurveyMonkey
<http://surveymonkey.com>`_ for sponsoring the development of this package!

.. warning:: This package only works with Pyramid 1.3a9 and better.

Installation
------------

``pyramid_ldap`` depends on the `python-ldap <http://www.python-ldap.org/>`_
and `ldappool <https://github.com/mozilla-services/ldappool>`_ packages.
``python_ldap`` requires OpenLDAP development libraries to be installed
before it can successfully be installed.  An easy way to get these installed
on a Debian Linux system is to use ``apt-get build-dep python-ldap``.

After you've got the OpenLDAP dependencies installed, you can install
``pyramid_ldap`` using setuptools, e.g. (within a virtualenv)::

  $ easy_install pyramid_ldap

Setup
-----

Once :mod:`pyramid_ldap` is installed, you must use the ``config.include``
mechanism to include it into your Pyramid project's configuration.  In your
Pyramid project's ``__init__.py``:

.. code-block:: python

   config = Configurator(.....)
   config.include('pyramid_ldap')

Alternately, instead of using the Configurator's ``include`` method, you can
activate Pyramid by changing your application's ``.ini`` file, use the
following line:

.. code-block:: ini

   pyramid.includes = pyramid_ldap

Once you've included ``pyramid_ldap``, you have to call methods of the
Configurator to tell it about your LDAP server and query particulars.  Here's
an example of calling methods to create a fully-configured LDAP setup that
attempts to talk to an Active Directory server:

.. code-block:: python

    import ldap

    config = Configurator()

    config.include('pyramid_ldap')

    config.ldap_setup(
        'ldap://ldap.example.com',
        bind='CN=ldap user,CN=Users,DC=example,DC=com',
        passwd='ld@pu5er'
        )

    config.ldap_set_login_query(
        base_dn='CN=Users,DC=example,DC=com',
        filter_tmpl='(sAMAccountName=%(login)s)',
        scope = ldap.SCOPE_ONELEVEL,
        )

    config.ldap_set_groups_query(
        base_dn='CN=Users,DC=example,DC=com',
        filter_tmpl='(&(objectCategory=group)(member=%(userdn)s))',
        scope = ldap.SCOPE_SUBTREE,
        cache_period = 600,
        )

Configurator Methods
--------------------

Configuration of ``pyramid_ldap`` is done via the Configurator methods named
``ldap_setup``, ``ldap_set_login_query``, and ``ldap_set_groups_query``.  All
three of these methods should be called once (and, ideally, only once) during
the startup phase of your Pyramid application.

``Configurator.ldap_setup``

   This Configurator method accepts arguments used to set up an LDAP
   connection.  After you call it, you will be able to use the
   :func:`pyramid_ldap.get_ldap_connector` API from within your application.
   It will return a :class:`pyramid_ldap.Connector` instance.  See
   :func:`pyramid_ldap.ldap_setup` for argument details.

``Configurator.ldap_set_login_query``

   This configurator method accepts parameters which tell ``pyramid_ldap``
   how to find a user based on a login.  Invoking this method allows the LDAP
   connector's ``authenticate`` method to work.  See
   :func:`pyramid_ldap.ldap_set_login_query` for argument details.

   If ``ldap_set_login_query`` is not called, the
   :meth:`pyramid_ldap.Connector.authenticate` method will not work.

``Configurator.ldap_set_groups_query``

   This configurator method accepts parameters which tell ``pyramid_ldap``
   how to find groups based on a user DN.  Invoking this method allows the
   connector's ``user_groups`` method to work.  See
   :func:`pyramid_ldap.ldap_set_groups_query` for argument details.

   If ``ldap_set_groups_query`` is not called, the
   :meth:`pyramid_ldap.Connector.user_groups` method will not work.

Caching
-------

The :func:`pyramid_ldap.ldap_set_groups_query` and
:func:`pyramid_ldap.ldap_set_login_query` methods accept a ``cache_period``
argument.  It must be an integer.  If it is nonzero, the results of the
associated query will be kept in memory for a maximum of that many seconds,
after which they will be flushed.

Usage
-----

Assuming LDAP server and query setup has been done (as per above),
you can begin using ``pyramid_ldap`` in your application.

Here's a small application which uses the ``pyramid_ldap`` API:

.. code-block:: python

    import ldap

    from pyramid.authentication import AuthTktAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy

    from pyramid.view import (
        view_config,
        forbidden_view_config,
        )

    from pyramid.httpexceptions import HTTPFound

    from pyramid.security import (
       Allow,
       Authenticated,
       remember,
       forget,
       )

    from pyramid_ldap import (
        get_ldap_connector,
        groupfinder,
        )

    @view_config(route_name='login',
                 renderer='templates/login.pt')
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
            else:
                error = 'Invalid credentials'
                
        return dict(
            login_url=url,
            login=login,
            password=password,
            error=error,
            )

    @view_config(route_name='root', permission='view')
    def logged_in(request):
        return Response('OK')

    @view_config(route_name='logout')
    def logout(request):
        headers = forget(request)
        return Response('Logged out', headers=headers)

    class RootFactory(object):
        __acl__ = [(Allow, Authenticated, 'view')]
        def __init__(self, request):
            pass

    if __name__ == '__main__':
        config = Configurator(root_factory=RootFactory)

        config.include('pyramid_ldap')

        config.set_authentication_policy(
            AuthTktAuthenticationPolicy('seekr1t',
                                        callback=groupfinder)
            )
        config.set_authorization_policy(
            ACLAuthorizationPolicy()
            )

        config.ldap_setup(
            'ldap://ldap.example.com',
            bind='CN=ldap user,CN=Users,DC=example,DC=com',
            passwd='ld@pu5er'
            )

        config.ldap_set_login_query(
            base_dn='CN=Users,DC=example,DC=com',
            filter_tmpl='(sAMAccountName=%(login)s)',
            scope = ldap.SCOPE_ONELEVEL,
            )

        config.ldap_set_groups_query(
            base_dn='CN=Users,DC=example,DC=com',
            filter_tmpl='(&(objectCategory=group)(member=%(userdn)s))',
            scope = ldap.SCOPE_SUBTREE,
            cache_period = 600,
            )

        config.add_route('root', '/')
        config.add_route('login', '/login')
        config.add_route('logout', '/logout')
        config.scan('.')
        return config.make_wsgi_app()

This application sets up for an LDAP server on ``ldap.example.com`` using
:func:`pyramid_ldap.ldap_setup`.  It passes a ``bind`` DN and ``passwd`` for
a user capable of doing LDAP queries.

It sets up a login query using :func:`pyramid_ldap.ldap_set_login_query`
using a base DN of ``CN=Users,DC=example,DC=com`` and a filter_tmpl of
``(sAMAccountName=%(login)s)``.  The filter template's ``%(login)s`` value
will be replaced with the login name provided to the
:meth:`pyramid_ldap.Connector.authenticate` method.  In this case, we're
using Active Directory, and we'd like to use the sAMAccountName as the login
parameter (aka the "windows login name").

The application also sets up a groups query using
:func:`pyramid_ldap.ldap_set_groups_query` using a base DN of
``CN=Users,DC=example,DC=com`` and a filter_tmpl of
``(&(objectCategory=group)(member=%(userdn)s))``.  The group query's filter
template's ``%(userdn)s`` value will be replaced with the DN of the user provided
as the userid by the :meth:`pyramid_ldap.Connector.user_groups` method, in
order to look up all the groups to which the user belongs.  In this case,
we're using the ``member`` attribute to match against the DN, returning all
objects of the ``objectCategory=group`` type as group results.  Unlike the
login query, we cache the result of each search made via this query for up to
10 minutes (600 seconds) based on its ``cache_period`` argument.

The ``login`` view is invoked when someone visits ``/login`` or when the user
is prevented from invoking another view due to its permission settings.  It
displays a login form.  When the form is submitted, the view obtains the
login and password passed from the form as well as an LDAP connector instance
using the :func:`pyramid_ldap.get_ldap_connector` function.

The LDAP connector instance has an
:meth:`~pyramid_ldap.Connector.authenticate` method which accepts the login
and password.  It will return a data structure containing the user's DN as
well as the user attributes if the user exists and his password is correct.
It will return ``None`` if the user doesn't exist or if the user exists and
his password is incorrect. A zero length password is always considered invalid
since it is, according to the LDAP spec, a request for "unauthenticated
authentication." Unauthenticated authentication should not be used for LDAP
based authentication.

See `section 5.1.2 of RFC-4513 <http://tools.ietf.org/html/rfc4513#section-5.1.2>`_
for a description of this behavior.

When the user's name and password are correct, the ``login`` view uses the
``pyramid.security.remember`` API to set headers indicating that the user is
logged in.  The user's id will be his LDAP DN.

We make use of a canned ``groupfinder`` function to provide group lookup
support to the built-in AuthTktAuthenticationPolicy.  This groupfinder is
called for every request that requires authentication.  The groups that an
authenticated user belongs to will be the DNs of each of his LDAP groups when
you use this groupfinder.  The groupfinder uses the
:meth:`pyramid_ldap.Connector.user_groups` method and looks like this:

.. code-block:: python

    def groupfinder(dn, request):
        connector = get_ldap_connector(request)
        group_list = connector.user_groups(dn)
        if group_list is None:
            return None
        return [dn for dn, attrs in group_list]

The effect of this configuration is that a user is unable to view the
``root`` view at ``/`` until logging in with successful credentials, because
it's protected by the ``view`` permission, which is only granted to the
``Authenticated`` principal based on the root factory's ACL.

The ``logout`` view calls ``pyramid.security.forget`` to obtain headers
useful for dropping the credentials.

See the ``sampleapp`` sample application inside the ``pyramid_ldap``
distribution for a working example of the above application.  It can be
viewed at https://github.com/Pylons/pyramid_ldap/tree/master/sampleapp .

Logging
-------

``pyramid_ldap`` uses the logger named ``pyramid_ldap``.  It sends output at
a DEBUG level useful for its own developers to see what's happening.

More Information
----------------

.. toctree::
   :maxdepth: 1

   api.rst

Reporting Bugs / Development Versions
-------------------------------------

Visit http://github.com/Pylons/pyramid_ldap to download development or
tagged versions.

Visit http://github.com/Pylons/pyramid_ldap/issues to report bugs.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
