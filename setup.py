from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))
README = open(path.join(here, 'README.md')).read()
CHANGES = open(path.join(here, 'CHANGES.txt')).read()

requires = ['pyramid>=1.4', 'ldap3>=2.0']

sampleapp_extras = [
    'waitress', 'pyramid_chameleon', 'pyramid_debugtoolbar']
testing_extras = ['coverage']
docs_extras = [
    'Sphinx>=3,<4',
    'repoze.sphinx.autointerface>=0.8,<1',
    'pylons-sphinx-themes>=1.0.8']

setup(
    name='pyramid_ldap3',
    version='0.5',
    description='pyramid_ldap3',
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type='text/markdown',
    classifiers=[
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        'Topic :: Software Development :: Libraries :: Python Modules',
        "Topic :: System :: Systems Administration"
            " :: Authentication/Directory :: LDAP",
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
        "License :: Repoze Public License"],
    author='Chris McDonough, Christoph Zwerschke',
    author_email='pylons-discuss@googlegroups.com',
    url='https://trypyramid.com/extending-pyramid.html',
    license="BSD-derived (Repoze)",
    keywords=['web', 'pyramid', 'pylons', 'ldap', 'auth', 'authentication'],
    packages=find_packages(exclude=['docs', 'tests', 'sampleapp']),
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    extras_require=dict(
        sampleapp=sampleapp_extras,
        docs=docs_extras,
        testing=testing_extras),
    test_suite='tests',
    entry_points={'paste.app_factory': ['sampleapp = sampleapp:main']})
