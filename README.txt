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

    pip install git+ssh://gcis-dev-back/usr/local/projects/repos/gcis-py-client.git/

To install from tarball:

    tar -xzvf GcisPyClient-0.67.tar.gz
    cd GcisPyClient-0.67

    python setup.py test (to run the test suite)
    python setup.py install (to install)

Usage
-----

    from gcis_clients import GcisClient

    base_url = 'http://data.gcis-dev-front.joss.ucar.edu'
    gcis = GcisClient(base_url, 'andrew.buddenberg@noaa.gov', 'your api key here')

Make sure our credentials work:

    status_code, resp_text = gcis.test_login()
    print status_code, resp_text
    assert 'auth_required' not in resp_text

Let's pull a list of all figures in Chapter 2 of the NCA3draft:

    for partial_figure in gcis.get_figure_listing('nca3draft', chapter_id='our-changing-climate'):
        full_figure = gcis.get_figure('nca3draft', partial_figure.identifier, chapter_id='our-changing-climate')
        print full_figure


Let's work with the infamous temperature figure:

    fig2_7 = gcis.get_figure('nca3draft', 'observed-us-temperature-change')

Warning: Images and Chapters are specifically excluded from JSON output.  This is what gets sent to GCIS. So...

    print fig2_7.as_json(indent=4)

...you might want to view the original input:

    print fig2_7.original

Let's see about the images:

    for image in fig2_7.images:
        print image

How about the whole Image?:

    print gcis.get_image('69da6d93-4426-4061-a2a1-7b3d01f2dc1c').as_json(indent=4)
