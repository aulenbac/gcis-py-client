__author__ = 'abuddenberg'

#To run the tests:
# py.test -v test_suite.py


from test_data import test_figure_json, test_image_json, webform_json_temp, webform_json_precip
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


def test_chapter_parsing():
    webform_fig = Figure(json.loads(webform_json_precip))
    gcis_fig = Figure(json.loads(test_figure_json))

    assert isinstance(webform_fig.ordinal, int)
    assert webform_fig.figure_num == 17
    assert webform_fig.ordinal == 17
    assert webform_fig.chapter is None

    merged_figure = webform_fig.merge(gcis_fig)
    #FYI, these are identical; I just wanted the variable name to reflect the merge
    assert id(merged_figure) == id(webform_fig)

    assert merged_figure.figure_num == '2.17'
    assert merged_figure.ordinal == 17
    assert isinstance(merged_figure.chapter, Chapter)
    assert merged_figure.chapter.number == 2

if __name__ == '__main__':
    test_chapter_parsing()