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
    version='0.67',
    author='Andrew Buddenberg',
    author_email='andrew.buddenberg@noaa.gov',
    packages=find_packages(),
    scripts=['bin/example', 'bin/problems', 'bin/sync_figures'],
    url='http://data.globalchange.gov',
    description='CLient for GCIS webservices',
    long_description=open('README.txt').read(),
    install_requires=[
        "requests >= 2.1.0",
        "python-dateutil >= 2.2"
    ],
    tests_require=["pytest >= 2.5.2"],
    cmdclass={'test': PyTest},
)
