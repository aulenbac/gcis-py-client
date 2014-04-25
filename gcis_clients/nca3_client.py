__author__ = 'abuddenberg'

import requests
import pickle
import json
from bs4 import BeautifulSoup

def http_resp(fn):
    def wrapped(*args, **kwargs):
        resp = fn(*args, **kwargs)
        if resp.status_code == 200:
            return resp
        else:
            raise Exception('Status: {code} \n{txt}'.format(code=resp.status_code, txt=resp.text))
    return wrapped


class Nca3Client(object):
    def __init__(self, url, username, password, http_basic_user=None, http_basic_pass=None):
        self.base_url = url
        self.s = requests.Session()
        self.s.auth = (http_basic_user, http_basic_pass)
        # self.s.headers = {'content-type': 'application/json'}

        self.drupal_user = username
        self.drupal_pass = password
        self.cookie_jar = '/tmp/cookies'
        try:
            self.s.cookies = pickle.load(open(self.cookie_jar, 'r'))
        except Exception, e:
            pass

    def do_login(self):
        url = '{b}/user'.format(b=self.base_url)
        form = BeautifulSoup(self.s.get(url).text).find('form', id='user-login')
        form_build_id = form.find_all('input', attrs={'name': 'form_build_id'})

        resp = self.s.post(
            url,
            data={
                'name': self.drupal_user,
                'pass': self.drupal_pass,
                'form_id': 'user_login',
                'form_build_id': form_build_id,
                'op': 'Log in'
            },
            allow_redirects=False
        )

        pickle.dump(self.s.cookies, open(self.cookie_jar, 'wb'))

        return resp

    @http_resp
    def get_all_captions(self):
        url = '{b}/gcis/figure-table-captions'.format(b=self.base_url)

        resp = self.s.get(url, verify=False, headers={'content-type': 'application/json'}, cookies=self.s.cookies)
        return resp

    def get_figure(self, nid):
        url = '{b}/gcis/node/{nid}'.format(b=self.base_url, nid=nid)

        return self.s.get(url, verify=False, headers={'content-type': 'application/json'}, cookies=self.s.cookies).json()

    def update_figure(self, nid, figure_frag):
        url = '{b}/gcis/node/{nid}'.format(b=self.base_url, nid=nid)
        token_url = '{b}/services/session/token'.format(b=self.base_url)
        token = self.s.get(token_url, verify=False, cookies=self.s.cookies).text

        return self.s.put(url, data=json.dumps(figure_frag), verify=False, cookies=self.s.cookies, headers={'X-CSRF-Token': token, 'content-type': 'application/json'})


