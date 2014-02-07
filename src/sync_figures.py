__author__ = 'abuddenberg'

from webform_client import WebformClient
from gcis_client import GcisClient
from os.path import exists
import json

# webform_dev = ('http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9')

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', '4cd31dc7173eb47b26f616fb07db607f25ab861552e81195')
# stage = GcisClient('http://data-stage.globalchange.gov', 'andrew.buddenberg@noaa.gov', 'ef427a895acf26d4f0b1f053ba7d922791b76f7852e7efee')

sync_metadata_tree = {
    #Reports
    'nca3draft': {
        #Chapters
        'our-changing-climate': [
            #(webform_url, gcis_id)
            # ('/metadata/figures/2506', 'observed-change-in-very-heavy-precipitation'),
            # ('/metadata/figures/2997', 'observed-change-in-very-heavy-precipitation-2'),
            # ('/metadata/figures/2677', 'observed-us-precipitation-change'),
            # ('/metadata/figures/3175', 'observed-us-temperature-change'),
            # ('/metadata/figures/3074', 'ten-indicators-of-a-warming-world'),
            # ('/metadata/figures/3170', 'global-temperature-and-carbon-dioxide'),
            ('/metadata/figures/3293', 'observed-increase-in-frostfree-season-length'),
            # ('/metadata/figures/3294', 'projected-changes-in-frostfree-season-length'),
            # ('/metadata/figures/3305', 'variation-of-storm-frequency-and-intensity-during-the-cold-season-november--march') #incomplete

        ]
    }
}

#These are artifacts from our collection efforts; largely duplicates
webform_skip_list = []


def main():
    print_webform_list()
    # sync_images()
    # sync_metadata()




def print_webform_list():
    for item in webform.get_list():
        webform_url = item['url']
        print webform_url
        print webform.get_webform(webform_url)


def sync_metadata():
    for report in ['nca3draft']:
        for chapter in ['our-changing-climate']:
            for figure_ids in sync_metadata_tree[report][chapter]:
                webform_url, gcis_id = figure_ids

                #Merge data from both systems into one object...
                figure_obj = webform.get_webform(webform_url).merge(
                    gcis.get_figure(report, gcis_id, chapter_id=chapter)
                )
                #...then send it.
                gcis.update_figure(report, chapter, figure_obj)


def sync_images():
    for report in ['nca3draft']:
        for chapter in ['our-changing-climate']:
            for figure_ids in sync_metadata_tree[report][chapter]:
                webform_url, gcis_id = figure_ids

                figure = webform.get_webform(webform_url)
                #Now identifiers don't need to be matched
                figure.identifier = gcis_id

                webform.download_all_images(figure)
                upload_images_to_gcis(figure)


def upload_images_to_gcis(figure, report_id='nca3draft'):
    #Make sure we have all the images required for a COMPLETE update
    for image in figure.images:
        if not exists(image.local_path):
            raise Exception('Local file missing ' + image.local_path)
    for image in figure.images:
        for resp in gcis.create_image(image, report_id=report_id, figure_id=figure.identifier):
            print resp.status_code, resp.text


if __name__ == '__main__':
    main()