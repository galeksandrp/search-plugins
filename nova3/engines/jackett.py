#VERSION: 4.1
# AUTHORS: Diego de las Heras (ngosang@hotmail.es)
# CONTRIBUTORS: ukharley
#               hannsen (github.com/hannsen)
#               Alexander Georgievskiy <galeksandrp@gmail.com>

import json
import os
import xml.etree.ElementTree
if True:
    import hashlib
from urllib.parse import urlencode, unquote
from urllib import request as urllib_request
from http.cookiejar import CookieJar
from multiprocessing.dummy import Pool
from threading import Lock

from novaprinter import prettyPrinter
from helpers import download_file


###############################################################################
# load configuration from file
CONFIG_FILE = 'jackett.json'
if 'CONFIG_FILE' in os.environ:
    CONFIG_FILE = os.environ['CONFIG_FILE']
CONFIG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), CONFIG_FILE)
CONFIG_DATA = {
    'api_key': 'YOUR_API_KEY_HERE',  # jackett / prowlarr api
    'url': 'http://127.0.0.1:' + ('9696' if CONFIG_FILE  == 'prowlarr.json' else '9117'),  # jackett / prowlarr url
    'tracker_first': False,          # (False/True) add tracker name to beginning of search result
    'thread_count': 20,              # number of threads to use for http requests
}
PRINTER_THREAD_LOCK = Lock()
if True:
    BYTES_IN_GB = 1024 * 1024 * 1024


def load_configuration():
    global CONFIG_PATH, CONFIG_DATA
    try:
        # try to load user data from file
        with open(CONFIG_PATH) as f:
            CONFIG_DATA = json.load(f)
    except ValueError:
        # if file exists, but it's malformed we load add a flag
        CONFIG_DATA['malformed'] = True
    except Exception:
        # if file doesn't exist, we create it
        save_configuration()

    # do some checks
    if any(item not in CONFIG_DATA for item in ['api_key', 'tracker_first', 'url']):
        CONFIG_DATA['malformed'] = True

    # add missing keys
    if 'thread_count' not in CONFIG_DATA:
        CONFIG_DATA['thread_count'] = 20
        save_configuration()


def save_configuration():
    global CONFIG_PATH, CONFIG_DATA
    with open(CONFIG_PATH, 'w') as f:
        f.write(json.dumps(CONFIG_DATA, indent=4, sort_keys=True))


load_configuration()
###############################################################################


