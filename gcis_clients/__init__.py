from gcis_client import GcisClient
from webform_client import WebformClient

from os.path import expanduser, exists
from os import makedirs


def default_image_dir():
    image_dir = expanduser('~/.gcis-py-client/images/')
    if not exists(image_dir):
        makedirs(image_dir)
    return image_dir

