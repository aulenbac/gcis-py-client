__author__ = 'abuddenberg'

import pickle
from gcis_client import GcisClient
from webform_client import WebformClient
from sync_figures import upload_images_to_gcis

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', 'd9fcfd947c1785ab1cd329a9920e05e5c5d3d7f35315f164')
# gcis = GcisClient('http://data-stage.globalchange.gov', 'andrew.buddenberg@noaa.gov', 'a6efcc7cf39c55e9329a8b027e0817e3354bada65310d192')

def main():
    hitlist_file = '../hitlist.pk1'

    create_problem_list('nca3', hitlist_file)
    print_problem_list(hitlist_file)
    # solve_problems(hitlist_file, 'nca3')

    #WTF:
    #requests.exceptions.ConnectionError: HTTPConnectionPool(host='data.gcis-dev-front.joss.ucar.edu', port=80): Max retries exceeded with url: /report/nca3/figure/rel/observed-change-in-very-heavy-precipitation (Caused by <class 'httplib.BadStatusLine'>: '')


def solve_problems(path, report_id):
    problems = load_problem_list(path)

    for webform in problems:
        webform_id, fig_num, gcis_id = webform

        #Without a valid GCIS figure_id, nothing else can happen
        if 'figure_id_not_found' in problems[webform]:
            print 'Unable to resolve figure identifier: {fig}'.format(fig=problems[webform]['figure_id_not_found'])
            continue

        img_id_missing = set(problems[webform]['image_id_not_found']) if 'image_id_not_found' in problems[webform] else set()
        img_file_missing = set(problems[webform]['missing_image_files']) if 'missing_image_files' in problems[webform] else set()
        creates = img_id_missing - img_file_missing

        img_assoc_broken = set(problems[webform]['broken_image_assoc']) if 'broken_image_assoc' in problems[webform] else set()
        assocs = img_assoc_broken - creates

        if len(creates) > 0:
            upload_images_to_gcis(webform_id, gcis_id, report_id, subset_images=creates)

        for image_id in assocs:
            print 'Associating image: {i} with figure: {f}'.format(i=image_id, f=gcis_id)
            print gcis.associate_image_with_figure(image_id, report_id, gcis_id)


def create_problem_list(report_id, path):
    with open(path, 'wb') as problem_file:
        pickle.dump(sort_webform_list(report_id), problem_file)


def load_problem_list(path):
    all_forms, ready, problems = pickle.load(open(path, 'r'))
    return problems


def load_ready_list(path):
    all_forms, ready, problems = pickle.load(open(path, 'r'))
    return ready


def print_problem_list(path):
    problems = load_problem_list(path)
    for webform in problems:
        print webform
        for problem_type in problems[webform]:
            print '\t', problem_type, problems[webform][problem_type]


def sort_webform_list(report_id):
    all_forms = []
    ready = []
    problems = {}

    for item in webform.get_list():
        webform_url = item['url']
        f = webform.get_webform(webform_url)
        key = (webform_url, f.figure_num, f.identifier)

        all_forms.append(key)

        #Check the ready for publication flag
        if 'ready_for_publication' in f.original and f.original['ready_for_publication'] == 'yes':
            #Check if the figure exists in GCIS
            if not gcis.figure_exists(report_id, f.identifier):
                problems.setdefault(key, {}).setdefault('figure_id_not_found', []).append(
                    (f.identifier, f.figure_num, f.title))
            #Check if each image exists in GCIS
            for image in f.images:
                if not gcis.image_exists(image.identifier):
                    problems.setdefault(key, {}).setdefault('image_id_not_found', []).append(
                        image.identifier)

                #Check if each image's dataset exists in GCIS
                for dataset in image.datasets:
                    if not gcis.dataset_exists(dataset.identifier):
                        problems.setdefault(key, {}).setdefault('dataset_id_not_found',
                            []).append(dataset.identifier)

                #Check if the filename fields are filled out and correct for what's been uploaded
                if image.remote_path in (None, '') or not webform.remote_image_exists(image.remote_path):
                    problems.setdefault(key, {}).setdefault('missing_image_files', []).append(
                        image.identifier)

            #Check for broken image associations
            has_all_images, image_deltas = gcis.has_all_associated_images(report_id, f.identifier,
                                                                               [i.identifier for i in f.images])
            if not has_all_images and len(image_deltas) > 0:
                problems.setdefault(key, {}).setdefault('broken_image_assoc', []).extend(
                    image_deltas)

            if key not in problems:
                ready.append(key)

    return all_forms, ready, problems


if __name__ == '__main__':
    main()