#!/usr/bin/python

from base64 import b64encode
import urllib
import json
import requests
from os.path import exists, basename
from domain import Figure, Image, Dataset


def check_image(fn):
    def wrapped(*args, **kwargs):
        # if len(args) < 1 or not isinstance(args[0], Image):
        #     raise Exception('Invalid Image')
        if args[1].identifier in (None, ''):
            raise Exception('Invalid identifier', args[0].identifier)
        return fn(*args, **kwargs)

    return wrapped


class GcisClient(object):
    def __init__(self, url, username, password):
        self.headers = {
            'Accept': 'application/json'
        }

        self.base_url = url
        self.headers['Authorization'] = 'Basic ' + b64encode(username + ':' + password)

    def create_figure(self, report_id, chapter_id, figure, skip_images=False):
        if figure.identifier in (None, ''):
            raise Exception('Invalid identifier', figure.identifier)

        url = '{b}/report/{rpt}/chapter/{chp}/figure/'.format(
            b=self.base_url, rpt=report_id, chp=chapter_id
        )

        resp = requests.post(url, data=figure.as_json(), headers=self.headers)

        if resp.status_code != 200:
            raise Exception(resp.text)

        if skip_images is False:
            for image in figure.images:
                self.create_image(image),
                self.associate_image_with_figure(image.identifier, report_id, figure.identifier)

        return resp

    def update_figure(self, report_id, chapter, figure, skip_images=False):
        if figure.identifier in (None, ''):
            raise Exception('Invalid identifier', figure.identifier)
        update_url = '{b}/report/{rpt}/chapter/{chp}/figure/{fig}'.format(
            b=self.base_url, rpt=report_id, chp=chapter, fig=figure.identifier
        )

        resp = requests.post(update_url, figure.as_json(), headers=self.headers)

        if resp.status_code != 200:
            raise Exception(resp.text)

        if skip_images is False:
            for image in figure.images:
                self.update_image(image)

        return resp

    def delete_figure(self, report_id, figure_id):
        url = '{b}/report/{rpt}/figure/{fig}'.format(b=self.base_url, rpt=report_id, fig=figure_id)
        return requests.delete(url, headers=self.headers)

    @check_image
    def create_image(self, image, report_id=None, figure_id=None):
        url = '{b}/image/'.format(b=self.base_url, img=image.identifier)
        responses = [requests.post(url, image.as_json(), headers=self.headers)]
        if image.local_path is not None:
            responses.append(self.upload_image_file(image.identifier, image.local_path))
        if figure_id and report_id:
            responses.append(self.associate_image_with_figure(image.identifier, report_id, figure_id))
        for dataset in image.datasets:
            self.associate_dataset_with_image(dataset.identifier, image.identifier)

        return responses

    @check_image
    def update_image(self, image):
        update_url = '{b}/image/{img}'.format(b=self.base_url, img=image.identifier)
        for dataset in image.datasets:
            self.associate_dataset_with_image(dataset.identifier, image.identifier)

        return requests.post(update_url, image.as_json(), headers=self.headers)

    @check_image
    def delete_image(self, image):
        delete_url = '{b}/image/{img}'.format(b=self.base_url, img=image.identifier)
        return requests.delete(delete_url, headers=self.headers)

    def associate_image_with_figure(self, image_id, report_id, figure_id):
        url = '{b}/report/{rpt}/figure/rel/{fig}'.format(b=self.base_url, rpt=report_id, fig=figure_id)
        return requests.post(url, json.dumps({'add_image_identifier': image_id}), headers=self.headers)

    def upload_image_file(self, image_id, local_path):
        url = '{b}/image/files/{id}/{fn}'.format(b=self.base_url, id=image_id, fn=basename(local_path))
        # For future multi-part encoding support
        # return requests.put(url, headers=headers, files={'file': (filename, open(filepath, 'rb'))})
        if not exists(local_path):
            raise Exception('File not found: ' + local_path)

        return requests.put(url, data=open(local_path, 'rb'), headers=self.headers)

    #Full listing
    def get_figure_listing(self, report_id, chapter_id=None):
        chapter_filter = '/chapter/' + chapter_id if chapter_id else ''

        url = '{b}/report/{rpt}{chap}/figure?{p}'.format(
            b=self.base_url, rpt=report_id, chap=chapter_filter, p=urllib.urlencode({'all': '1'})
        )
        resp = requests.get(url, headers=self.headers)

        try:
            return [Figure(figure) for figure in resp.json()]
        except ValueError:
            raise Exception('Add a better exception string here')

    def get_figure(self, report_id, figure_id, chapter_id=None):
        chapter_filter = '/chapter/' + chapter_id if chapter_id else ''

        url = '{b}/report/{rpt}{chap}/figure/{fig}?{p}'.format(
            b=self.base_url, rpt=report_id, chap=chapter_filter, fig=figure_id, p=urllib.urlencode({'all': '1'})
        )
        resp = requests.get(url, headers=self.headers)

        try:
            return Figure(resp.json())
        except ValueError:
            raise Exception(resp.text)

    def get_image(self, image_id):
        url = '{b}/image/{img}'.format(b=self.base_url, img=image_id)

        return Image(requests.get(url, headers=self.headers).json())

    def test_login(self):
        url = '{b}/login.json'.format(b=self.base_url)
        resp = requests.get(url, headers=self.headers)
        return resp.status_code, resp.text

    def get_keyword_listing(self):
        url = '{b}/gcmd_keyword?{p}'.format(b=self.base_url, p=urllib.urlencode({'all': '1'}))
        resp = requests.get(url, headers=self.headers)

        return resp.json()

    def get_keyword(self, key_id):
        url = '{b}/gcmd_keyword/{k}'.format(b=self.base_url, k=key_id)
        return requests.get(url, headers=self.headers).json()

    def associate_keyword_with_figure(self, keyword_id, report_id, figure_id):
        url = '{b}/report/{rpt}/figure/keywords/{fig}'.format(b=self.base_url, rpt=report_id, fig=figure_id)
        return requests.post(url, data=json.dumps({'identifier': keyword_id}), headers=self.headers)

    def get_dataset(self, dataset_id):
        url = '{b}/dataset/{ds}'.format(b=self.base_url, ds=dataset_id)
        resp = requests.get(url, headers=self.headers)
        try:
            return Dataset(resp.json())
        except ValueError:
            raise Exception(resp.text())

    def create_dataset(self, dataset):
        url = '{b}/dataset/'.format(b=self.base_url)
        print dataset.as_json(indent=4)
        return requests.post(url, data=dataset.as_json(), headers=self.headers)

    def update_dataset(self, dataset):
        url = '{b}/dataset/{ds}'.format(b=self.base_url, ds=dataset.identifier)
        return requests.post(url, data=dataset.as_json(), headers=self.headers)

    def delete_dataset(self, dataset):
        url = '{b}/dataset/{ds}'.format(b=self.base_url, ds=dataset.identifier)
        return requests.delete(url, headers=self.headers)

    def associate_dataset_with_image(self, dataset_id, image_id):
        url = '{b}/image/prov/{img}'.format(b=self.base_url, img=image_id)
        data = {
            'parent_uri': '/dataset/' + dataset_id,
            'parent_rel': 'prov:wasDerivedFrom'
        }
        resp = requests.post(url, data=json.dumps(data), headers=self.headers)
        if resp.status_code != 200:
            raise Exception('Dataset association failed:\n{url}\n{resp}'.format(url=url, resp=resp.text))
        return resp
