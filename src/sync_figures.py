__author__ = 'abuddenberg'

from webform_client import WebformClient
from gcis_client import GcisClient
from os.path import exists
import json

# webform_dev = ('http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9')

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
# gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', '4cd31dc7173eb47b26f616fb07db607f25ab861552e81195')
gcis = GcisClient('http://data-stage.globalchange.gov', 'andrew.buddenberg@noaa.gov', 'ef427a895acf26d4f0b1f053ba7d922791b76f7852e7efee')

sync_metadata_tree = {
    #Reports
    'nca3draft': {
        #Chapter 2
        'our-changing-climate': [
            #(webform_url, gcis_id)
            # ('/metadata/figures/2506', 'observed-change-in-very-heavy-precipitation'),
            # ('/metadata/figures/2997', 'observed-change-in-very-heavy-precipitation-2'),
            # ('/metadata/figures/2677', 'observed-us-precipitation-change'),
            # ('/metadata/figures/3175', 'observed-us-temperature-change'),
            # ('/metadata/figures/3074', 'ten-indicators-of-a-warming-world'),
            # ('/metadata/figures/3170', 'global-temperature-and-carbon-dioxide'),
            # ('/metadata/figures/3293', 'observed-increase-in-frostfree-season-length'),
            # ('/metadata/figures/3294', 'projected-changes-in-frostfree-season-length'),
            # ('/metadata/figures/3305', 'variation-of-storm-frequency-and-intensity-during-the-cold-season-november--march') #incomplete
        ],
        #Chapter 6
        'agriculture': [
            # ('/metadata/figures/2872', 'drainage')
            # ('/metadata/figures/2691', 'variables-affecting-ag') #Needs images redone
        ],
        #Chapter 9
        '': [
            # ('/metadata/figures/2896', 'heavy-downpours-disease') #Needs images redone
        ],
        #Chapter 14
        'rural': [
            # ('/metadata/figures/3306', 'length-growing-season') #Needs images redone
        ],
        #Chapter 19
        'great-plains': [
            # ('/metadata/figures/2697', 'mean-annual-temp-and-precip') #Needs images redone

        ],
        #Chapter 25
        'coastal-zone': [
            # ('/metadata/figures/2543', 'coastal-ecosystem-services')
        ],
        #Climate Science Appendix
        'appendix-climate-science': [
            ('/metadata/figures/3147', 'ice-loss-from-greenland-and-antarctica')
        ]

    }
}

#These are artifacts from our collection efforts; largely duplicates
webform_skip_list = []


def main():
    # print_webform_list()
    aggregate_datasets()
    # sync(uploads=True)

    # f = webform.get_webform('/metadata/figures/3147').merge(gcis.get_figure('nca3draft', 'ice-loss-from-greenland-and-antarctica', chapter_id='appendix-climate-science'))


def aggregate_datasets():
    dataset_set = {}

    for item in webform.get_list():
        webform_url = item['url']

        f = webform.get_webform(webform_url)

        #aggregate datasets
        for image in f.images:
            for dataset in image.datasets:
                if dataset.identifier not in dataset_set:
                    dataset_set[dataset.identifier] = dataset
                else:
                    dataset_set[dataset.identifier].merge(dataset)

    for ds in dataset_set:
        print gcis.create_dataset(ds)



def print_webform_list():
    for item in webform.get_list():
        webform_url = item['url']
        f = webform.get_webform(webform_url)

        if 'ready_for_publication' in f.original and f.original['ready_for_publication'] == 'yes':
            print webform_url, '***Ready For Publication***'
            print f
        else:
            webform_skip_list.append(webform_url)


def sync(uploads=True):
    for report_id in sync_metadata_tree:
        for chapter_id in sync_metadata_tree[report_id]:
            for figure_ids in sync_metadata_tree[report_id][chapter_id]:
                webform_url, gcis_id = figure_ids

                if webform_url in webform_skip_list:
                    print 'Skipping: ' + webform_url
                    continue
                if uploads:
                    print 'Attempting to upload: ' + gcis_id
                    sync_images(webform_url, gcis_id)
                print 'Attempting to sync: ' + gcis_id
                sync_metadata(report_id, chapter_id, webform_url, gcis_id)
                print 'Success!'


def sync_metadata(report_id, chapter_id, webform_url, gcis_id):
    #Merge data from both systems into one object...
    figure_obj = webform.get_webform(webform_url).merge(
        gcis.get_figure(report_id, gcis_id, chapter_id=chapter_id)
    )
    #...then send it.
    gcis.update_figure(report_id, chapter_id, figure_obj)

def sync_images(webform_url, gcis_id):
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

        for dataset in image.datasets:
            gcis.associate_dataset_with_image(dataset.identifier, report_id, figure.identifier)


if __name__ == '__main__':
    main()