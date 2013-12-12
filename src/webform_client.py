#!/usr/bin/python

import urllib
import urllib2
import json
import re

prod = {'base': 'http://resources.assessment.globalchange.gov', 'token': 'mgTD63FAjG'}
dev_base = 'http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9'


def sanitized(pattern):
    def dec(fn):
        def wrapped(*args, **kwargs):
            if re.match(pattern, urllib.quote(args[0])):
                return fn(*args, **kwargs)
            else:
                print 'Shitlisted: ', args[0]
        return wrapped
    return dec


def get_list():
    url = '{base}/metadata/list?token={token}'.format(**prod)
    figure = json.load(urllib2.urlopen(url))

    return figure


def get_all_webforms():
    pass


@sanitized('^/metadata/figures/\d+$')
def get_webform(url):
    prod['url'] = url
    full_url = '{base}{url}?token={token}'.format(**prod)
    figure = json.load(urllib2.urlopen(full_url))

    return figure


for listing in get_list():
    print listing

url = '/metadata/figures/2681'

print json.dumps(get_webform(url), indent=4, sort_keys=True)

