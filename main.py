import traceback

from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode, toUnicode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media.movie.providers.base import MovieProvider


log = CPLog(__name__)


class Funfile(TorrentProvider, MovieProvider):

    urls = {
        'test': 'https://www.funfile.org/',
        'login': 'https://www.funfile.org/takelogin.php',
        'login_check': 'https://www.funfile.org/my.php',
        'detail': 'https://www.funfile.org/details.php?id=%s',
        'search': 'https://www.funfile.org/browse.php?search=%s&cat=19&incldead=0&s_title=1&showspam=0',
        'download': 'https://www.funfile.org/download.php/%s/%s',
    }

    quality_map = {
        '720p': '720p x264',
        '1080p': '1080p x264',
        'BR-Rip': 'BDRip x264',
        'BR-Disk': 'Bluray',
        'DVD-Rip': 'DVDRip x264',
    }

    http_time_between_calls = 1 #Seconds

    def getQuality(self, quality = None):

        if not quality: return ''
        identifier = quality.get('identifier')
        return self.quality_map.get(identifier, '')

    def _searchOnTitle(self, title, movie, quality, results):

        url = self.urls['search'] % tryUrlencode('%s %s %s' % (title.replace(':', '').replace(' ', '.'), movie['info']['year'], self.getQuality(quality)))
        data = self.getHTMLData(url)

        if data:
            html = BeautifulSoup(data)

            try:
                result_table = html.find('table', attrs = {'cellspacing':'0', 'cellpadding':'2'})
                if not result_table:
                    return

                entries = result_table.find_all('tr')

                for result in entries[1:]:

                    cells = result.find_all('td')

                    if len(cells) > 6:

                        torrent = cells[1].find('a', attrs = {'style': 'float: left; vertical-align: middle; font-weight: bold;'})

                        if torrent:

                            torrent_id = torrent['href']
                            torrent_id = torrent_id.replace('details.php?id=', '')
                            torrent_id = torrent_id.replace('&hit=1', '')

                            torrent_name = torrent.getText()

                            results.append({
                                'id': torrent_id,
                                'name': torrent_name,
                                'url': self.urls['download'] % (torrent_id, torrent_name + '.torrent'),
                                'detail_url': self.urls['detail'] % torrent_id,
                                'size': self.parseSize(cells[7].contents[0] + cells[7].contents[2]),
                                'seeders': tryInt(cells[9].find('span').contents[0]),
                                'leechers': tryInt(cells[10].find('span').contents[0]),
                            })

            except:
                log.error('Failedtoparsing %s: %s', (self.getName(), traceback.format_exc()))

    def getLoginParams(self):
        return {
            'username': self.conf('username'),
            'password': self.conf('password'),
            'login': 'Login',
        }

    def loginSuccess(self, output):
        return 'logout.php' in output.lower()

    loginCheckSuccess = loginSuccess
