#!/usr/bin/python

import urllib
import urllib2
import json

url = 'http://data.gcis-test-front.joss.ucar.edu/report/nca3draft/figure'
#user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
values = {}
headers = {'Accept' : 'application/json' }
params = urllib.urlencode({'all':'1'})

url += '?' + params

data = urllib.urlencode(values)
req = urllib2.Request(url, None, headers)
response = urllib2.urlopen(req)
figure_listing = json.load(response)

for entry in figure_listing:
    print entry['identifier']

