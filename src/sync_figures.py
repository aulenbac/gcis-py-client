__author__ = 'abuddenberg'

from webform_client import WebformClient
from gcis_client import GcisClient
from os.path import exists
import json
import pickle

# webform_dev = ('http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9')

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', 'd9fcfd947c1785ab1cd329a9920e05e5c5d3d7f35315f164')
# gcis = GcisClient('http://data-stage.globalchange.gov', 'andrew.buddenberg@noaa.gov', 'a6efcc7cf39c55e9329a8b027e0817e3354bada65310d192')

sync_metadata_tree = {
    #Reports
    'nca3': {
        #Chapter 2
        'our-changing-climate': [
            #(webform_url, gcis_id)
            ('/metadata/figures/2506', 'observed-change-in-very-heavy-precipitation'),
            ('/metadata/figures/2997', 'observed-change-in-very-heavy-precipitation-2'),
            ('/metadata/figures/2677', 'observed-us-precipitation-change'),
            ('/metadata/figures/3175', 'observed-us-temperature-change'),
            ('/metadata/figures/3074', 'ten-indicators-of-a-warming-world'),
            ('/metadata/figures/3170', 'global-temperature-and-carbon-dioxide'),
            ('/metadata/figures/3293', 'observed-increase-in-frostfree-season-length'),
            ('/metadata/figures/3294', 'projected-changes-in-frostfree-season-length'),
            # ('/metadata/figures/3305', 'variation-of-storm-frequency-and-intensity-during-the-cold-season-november--march') #incomplete
        ],
        #Chapter 4
        'energy-supply-and-use': [
            ('/metadata/figures/3292', 'cooling-degree-days')
        ],
        #Chapter 6
        'agriculture': [
            ('/metadata/figures/2872', 'drainage'),
            ('/metadata/figures/2691', 'variables-affecting-ag') #Needs images redone
        ],
        #Chapter 9
        'human-health': [
            ('/metadata/figures/2896', 'heavy-downpours-disease') #Needs images redone
        ],
        #Chapter 14
        'rural': [
            ('/metadata/figures/3306', 'length-growing-season') #Needs images redone
        ],
        #Chapter 18
        '': [
            ('/metadata/figures/2992', 'projected-midcentury-temperature-changes-in-the-midwest')
        ],
        #Chapter 19
        'great-plains': [
            ('/metadata/figures/2697', 'mean-annual-temp-and-precip') #Needs images redone

        ],
        #Chapter 25
        'coastal-zone': [
            ('/metadata/figures/2543', 'coastal-ecosystem-services')
        ],
        #Climate Science Appendix
        'appendix-climate-science': [
            # ('/metadata/figures/3147', 'ice-loss-from-greenland-and-antarctica')
        ]

    }
}


def main():
    sync(uploads=False)


def sync(uploads=True):
    for report_id in sync_metadata_tree:
        for chapter_id in sync_metadata_tree[report_id]:
            for figure_ids in sync_metadata_tree[report_id][chapter_id]:
                webform_url, gcis_id = figure_ids

                if uploads:
                    print 'Attempting to upload: ' + gcis_id
                    upload_images_to_gcis(webform_url, gcis_id, report_id)
                print 'Attempting to sync: ' + gcis_id
                sync_figure_metadata(report_id, chapter_id, webform_url, gcis_id)
                print 'Success!'


def sync_figure_metadata(report_id, chapter_id, webform_url, gcis_id):
    #Merge data from both systems into one object...
    figure_obj = webform.get_webform(webform_url).merge(
        gcis.get_figure(report_id, gcis_id, chapter_id=chapter_id)
    )
    #...then send it.
    gcis.update_figure(report_id, chapter_id, figure_obj)


#This function is for adding images to existing figures
def upload_images_to_gcis(webform_url, gcis_id, report_id):
    figure = webform.get_webform(webform_url, download_images=True)
    #Now identifiers don't need to be matched
    figure.identifier = gcis_id

    #Make sure we have all the images required for a COMPLETE update
    for image in figure.images:
        if not exists(image.local_path):
            raise Exception('Local file missing ' + image.local_path)
    for image in figure.images:
        if not gcis.image_exists(image.identifier):
            gcis.create_image(image, report_id=report_id, figure_id=figure.identifier)


def sync_dataset_metadata(datasets):
    for ds in datasets:
        if gcis.dataset_exists(ds.identifier):
            print 'Updating: {ds}'.format(ds=ds)
            gcis.update_dataset(ds)
        else:
            print 'Creating: {ds}'.format(ds=ds)
            gcis.create_dataset(ds)


def aggregate_webform_datasets():
    dataset_map = {}

    for item in webform.get_list():
        webform_url = item['url']

        f = webform.get_webform(webform_url)

        #aggregate datasets
        for image in f.images:
            for dataset in image.datasets:
                if dataset.identifier not in dataset_map:
                    dataset_map[dataset.identifier] = dataset
                else:
                    dataset_map[dataset.identifier].merge(dataset)

    return dataset_map.values()


if __name__ == '__main__':
    main()