class jackett(object):
    name = 'Jackett'
    url = CONFIG_DATA['url'] if CONFIG_DATA['url'][-1] != '/' else CONFIG_DATA['url'][:-1]
    api_key = CONFIG_DATA['api_key']
    thread_count = CONFIG_DATA['thread_count']
    supported_categories = {
        'all': None,
        'anime': ['5070'],
        'books': ['8000'],
        'games': ['1000', '4000'],
        'movies': ['2000'],
        'music': ['3000'],
        'software': ['4000'],
        'tv': ['5000'],
    }
    if True:
        utilsIndexers = {}
        utilsLines = 1
        utilsIndexersTotal = 0

    def download_torrent(self, download_url):
        # fix for some indexers with magnet link inside .torrent file
        if download_url.startswith('magnet:?'):
            print(download_url + " " + download_url)
        response = self.get_response(download_url)
        if response is not None and response.startswith('magnet:?'):
            print(response + " " + download_url)
        else:
            print(download_file(download_url))

    def search(self, what, cat='all'):
        what = unquote(what)
        category = self.supported_categories[cat.lower()]

        # check for malformed configuration
        if 'malformed' in CONFIG_DATA:
            self.handle_error("malformed configuration file", what)
            return

        # check api_key
        if self.api_key == "YOUR_API_KEY_HERE":
            self.handle_error("api key error", what)
            return

        # search in Jackett / Prowlarr API
        if self.thread_count > 1:
            args = []
            indexers = self.get_jackett_indexers(what)
            for indexer in indexers:
                args.append((what, category, indexer))
            with Pool(min(len(indexers), self.thread_count)) as pool:
                pool.starmap(self.search_jackett_indexer, args)
        else:
            self.search_jackett_indexer(what, category, 'all')

        if True:
            with open(__file__, 'rb') as thisFile:
                self.pretty_printer_thread_safe({
                    'seeds': 99999,
                    'size': -1,
                    'leech': -1,
                    'engine_url': self.url,
                    'link': 'https://raw.githubusercontent.com/galeksandrp/search-plugins/jackett-test/nova3/engines/jackett.py',
                    'desc_link': hashlib.sha256(thisFile.read()).hexdigest(),  # noqa
                    'name': 'J: [%s] %s %s %s total %s' % (self.utilsLines, what, category, self.utilsIndexers, self.utilsIndexersTotal)  # noqa
                })

    def get_jackett_indexers(self, what):
        params = [
            ('apikey', self.api_key),
            ('t', 'indexers'),
            ('configured', 'true')
        ]
        if self.name  == 'Prowlarr':
            params = [params[0]]
        params = urlencode(params)
        jacket_url = self.url + ("/api/v1/indexer?%s" if self.name  == 'Prowlarr' else "/api/v2.0/indexers/all/results/torznab/api?%s") % params
        response = self.get_response(jacket_url)
        if response is None:
            self.handle_error("connection error getting indexer list", what)
            return
        # process results
        if self.name  == 'Prowlarr':
            indexers = []
            for indexer in json.loads(response):
                if True:
                    if indexer['enable']:
                        indexers.append(indexer)
                else:
                    indexers.append(str(indexer['id']))
            return indexers
        response_xml = xml.etree.ElementTree.fromstring(response)
        indexers = []
        for indexer in response_xml.findall('indexer'):
            indexers.append(indexer.attrib['id'])
        return indexers

    def search_jackett_indexer(self, what, category, indexer_id):
        if True:
            indexer_name = indexer_id
            if self.name  == 'Prowlarr':
                indexer_name = indexer_id['name']
                indexer_id = str(indexer_id['id'])
        # prepare jackett / prowlarr url
        params = [
            ('apikey', self.api_key),
            ('q', what)
        ]
        if self.name  == 'Prowlarr':
            params.append(('t', 'search'))
        if category is not None:
            params.append(('cat', ','.join(category)))
        params = urlencode(params)
        jacket_url = self.url + ("/" + indexer_id + "/api?%s" if self.name  == 'Prowlarr' else "/api/v2.0/indexers/" + indexer_id + "/results/torznab/api?%s") % params  # noqa
        response = self.get_response(jacket_url)
        if response is None:
            if True:
                self.handle_error("connection error for indexer: " + indexer_name, what)
            else:
                self.handle_error("connection error for indexer: " + indexer_id, what)
            return
        # process search results
        response_xml = xml.etree.ElementTree.fromstring(response)
        for result in response_xml.find('channel').findall('item'):
            res = {}

            title = result.find('title')
            if title is not None:
                title = title.text
            else:
                continue

            tracker = result.find(self.name.lower() + 'indexer')
            tracker = '' if tracker is None else tracker.text
            if CONFIG_DATA['tracker_first']:
                res['name'] = '[%s] %s' % (tracker, title)
            else:
                res['name'] = '%s [%s]' % (title, tracker)

            res['link'] = result.find(self.generate_xpath('magneturl'))
            if res['link'] is not None:
                res['link'] = res['link'].attrib['value']
            else:
                res['link'] = result.find('link')
                if res['link'] is not None:
                    res['link'] = res['link'].text
                else:
                    continue

            res['size'] = result.find('size')
            res['size'] = -1 if res['size'] is None else (res['size'].text + ' B')

            res['seeds'] = result.find(self.generate_xpath('seeders'))
            res['seeds'] = -1 if res['seeds'] is None else int(res['seeds'].attrib['value'])

            if True:
                utilsSizeInt = int(result.find('size').text)
                res['name'] = '%s %s [%s] [%s]' % (title, what, tracker, 'MOREGB' if utilsSizeInt > (9 * BYTES_IN_GB) else '')
                res['name'] = '[%s] %s' % ('%017.10f'%((utilsSizeInt * res['seeds']) / BYTES_IN_GB), res['name'])

            res['leech'] = result.find(self.generate_xpath('peers'))
            res['leech'] = -1 if res['leech'] is None else int(res['leech'].attrib['value'])

            if res['seeds'] != -1 and res['leech'] != -1:
                res['leech'] -= res['seeds']

            res['desc_link'] = result.find('comments')
            if res['desc_link'] is not None:
                res['desc_link'] = res['desc_link'].text
            else:
                res['desc_link'] = result.find('guid')
                res['desc_link'] = '' if res['desc_link'] is None else res['desc_link'].text

            # note: engine_url can't be changed, torrent download stops working
            res['engine_url'] = self.url

            self.pretty_printer_thread_safe(res)

        if True:
            self.utilsIndexers[indexer_name] = len(response_xml.find('channel').findall('item'))
            self.utilsIndexersTotal = self.utilsIndexersTotal + 1;

            if len(self.utilsIndexers) > 2:
                with open(__file__, 'rb') as thisFile:
                    self.pretty_printer_thread_safe({
                        'seeds': 99999,
                        'size': -1,
                        'leech': -1,
                        'engine_url': self.url,
                        'link': 'https://raw.githubusercontent.com/galeksandrp/search-plugins/jackett-test/nova3/engines/jackett.py',
                        'desc_link': hashlib.sha256(thisFile.read()).hexdigest(),  # noqa
                        'name': 'J: [%s] %s %s %s' % (self.utilsLines, what, category, self.utilsIndexers)  # noqa
                    })
                self.utilsLines = self.utilsLines + 1
                self.utilsIndexers = {}

    def generate_xpath(self, tag):
        return './{http://torznab.com/schemas/2015/feed}attr[@name="%s"]' % tag

    def get_response(self, query):
        response = None
        try:
            # we can't use helpers.retrieve_url because of redirects
            # we need the cookie processor to handle redirects
            opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(CookieJar()))
            response = opener.open(query).read().decode('utf-8')
        except urllib_request.HTTPError as e:
            # if the page returns a magnet redirect, used in download_torrent
            if e.code == 302:
                response = e.url
        except Exception:
            pass
        return response

    def handle_error(self, error_msg, what):
        # we need to print the search text to be displayed in qBittorrent when
        # 'Torrent names only' is enabled
        self.pretty_printer_thread_safe({
            'seeds': -1,
            'size': -1,
            'leech': -1,
            'engine_url': self.url,
            'link': self.url,
            'desc_link': 'https://github.com/qbittorrent/search-plugins/wiki/How-to-configure-Jackett-plugin',  # noqa
            'name': self.name + ": %s! Right-click this row and select 'Open description page' to open help. Configuration file: '%s' Search: '%s'" % (error_msg, CONFIG_PATH, what)  # noqa
        })

    def pretty_printer_thread_safe(self, dictionary):
        global PRINTER_THREAD_LOCK
        with PRINTER_THREAD_LOCK:
            prettyPrinter(self.escape_pipe(dictionary))

    def escape_pipe(self, dictionary):
        # Safety measure until it's fixed in prettyPrinter
        for key in dictionary.keys():
            if isinstance(dictionary[key], str):
                dictionary[key] = dictionary[key].replace('|', '%7C')
        return dictionary


if __name__ == "__main__":
    jackett_se = jackett()
    jackett_se.search("ubuntu server", 'software')
