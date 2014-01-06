#!/usr/bin/python

import httplib
import urllib
import json
from domain import Figure, Image

from pickle import dump

base_url = 'data.gcis-dev-front.joss.ucar.edu'
# base_url = 'http://data-stage.globalchange.gov/report/nca3'
headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic YW5kcmV3LmJ1ZGRlbmJlcmdAbm9hYS5nb3Y6ZjBiNDc1OTUyMDY2MWY5M2U0N2E5Yzc4NjY1NWJjZjg0ZTZmZTU1NzUyYWI0ZmIx'
}
conn = httplib.HTTPConnection(base_url)


def check_image(fn):
    def wrapped(*args, **kwargs):
        # if len(args) < 1 or not isinstance(args[0], Image):
        #     raise Exception('Invalid Image')
        if args[0].identifier in (None, ''):
            raise Exception('Invalid identifier', args[0].identifier)
        fn(*args, **kwargs)

    return wrapped


def main():
    f = get_figure(report='nca3draft', chapter='our-changing-climate', figure='temperature-change')

    for i in f.images:
        # print i.as_json()
        i.identifier = ''
        delete_image(i)


def update_figure(figure):
    if figure.identifier in (None, ''):
        raise Exception('Invalid identifier', figure.identifier)


@check_image
def create_image(image):
    update_url = '/image/'.format(img=image.identifier)
    conn.request('POST', update_url, image.as_json(), headers)
    resp = conn.getresponse()
    return resp.status, resp.reason, resp.read()


@check_image
def update_image(image):
    update_url = '/image/{img}'.format(img=image.identifier)
    conn.request('POST', update_url, image.as_json(), headers)
    resp = conn.getresponse()
    return resp.status, resp.reason, resp.read()


@check_image
def delete_image(image):
    delete_url = '/image/{img}'.format(img=image.identifier)
    conn.request('DELETE', delete_url, None, headers)
    resp = conn.getresponse()
    return resp.status, resp.reason, resp.read()


def associate_image_with_figure(image_id, report, figure_id):
    url = '/report/{rpt}/figure/rel/{fig}'.format(rpt=report, fig=figure_id)
    conn.request('POST', url, json.dumps({'add_image_identifier': image_id}), headers)
    resp = conn.getresponse()
    return resp.status, resp.reason, resp.read()


def upload_image_file(image_id)

#Full listing
def get_figure_listing(report, chapter=None):
    chapter_filter = 'chapter/' + chapter if chapter else ''

    url = '/report/{rpt}/{chap}figure?{p}'.format(rpt=report, chap=chapter_filter, p=urllib.urlencode({'all': '1'}))
    conn.request('GET', url, None, headers)
    resp = conn.getresponse()

    return [Figure(figure) for figure in json.load(resp.read())]


def get_figure(report, figure, chapter=None):
    chapter_filter = '/chapter' + chapter if chapter else ''

    url = '/report/{rpt}/{chap}figure/{fig}?{p}'.format(rpt=report, chap=chapter_filter, fig=figure, p=urllib.urlencode({'all': '1'}))
    conn.request('GET', url, None, headers)
    resp = conn.getresponse()

    return Figure(json.load(resp))


if __name__ == "__main__":
    main()
