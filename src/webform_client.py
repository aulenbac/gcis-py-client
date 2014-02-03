#!/usr/bin/python

import urllib
import requests
import re
import os.path

from domain import Figure, Image


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

    def __init__(self, url, token, local_image_repo='../dist/images/'):
        self.base_url = url
        self.token = token
        self.images_dir = local_image_repo

    def get_list(self):
        url = '{b}/metadata/list?token={t}'.format(b=self.base_url, t=self.token)
        return requests.get(url).json()

    def get_all_webforms(self):
        pass


    @sanitized('^/metadata/figures/\d+$')
    def get_webform(self, fig_url):
        full_url = '{b}{url}?token={t}'.format(b=self.base_url, url=fig_url, t=self.token)
        figure_json = requests.get(full_url).json()

        #TODO: refactor the service so this isn't necessary
        id = figure_json.keys()[0]
        f = Figure(figure_json[id]['figure'][0])
        # f.images = [Image(image) for image in figure_json[id]['images']]
        for i in figure_json[id]['images']:
            image = Image(i)
            if image.filepath not in (None, ''):
                #TODO: this sucks in every way; make it better
                png_image = image.filepath.split('/')[-1].replace('.eps', '.png')
                image.filepath = os.path.join(self.images_dir, png_image) if self.local_image_exists(png_image) else image.filepath

            f.images.append(image)

        return f

    def local_image_exists(self, filename):
        return os.path.exists(os.path.join(self.images_dir, filename))

    def remote_image_exists(self, path):
        url = '{b}{path}?token={t}'.format(b=self.base_url, path=path, t=self.token)
        resp = requests.head(url)
        print resp.status_code, resp.text
        return True if resp.status_code == 200 else False

    def download_image(self, path):
        url = '{b}{path}?token={t}'.format(b=self.base_url, path=path, t=self.token)
        resp = requests.get(url, stream=True)

        if resp.status_code == 200:
            filepath = os.path.join(self.images_dir, path.split('/')[-1])
            with open(filepath, 'wb') as image_out:
                for bytes in resp.iter_content(chunk_size=4096):
                    image_out.write(bytes)

            return filepath
        else:
            return resp

