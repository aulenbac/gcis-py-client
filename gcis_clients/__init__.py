from gcis_client import GcisClient, AssociationException
from webform_client import WebformClient
from nca3_client import Nca3Client

from os.path import expanduser, exists
from os import makedirs, getenv


def default_image_dir():
    image_dir = expanduser('~/.gcis-py-client/images/')
    if not exists(image_dir):
        makedirs(image_dir)
    return image_dir

#Magic environment variables
gcis_prod_auth = (getenv('GCIS_PROD_USER'), getenv('GCIS_PROD_KEY'))
gcis_stage_auth = (getenv('GCIS_STAGE_USER'), getenv('GCIS_STAGE_KEY'))
gcis_dev_auth = (getenv('GCIS_DEV_USER'), getenv('GCIS_DEV_KEY'))

gcis_auth = (getenv('GCIS_USER'), getenv('GCIS_KEY'))

webform_token = getenv('WEBFORM_TOKEN')