.. _pyramid_ldap_api:

:mod:`pyramid_ldap3` API
------------------------

Configuration
~~~~~~~~~~~~~

.. automodule:: pyramid_ldap3

.. autofunction:: ldap_set_login_query

.. autofunction:: ldap_set_groups_query

.. autofunction:: ldap_setup

.. autofunction:: includeme

Usage
~~~~~

.. autofunction:: get_ldap_connector

.. autoclass:: Connector
   :members:

   .. attribute:: manager

       A ConnectionManager instance that can be used to perform
       arbitrary LDAP queries.

.. autofunction:: groupfinder

