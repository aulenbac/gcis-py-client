__author__ = 'abuddenberg'
from gcis_clients import Nca3Client, GcisClient, gcis_stage_auth
import pickle
import json
import requests

nca3_url = 'https://nca3.cicsnc.org'
nca3 = Nca3Client(nca3_url, 'andrew.buddenberg', 'Nz9O^00I', http_basic_user='nca3', http_basic_pass='avl-TSU')

gcis_url = 'https://data-stage.globalchange.gov'
gcis = GcisClient(gcis_url, *gcis_stage_auth)


def main():
    pass




def get_gcis_chapters():
    gcis_all_chapters = requests.get('{b}/report/nca3/chapter.json'.format(b=gcis_url), params={'all': 1}, verify=False).json()
    chapter_map = {c['identifier']: c for c in gcis_all_chapters}

    with open('chapter_map.pk1', 'wb') as fout:
        pickle.dump(chapter_map, fout)

    return pickle.load(open('chapter_map.pk1'))


def get_all_gcis_figures():
    gcis_all_figs = {}
    for f in gcis.get_figure_listing('nca3'):
        chapter_num = get_gcis_chapters()[f.chapter_identifier]['number']
        # print f.chapter_identifier, chapter_num, f.ordinal

        f.figure_num = '{0}.{1}'.format(chapter_num, f.ordinal)
        gcis_all_figs[f.figure_num] = f

    with open('fig_map.pk1', 'wb') as fout:
        pickle.dump(gcis_all_figs, fout)

    gcis_all_figs = pickle.load(open('fig_map.pk1'))
    return gcis_all_figs


def populate_uris_in_drupal():
    gcis_all_figs = get_all_gcis_figures()

    for list_item in sorted(nca3.get_all_captions().json(), key=lambda f: f['Ordinal']):
        nid = list_item['nid']
        ordinal = list_item['Ordinal']
        graphic_type = list_item['Graphic Type']

        if ordinal and ordinal in gcis_all_figs and graphic_type == 'Figure':
            print 'Found: ', graphic_type, ordinal, gcis_all_figs[ordinal].uri
            # nca3_fig = nca3.get_figure(nid)
            # print nca3_fig

            uri_frag = {
                'und': [
                    {
                        'value': gcis_all_figs[ordinal].uri[1:],
                        'format': None,
                        'safe_value': gcis_all_figs[ordinal].uri[1:]
                    }
                ]
            }
            # nca3_fig['field_metadata_uri'] = uri_frag

            resp = nca3.update_figure(nid, {'field_metadata_uri': uri_frag})
            print resp.status_code, resp.text
            print ''

        else:
            print '***NO URI FOUND***', graphic_type, ordinal

main()