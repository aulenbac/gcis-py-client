__author__ = 'abuddenberg'

#To run the tests:
# py.test -v test_suite.py


from test_data import test_figure_json, test_image_json
import json
from domain import Gcisbase, Figure, Image, Dataset, Chapter


def test_gcis_client_version():
    assert True


def test_domain():
    f = Figure(json.loads(test_figure_json))

    assert isinstance(f, Gcisbase)
    assert isinstance(f, Figure)

    assert len(f.images) == 11
    assert all([isinstance(i, Image) for i in f.images])

    assert isinstance(f.chapter, Chapter)
    assert f.chapter.identifier == 'our-changing-climate'

    i = Image(json.loads(test_image_json))
    assert isinstance(i, Image)


def test_domain_as_json():
    f = Figure(json.loads(test_figure_json))

    assert f.original['chapter']['identifier'] == 'our-changing-climate'
    assert f.original['images'] not in (None, '')
    assert f.original['uri'] not in (None, '')

    #Make sured fields specifically
    fig_json_out = json.loads(f.as_json())
    assert all([omitted_key not in fig_json_out for omitted_key in ['chapter', 'images', 'uri', 'href']])

    i = Image(json.loads(test_image_json))

    assert i.original['uri'] not in (None, '')
    assert i.original['href'] not in (None, '')

    img_json_out = json.loads(i.as_json())
    assert all([omitted_key not in img_json_out for omitted_key in ['uri', 'href']])


if __name__ == '__main__':
    test_domain_as_json()