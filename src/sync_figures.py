__author__ = 'abuddenberg'

from webform_client import WebformClient
from gcis_client import GcisClient
import json
from subprocess import call

# webform_dev = ('http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9')

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', '4cd31dc7173eb47b26f616fb07db607f25ab861552e81195')

# stage = GcisClient('http://data-stage.globalchange.gov', 'andrew.buddenberg@noaa.gov', 'ef427a895acf26d4f0b1f053ba7d922791b76f7852e7efee')





# print gcis.update_figure('nca3draft', 'our-changing-climate', figure, skip_images=True)

# for item in webform.get_list():
#     webform_url = item['url']
#     print webform_url
#     print webform.get_webform(webform_url)


heavy_precip = webform.get_webform('/metadata/figures/2506').merge(
    gcis.get_figure('nca3draft', 'observed-change-in-very-heavy-precipitation', chapter_id='our-changing-climate')
)

# for i in heavy_precip.images[1:]:
#     gcis.create_image(i, report_id='nca3draft', figure_id='observed-change-in-very-heavy-precipitation')

gcis.update_figure('nca3draft', 'our-changing-climate', heavy_precip)

# heavy_precip = webform.get_webform('/metadata/figures/2506')
#
# for i in heavy_precip.images:
#     # print i.as_json()
#     # print i.filepath, webform.image_exists(i.filepath)
#     image = webform.download_image(i.filepath)
#     call(['/opt/local/bin/convert', image, image.replace('.eps', '.png')])



# print json.dumps(webform.get_webform('/metadata/figures/3294').original, indent=4)

# for image in figure.images[1:]:
#     print image.identifier
#     image.filename = file_map[image.identifier]
#
#     print gcis.associate_image_with_figure(image.identifier, 'nca3draft', figure.identifier)

    # print gcis.create_image(image, report_id='nca3draft', figure_id='temperature-change')


