#!/usr/bin/python

import urllib
import urllib2
import json
from domain import Figure

from pickle import dump

# base_url = 'http://data.gcis-test-front.joss.ucar.edu/report/nca3draft'
base_url = 'http://data-stage.globalchange.gov/report/nca3'
#user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic YW5kcmV3LmJ1ZGRlbmJlcmdAbm9hYS5nb3Y6MjFjMjM2Y2YxYmZmMmRjMmMyOTNlZjljMWVjNTY1NWFhZWIyYjQ0ZDUyMzc3OGE1'
}


def main():
    # drupal_id, create_dt = get_webform('1320')
    # my_thing, post_url = get_figure(drupal_id)
    #
    # my_thing['create_dt'] = create_dt
   

    # req = urllib2.Request(post_url, json.dumps(my_thing), headers)
    # response = urllib2.urlopen(req)

    # print response.read()
    # print [key for key in get_figure_listing('our-changing-climate')['temperature-change'].keys()]

   # for figure in get_figure_listing('our-changing-climate'):
   #     print figure.

    out = open('../chapter2_listing.pk1', 'w')
    dump(get_figure_listing('our-changing-climate'), out)
    out.close()



def do_update():
    print ''
    update_url = '{base_url}/form/update'.format(base_url=base_url)


def get_figure(identifier):
    query = '{url}{id}.json'.format(url=base_url, id=identifier)
    resp = json.load(urllib2.urlopen(query))
    del(resp['images'])
    del(resp['chapter'])
    del(resp['parents'])
    return resp, query


#Full listing
def get_figure_listing(chapter=None):
    #Enable filtering by chapter
    chapter_filter = '/chapter/' + chapter if chapter else ''
    url = '{base}{chap}/figure?{p}'.format(base=base_url, chap=chapter_filter, p=urllib.urlencode({'all': '1'}))
    req = urllib2.Request(url, None, headers)

    return [Figure(**figure) for figure in json.load(urllib2.urlopen(req))]


#Numerical identifiers
# def print_chapter_figure_list():
#     for entry in figure_listing:
#         chapter_num = ''
#
#         if 'chapter' in entry and 'number' in entry['chapter'] and entry['ordinal']:
#             chapter_num = entry['chapter']['number']
#             ordinal = entry['ordinal']
#
#             print '{0}.{1} '.format(chapter_num, ordinal), entry['identifier']

if __name__ == "__main__":
    main()
