import sys

from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand

from keybase_proofs import get_version


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='django-keybase-proofs',
    version=get_version().replace(' ', '-'),
    description='Support for keybase proofs in Django',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Josh Blum',
    author_email='jblum18@gmail.com',
    url='https://github.com/keybase/django-keybase-proofs',
    package_dir={'keybase_proofs': 'keybase_proofs'},
    packages=find_packages(exclude='test_app'),
    tests_require=['pytest-django'],
    cmdclass={'test': PyTest},
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
)
