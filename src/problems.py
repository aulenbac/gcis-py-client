__author__ = 'abuddenberg'

import pickle
from gcis_client import GcisClient
from webform_client import WebformClient

webform = WebformClient('http://resources.assessment.globalchange.gov', 'mgTD63FAjG')

gcis_url = 'http://data.gcis-dev-front.joss.ucar.edu'
gcis = GcisClient(gcis_url, 'andrew.buddenberg@noaa.gov', 'd9fcfd947c1785ab1cd329a9920e05e5c5d3d7f35315f164')


def main():
    hitlist_file = '../hitlist.pk1'

    # create_problem_list('nca3', hitlist_file)
    print_problem_list(hitlist_file)
    solve_problems(hitlist_file)


def solve_problems(path):
    problems = load_problem_list(path)

    for webform in problems:
        if problems[webform]['figure_id_not_found']:
            print 'Unable to resolve figure identifier: ' + problems[webform]['figure_id_not_found']
            continue
        


def create_problem_list(report_id, path):
    pickle.dump(sort_webform_list(report_id), open(path, 'wb'))


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
        all_forms.append(f)

        #Check the ready for publication flag
        if 'ready_for_publication' in f.original and f.original['ready_for_publication'] == 'yes':
            #Check if the figure exists in GCIS
            if not gcis.figure_exists(report_id, f.identifier):
                problems.setdefault(webform_url, {}).setdefault('figure_id_not_found', []).append((f.identifier, f.figure_num, f.title))
            #Check if each image exists in GCIS
            for image in f.images:
                if not gcis.image_exists(image.identifier):
                    problems.setdefault(webform_url, {}).setdefault('image_id_not_found', []).append(image.identifier)

                #Check if each image's dataset exists in GCIS
                for dataset in image.datasets:
                    if not gcis.dataset_exists(dataset.identifier):
                        problems.setdefault(webform_url, {}).setdefault('dataset_id_not_found', []).append(dataset.identifier)

                #Check if the filename fields are filled out and correct for what's been uploaded
                if image.remote_path in (None, '') or not webform.remote_image_exists(image.remote_path):
                    problems.setdefault(webform_url, {}).setdefault('missing_image_files', []).append(image.identifier)

            #Check for broken image associations
            if not gcis.has_all_associated_images(report_id, f.identifier, f.images):
                problems.setdefault(webform_url, {}).setdefault('broken_image_assoc', []).append(image.identifier)

            if webform_url not in problems:
                ready.append((webform_url, f.identifier))

    return all_forms, ready, problems



if __name__ == '__main__':
    main()