__author__ = 'abuddenberg'

from webform_client import WebformClient
from gcis_client import GcisClient

# webform_dev = ('http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9')

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', 'fcee8e3f11f36313e463ece51aab15242f71f3d552d565be')


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

figure = webform.get_webform('/metadata/figures/3175')

# print gcis.update_figure('nca3draft', figure)

print webform.get_list()

# for image in figure.images[2:]:
#     print image.identifier
#     image.filename = file_map[image.identifier]
#
#     print gcis.create_image(image, report_id='nca3draft', figure_id='temperature-change')
