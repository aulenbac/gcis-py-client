#!/usr/bin/python

import urllib
import re
from os.path import join

import requests
from dateutil.parser import parse

from domain import Figure, Image, Dataset, Activity


def sanitized(pattern):
    def dec(fn):
        def wrapped(*args, **kwargs):
            if re.match(pattern, urllib.quote(args[1])):
                return fn(*args, **kwargs)
            else:
                print 'Shitlisted: ', args[1]
        return wrapped
    return dec


class WebformClient:

    def __init__(self, url, token, local_image_dir='../dist/images/'):
        self.base_url = url
        self.token = token
        self.images_dir = local_image_dir
        self.remote_image_dir = '/system/files/'

    def get_list(self):
        url = '{b}/metadata/list?token={t}'.format(b=self.base_url, t=self.token)
        return requests.get(url).json()

    def get_all_webforms(self):
        pass


    @sanitized('^/metadata/figures/\d+$')
    def get_webform(self, fig_url, download_images=False):
        full_url = '{b}{url}?token={t}'.format(b=self.base_url, url=fig_url, t=self.token)
        webform_json = requests.get(full_url).json()

        #TODO: refactor the service so this isn't necessary
        webform_nid = webform_json.keys()[0]
        f = Figure(webform_json[webform_nid]['figure'][0])

        if 'images' in webform_json[webform_nid]:
            for img_idx, image in enumerate(webform_json[webform_nid]['images']):
                image_obj = Image(image, local_path=self.get_local_image_path(image),
                                  remote_path=self.get_remote_image_path(image))

                #TODO: this just keeps getting worse
                if 'datasources' in webform_json[webform_nid]['images'][img_idx]:
                    for dataset_json in webform_json[webform_nid]['images'][img_idx]['datasources']:
                        dataset = Dataset(dataset_json)

                        #Commence the hacks
                        try:
                            dataset.temporal_extent = ' '.join(
                                [parse(dataset_json[field]).isoformat() for field in ['start_time', 'end_time']]
                            )
                        except TypeError, e:
                            print 'Problem with start/end time: ', fig_url, f.title, e
                            print dataset_json['start_time'], dataset_json['end_time']
                            dataset.temporal_extent = None
                        except ValueError, e:
                            print 'Problem with start/end time: ', fig_url, f.title, e
                            print dataset_json['start_time'], dataset_json['end_time']
                            dataset.temporal_extent = None

                        dataset.spatial_extent = ' '.join(['{k}: {v};'.format(k=key, v=dataset_json[key]) for key in
                                                           ['maximum_latitude', 'minimum_latitude', 'maximum_longitude',
                                                            'minimum_longitude']])

                        #Filter overlapping Dataset keys out
                        activity_json = {k: dataset_json[k] for k in dataset_json if
                                         k not in ['href', 'uri', 'identifier', 'start_time', 'end_time']}

                        #Add synthetic identifier
                        activity_json['identifier'] = dataset.identifier + '-process'
                        dataset.activity = Activity(activity_json)

                        #TODO: Extract DOIs from citation
                        image_obj.datasets.append(dataset)

                f.images.append(image_obj)
            #If download_images arg is set, attempt to download all images for this figure
            if download_images:
                self.download_all_images(f)
        return f

    def get_remote_image_path(self, image_json):
        filename_key = 'what_is_the_file_name_extension_of_the_image'
        if image_json not in (None, '') and image_json[filename_key] not in (None, ''):
            return self.remote_image_dir + image_json[filename_key].lower()

    def get_local_image_path(self, image_json):
        filename_key = 'what_is_the_file_name_extension_of_the_image'
        if image_json not in (None, '') and image_json[filename_key] not in (None, ''):
            return join(self.images_dir, image_json[filename_key].lower())

    # def local_image_exists(self, filename):
    #     return exists(join(self.images_dir, filename))

    def remote_image_exists(self, path):
        url = '{b}{path}?token={t}'.format(b=self.base_url, path=path, t=self.token)
        resp = requests.head(url)
        # print resp.status_code, resp.text
        return True if resp.status_code == 200 else False

    def download_image(self, image):
        url = '{b}{path}?token={t}'.format(b=self.base_url, path=image.remote_path, t=self.token)
        resp = requests.get(url, stream=True)

        if resp.status_code == 200:
            filepath = join(self.images_dir, image.remote_path.split('/')[-1])
            with open(filepath, 'wb') as image_out:
                for bytes in resp.iter_content(chunk_size=4096):
                    image_out.write(bytes)

            return filepath
        elif resp.status_code == 404:
            raise Exception('Image not found: {u}'.format(u=url))
        else:
            raise Exception(resp.status_code)

    def download_all_images(self, figure):
        for image in figure.images:
            self.download_image(image)

    def get_aggregated_datasets(self):
        dataset_map = {}

        for item in self.get_list():
            webform_url = item['url']

            f = self.get_webform(webform_url)

            #aggregate datasets
            for image in f.images:
                for dataset in image.datasets:
                    if dataset.identifier not in dataset_map:
                        dataset_map[dataset.identifier] = dataset
                    else:
                        dataset_map[dataset.identifier].merge(dataset)
                        dataset_map[dataset.identifier].activity.merge(dataset.activity)

        return dataset_map.values()