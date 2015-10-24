import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['pyramid>=1.3', 'ldap3']

sampleapp_extras = [
    'waitress',
    'pyramid_debugtoolbar']
testing_extras = ['nose', 'coverage']
docs_extras = ['Sphinx']

setup(
    name='pyramid_ldap3',
    version='0.2.3',
    description='pyramid_ldap3',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: System :: Systems Administration"
            " :: Authentication/Directory :: LDAP",
        "License :: Repoze Public License"],
    author='Chris McDonough, Christoph Zwerschke',
    author_email='pylons-discuss@groups.google.com',
    url='http://pylonsproject.org',
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    keywords='web pyramid pylons ldap',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    extras_require=dict(
        sampleapp=sampleapp_extras,
        docs=docs_extras,
        testing=testing_extras),
    test_suite='pyramid_ldap3',
    entry_points="""\
    [paste.app_factory]
    sampleapp = sampleapp:main
    """)
