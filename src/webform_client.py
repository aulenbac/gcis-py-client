#!/usr/bin/python

import urllib
import requests
import re

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

    def __init__(self, url, token):
        self.base_url = url
        self.token = token

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
        f.images = [Image(image) for image in figure_json[id]['images']]

        return f

    def download_image(self, path):
        url = '{b}{path}?token={t}'.format(b=self.base_url, path=path, t=self.token)
        resp = requests.get(url, stream=True)

        if resp.status_code == 200:
            filename = path.split('/')[-1]
            with open('../dist/images/' + filename, 'wb') as image_out:
                for bytes in resp.iter_content(chunk_size=4096):
                    image_out.write(bytes)

            print 'Downloaded: ' + filename

