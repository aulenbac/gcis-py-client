#!/usr/bin/python

from base64 import b64encode
import urllib
import json
from os.path import exists, basename

import requests

from domain import Figure, Image, Dataset, Activity


def check_image(fn):
    def wrapped(*args, **kwargs):
        # if len(args) < 1 or not isinstance(args[0], Image):
        #     raise Exception('Invalid Image')
        if args[1].identifier in (None, ''):
            raise Exception('Invalid identifier', args[0].identifier)
        return fn(*args, **kwargs)

    return wrapped


def exists(fn):
    def wrapped(*args, **kwargs):
        resp = fn(*args, **kwargs)
        if resp.status_code == 200:
            return True
        elif resp.status_code == 404:
            return False
        else:
            raise Exception(resp.text)
    return wrapped


def http_resp(fn):
    def wrapped(*args, **kwargs):
        resp = fn(*args, **kwargs)
        if resp.status_code == 200:
            return resp
        else:
            raise Exception(resp.text)
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
            raise Exception('Invalid figure identifier', figure.identifier)

        #Is GCIS not inferring this from the url parameter?
        if figure.chapter_identifier in (None, ''):
            figure.chapter_identifier = chapter_id

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

    def update_figure(self, report_id, chapter_id, figure, skip_images=False):
        if figure.identifier in (None, ''):
            raise Exception('Invalid identifier', figure.identifier)

        #Is GCIS not inferring this from the url parameter?
        if figure.chapter_identifier in (None, ''):
            figure.chapter_identifier = chapter_id

        update_url = '{b}/report/{rpt}/chapter/{chp}/figure/{fig}'.format(
            b=self.base_url, rpt=report_id, chp=chapter_id, fig=figure.identifier
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
        resp = requests.post(url, image.as_json(), headers=self.headers)
        if image.local_path is not None:
            self.upload_image_file(image.identifier, image.local_path)
        if figure_id and report_id:
            self.associate_image_with_figure(image.identifier, report_id, figure_id)
        for dataset in image.datasets:
            self.create_activity(dataset.activity)
            self.associate_dataset_with_image(dataset.identifier, image.identifier,
                                              activity_id=dataset.activity.identifier)

        return resp

    @check_image
    def update_image(self, image):
        update_url = '{b}/image/{img}'.format(b=self.base_url, img=image.identifier)
        for dataset in image.datasets:
            self.update_activity(dataset.activity)
            self.associate_dataset_with_image(dataset.identifier, image.identifier,
                                              activity_id=dataset.activity.identifier)

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

    @exists
    def figure_exists(self, report_id, figure_id, chapter_id=None):
        chapter_filter = '/chapter/' + chapter_id if chapter_id else ''

        url = '{b}/report/{rpt}{chap}/figure/{fig}?{p}'.format(
            b=self.base_url, rpt=report_id, chap=chapter_filter, fig=figure_id, p=urllib.urlencode({'all': '1'})
        )
        return requests.head(url, headers=self.headers)

    def get_image(self, image_id):
        url = '{b}/image/{img}'.format(b=self.base_url, img=image_id)
        resp = requests.get(url, headers=self.headers)

        try:
            return Image(resp.json())
        except ValueError:
            raise Exception(resp.text)

    @exists
    def image_exists(self, image_id):
        url = '{b}/image/{img}'.format(b=self.base_url, img=image_id)
        return requests.head(url, headers=self.headers)

    def has_all_associated_images(self, report_id, figure_id, target_image_ids):
        try:
            figure_image_ids = [i.identifier for i in self.get_figure(report_id, figure_id).images]
        except Exception, e:
            print e.message
            return False, set()

        target_set = set(target_image_ids)
        gcis_set = set(figure_image_ids)
        deltas = target_set - gcis_set

        if target_set.issubset(gcis_set):
            return True, deltas
        else:
            return False, deltas

    def test_login(self):
        url = '{b}/login.json'.format(b=self.base_url)
        resp = requests.get(url, headers=self.headers, verify=False)
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
        resp = requests.get(url, headers=self.headers, verify=False)
        try:
            return Dataset(resp.json())
        except ValueError:
            raise Exception(resp.text())

    @exists
    def dataset_exists(self, dataset_id):
        url = '{b}/dataset/{ds}'.format(b=self.base_url, ds=dataset_id)
        return requests.head(url, headers=self.headers)

    def create_dataset(self, dataset):
        url = '{b}/dataset/'.format(b=self.base_url)
        return requests.post(url, data=dataset.as_json(), headers=self.headers)

    def update_dataset(self, dataset):
        url = '{b}/dataset/{ds}'.format(b=self.base_url, ds=dataset.identifier)
        return requests.post(url, data=dataset.as_json(), headers=self.headers)

    def delete_dataset(self, dataset):
        url = '{b}/dataset/{ds}'.format(b=self.base_url, ds=dataset.identifier)
        return requests.delete(url, headers=self.headers)

    def associate_dataset_with_image(self, dataset_id, image_id, activity_id=None):
        url = '{b}/image/prov/{img}'.format(b=self.base_url, img=image_id)

        data = {
            'parent_uri': '/dataset/' + dataset_id,
            'parent_rel': 'prov:wasDerivedFrom'
        }
        if activity_id:
            data['activity'] = activity_id

        self.delete_dataset_image_assoc(dataset_id, image_id)
        resp = requests.post(url, data=json.dumps(data), headers=self.headers)

        if resp.status_code == 200:
            return resp
        #TODO: Change to 409 in next release
        elif resp.status_code == 400:
            print resp.text
            print 'Duplicate dataset association {ds} for image: {img}'.format(ds=dataset_id, img=image_id)
            return resp
        else:
            raise Exception('Dataset association failed:\n{url}\n{resp}'.format(url=url, resp=resp.text))

    def delete_dataset_image_assoc(self, dataset_id, image_id):
        url = '{b}/image/prov/{img}'.format(b=self.base_url, img=image_id)

        data = {
            'delete': {
                'parent_uri': '/dataset/' + dataset_id,
                'parent_rel': 'prov:wasDerivedFrom'
            }
        }
        print data

        print json.dumps(data)
        resp = requests.post(url, data=json.dumps(data), headers=self.headers)

        if resp.status_code == 200:
            return resp
        else:
            print resp.status_code
            raise Exception('Dataset dissociation failed:\n{url}\n{resp}'.format(url=url, resp=resp.text))

    # @exists
    def activity_exists(self, activity_id):
        url = '{b}/activity/{act}'.format(b=self.base_url, act=activity_id)
        resp = requests.head(url, headers=self.headers)
        if resp.status_code == 200:
            return True
        else:
            return False

    def get_activity(self, activity_id):
        url = '{b}/activity/{act}'.format(b=self.base_url, act=activity_id)
        resp = requests.get(url, headers=self.headers, verify=False)
        try:
            return Activity(resp.json())
        except ValueError:
            raise Exception(resp.text())

    @http_resp
    def create_activity(self, activity):
        url = '{b}/activity/'.format(b=self.base_url)
        return requests.post(url, data=activity.as_json(), headers=self.headers)

    @http_resp
    def update_activity(self, activity):
        url = '{b}/activity/{act}'.format(b=self.base_url, act=activity.identifier)
        return requests.post(url, data=activity.as_json(), headers=self.headers)

    @http_resp
    def delete_activity(self, activity):
        url = '{b}/activity/{act}'.format(b=self.base_url, act=activity.identifier)
        return requests.delete(url, headers=self.headers)

