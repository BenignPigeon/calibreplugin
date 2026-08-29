#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

import json
import urllib.error
import urllib.request

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)
PAGE_SIZE = 100


class AbsClient(object):
    '''
    HTTP client for the Audiobookshelf API.
    All requests include a browser User-Agent to pass Cloudflare.
    '''

    def __init__(self, server_url):
        self.server_url = (server_url or '').rstrip('/')
        self.token = None

    def _headers(self, json_content=False):
        headers = {'User-Agent': USER_AGENT}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        if json_content:
            headers['Content-Type'] = 'application/json'
        return headers

    def _get_json(self, url):
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

    def login(self, username, password):
        login_url = f'{self.server_url}/login'
        login_data = json.dumps({
            'username': username,
            'password': password
        }).encode('utf-8')

        req = urllib.request.Request(
            login_url,
            data=login_data,
            headers=self._headers(json_content=True)
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                self.token = result.get('user', {}).get('token')
                if not self.token:
                    raise Exception('No token received from server')
                return self.token
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            raise Exception(f'Authentication failed: {e.code} - {error_body}')

    def get_libraries(self):
        data = self._get_json(f'{self.server_url}/api/libraries')
        return data.get('libraries', [])

    def get_library_items(self, library_id):
        '''
        Fetch all items in a library, following pagination.
        '''
        items = []
        page = 0
        while True:
            url = (
                f'{self.server_url}/api/libraries/{library_id}/items'
                f'?limit={PAGE_SIZE}&page={page}'
            )
            data = self._get_json(url)
            results = data.get('results', [])
            items.extend(results)

            total = data.get('total')
            if not results:
                break
            if total is not None and len(items) >= total:
                break
            if len(results) < PAGE_SIZE:
                break
            page += 1
        return items

    def get_item(self, item_id):
        return self._get_json(f'{self.server_url}/api/items/{item_id}')

    def download_to_path(self, item_id, ino, dest_path):
        if ino:
            url = f'{self.server_url}/api/items/{item_id}/file/{ino}/download'
        else:
            url = f'{self.server_url}/api/items/{item_id}/download'

        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req) as dl_resp, open(dest_path, 'wb') as out_file:
            while True:
                chunk = dl_resp.read(16384)
                if not chunk:
                    break
                out_file.write(chunk)


def normalize_item(item, library_name=None):
    '''
    Flatten an ABS library-item payload for the book picker UI.
    '''
    media = item.get('media') or {}
    metadata = media.get('metadata') or {}
    title = metadata.get('title') or item.get('title') or 'Unknown'
    author = (
        metadata.get('authorName')
        or metadata.get('author')
        or ''
    )
    return {
        'id': item.get('id'),
        'title': title,
        'author': author,
        'library_name': library_name or '',
    }
