__author__ = 'abuddenberg'
from os.path import exists


#This function is for adding images to existing figures
def move_images_to_gcis(webform_client, gcis_client, webform_url, gcis_id, report_id, subset_images=None):
    figure = webform_client.get_webform(webform_url, download_images=True)
    #Now identifiers don't need to be matched
    figure.identifier = gcis_id

    #If a subset of identifiers has been provided, only process those
    if subset_images:
        images_to_process = [image for image in figure.images if image.identifier in subset_images]
    else:
        images_to_process = figure.images

    for image in images_to_process:
        if not exists(image.local_path):
            raise Exception('Local file missing ' + image.local_path)

        if not gcis_client.image_exists(image.identifier):
            print 'Creating image: {img}'.format(img=image.identifier)
            gcis_client.create_image(image, report_id=report_id, figure_id=figure.identifier)


def sync_dataset_metadata(gcis_client, datasets, skip=[]):
    for ds in [ds for ds in datasets if ds.identifier not in skip]:
        gcis_client.create_or_update_dataset(ds)
        # gcis_client.create_or_update_activity(ds.activity)


def realize_contributors(gcis_client, contributors):
    for cont in contributors:
        person = cont.person
        org = cont.organization

        #Hack for F. Chapin
        if '.' in person.first_name:
            person.first_name = ''

        name_matches = gcis_client.lookup_person(person.first_name + ' ' + person.last_name)
        if len(name_matches) == 1:
            person.id = name_matches[0][0]
        elif len(name_matches) == 0:
            print '\t', 'No ID found for ' + person.first_name + ' ' + person.last_name
        else:
            print '\t', 'Ambiguous results for ' + person.first_name + ' ' + person.last_name
            print '\t\t', name_matches

        if org.identifier in (None, '') and org.name not in (None, ''):

            print 'No ID found for ' + org.name

    #Check if we missed any organizations in our hardcoding...
    if not all(map(lambda c: c.organization.identifier is not None, contributors)):
        print contributors


def realize_parents(gcis_client, parents):
    for parent in parents:
        # print parent.publication_type_identifier, parent.label
        if parent.url:
            print '\t', ' '.join(('Using hint for', parent.publication_type_identifier, parent.label))
            continue

        parent_matches = gcis_client.lookup_publication(parent.publication_type_identifier, parent.label)

        if len(parent_matches) == 1:
            parent.url = '/{type}/{id}'.format(type=parent.publication_type_identifier, id=parent_matches[0][0])
        elif len(parent_matches) == 0:
            print '\t', ' '.join(('No ID found for', parent.publication_type_identifier, parent.label))
        else:
            print '\t', ' '.join(('Ambiguous results for', parent.publication_type_identifier, parent.label))
            print '\t\t', parent_matches