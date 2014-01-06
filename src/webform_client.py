#!/usr/bin/python

import urllib
import urllib2
import json
import re

from domain import Figure, Image
from gcis_client import update_image, get_figure, create_image, associate_image_with_figure, upload_image_file

prod = {'base': 'http://resources.assessment.globalchange.gov', 'token': 'mgTD63FAjG'}
dev_base = 'http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9'


def sanitized(pattern):
    def dec(fn):
        def wrapped(*args, **kwargs):
            if re.match(pattern, urllib.quote(args[0])):
                return fn(*args, **kwargs)
            else:
                print 'Shitlisted: ', args[0]
        return wrapped
    return dec


def get_list():
    url = '{base}/metadata/list?token={token}'.format(**prod)
    figure = json.load(urllib2.urlopen(url))

    return figure


def get_all_webforms():
    pass


@sanitized('^/metadata/figures/\d+$')
def get_webform(url):
    prod['url'] = url
    full_url = '{base}{url}?token={token}'.format(**prod)
    figure_json = json.load(urllib2.urlopen(full_url))

    #TODO: refactor the service so this isn't necessary
    id = figure_json.keys()[0]
    f = Figure(figure_json[id]['figure'][0])
    f.images = [Image(image) for image in figure_json[id]['images']]

    return f


# for listing in get_list():
#     print listing

#Hack
file_map = {
    '69da6d93-4426-4061-a2a1-7b3d01f2dc1c': '../AK.jpg',
    '230cb2f8-92e0-4897-ab5f-4d6339673832': '../US.jpg',
    '1f5a3cdd-fc45-403e-bf11-d1772005b430': '../GPN.jpg',
    'b180cfd9-b064-4644-a9a1-d2c3660c1be7': '../MW.jpg',
    'fa83c34b-7b67-4b74-bcba-5bf60ba7730f': '../NE.jpg',
    'ca983a87-53a7-4c42-b0e9-18d26fad40ba': '../SE.jpg',
    '68537d68-b14c-4811-908a-5dc0ab73879b': '../GPS.jpg',
    '26a28c2a-75f2-47f7-a40f-becfc468d3d6': '../SW.jpg',
    'f69194e8-397d-4f9c-836c-335d259ee09c': '../HI.jpg',
    'db4d291d-17c5-4e10-b760-6c8799a8d709': '../NW.jpg',
    '8e74f576-a5af-46c0-b33a-f30072118b86': '../usgcrp_draft-038-012.jpg',
}

figure = get_webform('/metadata/figures/3175')

for image in figure.images:
    image.filename = file_map[image.identifier]

print upload_image_file('69da6d93-4426-4061-a2a1-7b3d01f2dc1c', 'AK.jpg', '../AK.jpg').text

# f = get_figure(report='nca3draft', chapter='our-changing-climate', figure='temperature-change')
#
# print json.dumps(f.original, indent=4)

# for i in figure.images[0:-2]:
    # print create_image(i)

# print associate_image_with_figure('69da6d93-4426-4061-a2a1-7b3d01f2dc1c', 'nca3draft', 'temperature-change')




# print json.dumps(get_webform(url), indent=4, sort_keys=True)

