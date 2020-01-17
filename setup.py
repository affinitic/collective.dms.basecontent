#! -*- coding: utf8 -*-
from setuptools import setup, find_packages

version = '0.1.2.dev0'

long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

setup(name='collective.dms.basecontent',
      version=version,
      description="Base content types for document management system",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Ecreall, Entrouvert, IMIO',
      author_email='cedricmessiant@ecreall.com',
      url='https://github.com/collective/collective.dms.basecontent',
      license='gpl',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['collective', 'collective.dms'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'five.grok',
          'collective.documentviewer',
          'collective.select2',
          'plone.api',
          'plone.app.dexterity',
          'plone.namedfile',
          'z3c.blobfile',
          'plone.app.contenttypes',
          'plone.app.relationfield',
          'plone.formwidget.contenttree',
          'plone.principalsource',
          'collective.z3cform.chosen',
          'collective.z3cform.rolefield',
          'z3c.table',
          'plone.memoize',
      ],
      extras_require={
          'test': ['plone.app.testing',
                   'ecreall.helpers.testing',
                   'plone.app.vocabularies'
                   ],
          },
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
