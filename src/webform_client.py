#!/usr/bin/python

import urllib
import urllib2
import json

def get_webforms(nid):
    url = 'http://dev.nemac.org/asides10/metadata/figures/all?token=A2PNYxRuG9'
    
    figure_listing = json.load(urllib2.urlopen(url))
    
    results = []
    
    #for figure_id in figure_listing:
    #    if 'what_is_the_figure_id' not in figure_listing[figure_id]['figure'][0]:
    #        continue
    #    else:
    #        print figure_id, figure_listing[figure_id]['figure'][0]['what_is_the_figure_id']
    
    return figure_listing[nid]['figure'][0]['what_is_the_figure_id'], figure_listing[nid]['figure'][0]['when_was_this_figure_created']

    
