gcis-py-client
===========

gcis-py-client provides a python-based abstraction of the Global Change
Information System Structured Data Server [API](http://data.globalchange.gov).

Installation
------------

### Requirements

These should be available through the package manager of your choice
(Macports, apt, yum, etc.):

* Python 2.7.x (though it might work with previous versions)
* Setuptools 2.0.x
* pip is highly recommended


To install from git with pip:

    pip install git+http://github.com/USGCRP/gcis-py-client

To install from tarball:

    tar -xzvf GcisPyClient-x.y.tar.gz
    cd GcisPyClient-x.y

    python setup.py test (to run the test suite)
    python setup.py install (to install)

Setup
-----

### User Credentials

GcisClient will use the first credentials it finds while searching the following places:

1. Strings passed directly to the GcisClient constructor.
2. Environment variables "GCIS_USER" and "GCIS_KEY" (both are required)
3. Config file at $HOME/etc/Gcis.conf (A sample of this file is included below)
4. Config file at $HOME/.gcis-py-client/Gcis.conf
5. Interactively, with a username and key prompt

Sample Gcis.conf file:

    - url      : http://data-stage.globalchange.gov
      userinfo : me@example.com:298015f752D99E789056EF826A7D97afc38a8bbd6e3e23b3
      key      : M2FiLtG2n2qTyJHIztvHm5zweTYjNkM5ZWEtYjNkMS00LTgS00LTg2N2QtYZDFhzQyNGUxCg==

    - url      : http://data.globalchange.gov
      userinfo : username:pass
      key      : key

Usage
-----

    from gcis_clients import GcisClient

    base_url = 'http://data.gcis-dev-front.joss.ucar.edu'
    gcis = GcisClient(base_url, 'andrew.buddenberg@noaa.gov', 'your api key here')

Make sure our credentials work:

    status_code, resp_text = gcis.test_login()
    print status_code, resp_text
    assert 'auth_required' not in resp_text

Let's pull a list of all figures in Chapter 2 of the nca3:

    for partial_figure in gcis.get_figure_listing('nca3', chapter_id='our-changing-climate'):
        full_figure = gcis.get_figure('nca3', partial_figure.identifier, chapter_id='our-changing-climate')
        print full_figure


Let's work with the infamous temperature figure:

    fig2_7 = gcis.get_figure('nca3', 'observed-us-temperature-change')

Warning: Images and Chapters are specifically excluded from JSON output.  This is what gets sent to GCIS. So...

    print fig2_7.as_json(indent=4)

...you might want to view the original input:

    print fig2_7.original

Let's see about the images:

    for image in fig2_7.images:
        print image

How about the whole Image?:

    print gcis.get_image('69da6d93-4426-4061-a2a1-7b3d01f2dc1c').as_json(indent=4)
