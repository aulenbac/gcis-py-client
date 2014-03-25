import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

setup(
    name='GcisPyClient',
    version='0.67',
    author='Andrew Buddenberg',
    author_email='andrew.buddenberg@noaa.gov',
    packages=['gcis-py-client', 'gcis-py-client.test'],
    scripts=['bin/example.py'],
    url='http://data.globalchange.gov',
    description='CLient for GCIS webservices',
    long_description=open('README.txt').read(),
    install_requires=[
        "requests >= 2.1.0",
    ],
)
