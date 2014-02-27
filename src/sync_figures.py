__author__ = 'abuddenberg'

from webform_client import WebformClient
from gcis_client import GcisClient
from os.path import exists
import json
import pickle

# webform_dev = ('http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9')

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', '4cd31dc7173eb47b26f616fb07db607f25ab861552e81195')
# gcis = GcisClient('http://data-stage.globalchange.gov', 'andrew.buddenberg@noaa.gov', 'ef427a895acf26d4f0b1f053ba7d922791b76f7852e7efee')

global_report_name = 'nca3draft'

sync_metadata_tree = {
    #Reports
    global_report_name: {
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
        #Chapter 4
        'energy-supply-and-use': [
            # ('/metadata/figures/3292', 'cooling-degree-days')
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
            # ('/metadata/figures/3147', 'ice-loss-from-greenland-and-antarctica')
        ]

    }
}

#These are artifacts from our collection efforts; largely duplicates
# webform_skip_list = []


def main():
    pickle.dump(sort_webform_list(), open('../hitlist.pk1', 'wb'))
    all_forms, ready, problems = pickle.load(open('../hitlist.pk1', 'r'))

    print ready

    # for ds in aggregate_datasets():
    #     gcis.update_dataset(ds)
    # sync(uploads=False)

    # f = webform.get_webform('/metadata/figures/3147').merge(gcis.get_figure('nca3draft', 'ice-loss-from-greenland-and-antarctica', chapter_id='appendix-climate-science'))


def sort_webform_list():
    all_forms = []
    ready = []
    problems = {}

    for item in webform.get_list():
        webform_url = item['url']
        f = webform.get_webform(webform_url)
        all_forms.append(f)

        #Check the ready for publication flag
        if 'ready_for_publication' in f.original and f.original['ready_for_publication'] == 'yes':
            #Check if the figure exists in GCIS
            if not gcis.figure_exists(global_report_name, f.identifier):
                problems.setdefault(webform_url, {}).setdefault('figure_id', []).append(f.identifier)
            #Check if each image exists in GCIS
            for image in f.images:
                if not gcis.image_exists(image.identifier):
                    problems.setdefault(webform_url, {}).setdefault('image_id', []).append(image.identifier)

                #Check if each image's dataset exists in GCIS
                for dataset in image.datasets:
                    if not gcis.dataset_exists(dataset.identifier):
                        problems.setdefault(webform_url, {}).setdefault('dataset_id', []).append(dataset.identifier)

                #Check if the filename fields are filled out and correct for what's been uploaded
                if image.remote_path in (None, '') or not webform.remote_image_exists(image.remote_path):
                    problems.setdefault(webform_url, {}).setdefault('missing_image_files', []).append(image.identifier)

            if webform_url not in problems:
                ready.append((webform_url, f.identifier))

    return all_forms, ready, problems


def sync(uploads=True):
    for report_id in sync_metadata_tree:
        for chapter_id in sync_metadata_tree[report_id]:
            for figure_ids in sync_metadata_tree[report_id][chapter_id]:
                webform_url, gcis_id = figure_ids

                if uploads:
                    print 'Attempting to upload: ' + gcis_id
                    upload_images_to_gcis(webform_url, gcis_id, report_id)
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


#This function is for adding images to existing figures
def upload_images_to_gcis(webform_url, gcis_id, report_id):
    figure = webform.get_webform(webform_url)
    #Now identifiers don't need to be matched
    figure.identifier = gcis_id

    webform.download_all_images(figure)

    #Make sure we have all the images required for a COMPLETE update
    for image in figure.images:
        if not exists(image.local_path):
            raise Exception('Local file missing ' + image.local_path)
    for image in figure.images:
        for resp in gcis.create_image(image, report_id=report_id, figure_id=figure.identifier):
            print resp.status_code, resp.text

        # for dataset in image.datasets:
        #     gcis.associate_dataset_with_image(dataset.identifier, report_id, image.identifier)


def aggregate_datasets():
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