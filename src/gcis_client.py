#!/usr/bin/python

from base64 import b64encode
import urllib
import json
import requests
from domain import Figure, Image


def check_image(fn):
    def wrapped(*args, **kwargs):
        # if len(args) < 1 or not isinstance(args[0], Image):
        #     raise Exception('Invalid Image')
        if args[0].identifier in (None, ''):
            raise Exception('Invalid identifier', args[0].identifier)
        fn(*args, **kwargs)

    return wrapped


class GcisClient:
    headers = {
        'Accept': 'application/json'
    }

    def __init__(self, url, username, password):
        self.base_url = url
        self.headers['Authorization'] = 'Basic ' + b64encode(username + ':' + password)

    def update_figure(self, report_id, figure):
        if figure.identifier in (None, ''):
            raise Exception('Invalid identifier', figure.identifier)
        update_url = '{b}/report/{rpt}/figure/{fig}'.format(b=self.base_url, rpt=report_id, fig=figure.identifier)
        return requests.post(update_url, figure.as_json(), headers=self.headers)

    @check_image
    def create_image(self, image):
        update_url = '{b}/image/'.format(b=self.base_url, img=image.identifier)
        return requests.post(update_url, image.as_json(), headers=self.headers)

    @check_image
    def update_image(self, image):
        update_url = '{b}/image/{img}'.format(b=self.base_url, img=image.identifier)
        return requests.post(update_url, image.as_json(), headers=self.headers)

    @check_image
    def delete_image(self, image):
        delete_url = '{b}/image/{img}'.format(b=self.base_url, img=image.identifier)
        return requests.delete(delete_url, headers=self.headers)

    def associate_image_with_figure(self, image_id, report_id, figure_id):
        url = '{b}/report/{rpt}/figure/rel/{fig}'.format(b=self.base_url, rpt=report_id, fig=figure_id)
        return requests.post(url, json.dumps({'add_image_identifier': image_id}), headers=self.headers)

    def upload_image_file(self, image_id, filepath):
        url = '{b}/image/files/{id}'.format(b=self.base_url, id=image_id)
        # For future multi-part encoding support
        # return requests.put(url, headers=headers, files={'file': (filename, open(filepath, 'rb'))})
        return requests.put(url, data=open(filepath, 'rb'), headers=self.headers)

    #Full listing
    def get_figure_listing(self, report_id, chapter_id=None):
        chapter_filter = '/chapter/' + chapter_id if chapter_id else ''

        url = '{b}/report/{rpt}{chap}/figure?{p}'.format(
            b=self.base_url, rpt=report_id, chap=chapter_filter, p=urllib.urlencode({'all': '1'})
        )
        resp = requests.get(url, headers=self.headers)

        return [Figure(figure) for figure in resp.json()]

    def get_figure(self, report_id, figure_id, chapter_id=None):
        chapter_filter = '/chapter/' + chapter_id if chapter_id else ''

        url = '{b}/report/{rpt}{chap}/figure/{fig}?{p}'.format(
            b=self.base_url, rpt=report_id, chap=chapter_filter, fig=figure_id, p=urllib.urlencode({'all': '1'})
        )
        resp = requests.get(url, headers=self.headers)

        return Figure(resp.json())

