from setuptools import setup, find_packages

setup(
    name='collective.autoqueryplan',
    version='0.1.0.dev0',
    description='Periodic saving of the catalog queryplan to improve memory usage',
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGES.txt').read()),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.0',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='',
    author='Dylan Jay',
    author_email='software@pretaweb.com',
    url='https://github.com/collective/collective.autoqueryplan/',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Zope2',
        'five.globalrequest',
    ],
    extras_require={
    },
    entry_points='''
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    '''
)
