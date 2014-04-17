__author__ = 'abuddenberg'

import requests


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

        self.drupal_user = username
        self.drupal_pass = password

    def do_login(self):
        url = '{b}/user'.format(b=self.base_url)
        resp = self.s.post(
            url,
            data={
                'name': self.drupal_user,
                'pass': self.drupal_pass,
                'form_id': 'user_login',
                'op': 'Log in'
            },
            allow_redirects=False
        )

        return resp

    @http_resp
    def get_all_captions(self):
        self.do_login()
        url = '{b}/gcis/figure-table-captions'.format(b=self.base_url)

        resp = self.s.get(url, verify=False)
        return resp
