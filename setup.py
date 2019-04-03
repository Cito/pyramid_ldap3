from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))
README = open(path.join(here, 'README.rst')).read()
CHANGES = open(path.join(here, 'CHANGES.txt')).read()

requires = ['pyramid>=1.4', 'ldap3>=2.0']

sampleapp_extras = [
    'waitress', 'pyramid_chameleon', 'pyramid_debugtoolbar']
testing_extras = [
    'nose', 'coverage']
docs_extras = [
    'Sphinx', 'docutils',
    'repoze.sphinx.autointerface', 'pylons-sphinx-themes']

setup(
    name='pyramid_ldap3',
    version='0.4.1',
    description='pyramid_ldap3',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        'Topic :: Software Development :: Libraries :: Python Modules',
        "Topic :: System :: Systems Administration"
            " :: Authentication/Directory :: LDAP",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
        "License :: Repoze Public License"],
    author='Chris McDonough, Christoph Zwerschke',
    author_email='pylons-discuss@groups.google.com',
    url='https://trypyramid.com/extending-pyramid.html',
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    keywords='web pyramid pylons ldap auth authentication',
    packages=find_packages(exclude=['docs', 'tests', 'sampleapp']),
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    extras_require=dict(
        sampleapp=sampleapp_extras,
        docs=docs_extras,
        testing=testing_extras),
    test_suite='tests',
    entry_points={
        'paste.app_factory': ['sampleapp = sampleapp:main']})
