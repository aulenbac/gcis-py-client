#import ez_setup
#ez_setup.use_setuptools()

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='GcisPyClient',
    version='1.0',
    author='Andrew Buddenberg',
    author_email='andrew.buddenberg@noaa.gov',
    packages=find_packages(),
    scripts=['bin/example', 'bin/problems', 'bin/sync_figures'],
    url='http://data.globalchange.gov',
    description='Client for GCIS webservices',
    long_description=open('README.md').read(),
    license='New BSD',
    data_files = [("", ["LICENSE.txt"])],
    install_requires=[
        "requests >= 2.1.0",
        "python-dateutil >= 2.2",
        "PyYAML >= 3.11",
        "beautifulsoup4 >= 4.3.2",
        "pytest >= 2.5.2"
    ],
    cmdclass={'test': PyTest},
)
