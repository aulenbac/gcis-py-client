#!/usr/bin/python

import urllib
import urllib2
import json
from webform_client import get_webforms

base_url = 'http://data.gcis-test-front.joss.ucar.edu/report/nca3draft'
#user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
values = {}
headers = {'Accept' : 'application/json' }
params = urllib.urlencode({'all':'1'})

url = base_url + '?' + params

data = urllib.urlencode(values)
req = urllib2.Request(url, None, headers)
response = urllib2.urlopen(req)
figure_listing = json.load(response)

def main():
    drupal_id, create_dt = get_webforms('1320')
    my_thing, post_url = get_figure(drupal_id)

    my_thing['create_dt'] = create_dt
   
    headers = {
            'Accept' : 'application/json',
            'Authorization': 'Basic YW5kcmV3LmJ1ZGRlbmJlcmdAbm9hYS5nb3Y6MjFjMjM2Y2YxYmZmMmRjMmMyOTNlZjljMWVjNTY1NWFhZWIyYjQ0ZDUyMzc3OGE1'            
            }
    req = urllib2.Request(post_url, json.dumps(my_thing), headers)
    response = urllib2.urlopen(req)

    print response.read()



#    for key in get_full_listing():
#        print key

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
def get_full_listing():
    full_listing = {}
    for entry in figure_listing:
        full_listing[entry['identifier']] = entry
    return full_listing 

#Numerical identifiers
def print_chapter_figure_list():
    for entry in figure_listing:
        chapter_num = ''
    
        if 'chapter' in entry and 'number' in entry['chapter'] and entry['ordinal']:
            chapter_num = entry['chapter']['number']
            ordinal = entry['ordinal'] 
    
            print '{0}.{1} '.format(chapter_num, ordinal), entry['identifier']
    
main()
