import sys
import urllib.parse
import xbmc
import xbmcgui
from urllib.parse import urlparse

import core.constants as const
from core.api import get_channels, get_logos
from core.cache import cache
from core.http_client import HttpClient
from core.player import PlaybackTracker, setup_item
from core.utils import get_better_logo, should_ignore_channel
from kodi.api import ListItem, add_directory_item, set_content, end_of_directory, set_resolved_url, log
from resolvers import resolve_url


def build_url(query):
    return const.BASE_URL + '?' + urllib.parse.urlencode(query)


def list_channels():
    channels = get_channels()
    logos_dict = get_logos()
    for idx, channel in enumerate(channels):
        if not channel.get('show', True) or should_ignore_channel(channel, const.IGNORE_CATEGORIES):
            continue
        name = channel.get('name', 'Unknown Channel')
        logo = channel.get('logo', '')
        if any(bad in logo for bad in const.BAD_LOGO_DOMAINS):
            logo = ''
        better_logo = get_better_logo(name, logos_dict)
        if better_logo:
            logo = better_logo
        list_item = ListItem(label=name)
        list_item.set_art({'thumb': logo, 'icon': logo, 'poster': logo})
        list_item.getVideoInfoTag().setTitle(name)
        url = build_url({'action': 'options', 'channel_idx': idx})
        add_directory_item(const.ADDON_HANDLE, url, list_item, isFolder=True)
    set_content(const.ADDON_HANDLE, 'videos')
    end_of_directory(const.ADDON_HANDLE)


def list_options(channel_idx):
    channels = get_channels()
    idx = int(channel_idx)
    if idx >= len(channels):
        return
    options = channels[idx].get('options', [])
    for option in options:
        name = option.get('name', 'Source')
        url = option.get('iframe') or option.get('url', '')
        if not url:
            continue
        stats = cache.get(f'stats:{url}') or {'s': 0, 't': 0}
        color = _get_status_color(stats)
        list_item = ListItem(label=f'[COLOR {color}]{name}[/COLOR]')
        list_item.getVideoInfoTag().setTitle(name)
        list_item.set_property('IsPlayable', 'true')
        play_url = build_url({'action': 'play', 'url': url})
        add_directory_item(const.ADDON_HANDLE, play_url, list_item, isFolder=False)
    end_of_directory(const.ADDON_HANDLE)


def play_video(url):
    log(f'[Angulismo] Play request: {url}')
    tracker = PlaybackTracker(url)
    tracker.record_attempt()
    
    resolved = resolve_url(url)
    if not resolved:
        set_resolved_url(const.ADDON_HANDLE, False, listitem=ListItem(path=''))
        return

    real_url, headers, clearkey = _parse_resolved_url(resolved)
    
    if not headers and not clearkey:
        headers = _generate_default_headers(url)

    final_headers = _probe_and_fix_headers(real_url, headers)
    
    setup_item(real_url, final_headers, clearkey)
    tracker.monitor()


def _get_status_color(stats):
    if stats['t'] == 0:
        return 'white'
    if stats['s'] == 0:
        return 'red'
    if stats['s'] == stats['t']:
        return 'green'
    return 'yellow'


def _parse_resolved_url(resolved):
    real_url = resolved
    headers = ''
    clearkey = ''
    
    if '&clearkey=' in resolved:
        parts = resolved.rsplit('&clearkey=', 1)
        url_part, clearkey = parts[0], parts[1]
        if '|' in url_part:
            real_url, headers = url_part.split('|', 1)
        else:
            real_url = url_part
    elif '|clearkey=' in resolved:
        real_url, clearkey = resolved.split('|clearkey=', 1)
    elif '|' in resolved:
        real_url, headers = resolved.split('|', 1)
        
    return real_url, headers, clearkey


def _generate_default_headers(original_url):
    try:
        p = urlparse(original_url)
        ref = f"{p.scheme}://{p.netloc}/"
        ua = HttpClient().headers.get('User-Agent')
        return f'Referer={urllib.parse.quote(ref)}&User-Agent={urllib.parse.quote(ua)}'
    except Exception:
        return ''


def _probe_and_fix_headers(url, current_headers):
    client = HttpClient()
    probe_hdrs = _header_str_to_dict(current_headers)
    
    try:
        if client.head(url, headers=probe_hdrs).status_code == 200:
            return current_headers
            
        p = urlparse(url)
        origin = f"{p.scheme}://{p.netloc}"
        candidates = [
            {'Referer': const.HEADERS['referer']},
            {'Referer': origin, 'Origin': origin}
        ]
        
        ua = client.headers.get('User-Agent')
        for cand in candidates:
            hdrs = dict(cand)
            hdrs['User-Agent'] = ua
            if client.head(url, headers=hdrs).status_code == 200:
                return '&'.join([f'{k}={v}' for k, v in hdrs.items()])
    except Exception:
        pass
        
    return current_headers


def _header_str_to_dict(headers_str):
    d = {}
    if not headers_str:
        return d
    for part in headers_str.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            d[k] = v
    return d


def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get('action')
    if action is None:
        list_channels()
    elif action == 'options':
        list_options(params.get('channel_idx', 0))
    elif action == 'play':
        play_video(params.get('url', ''))
    elif action == 'clear_cache':
        cache.clear()
        xbmcgui.Dialog().notification('Angulismo TV', 'Cache limpiado correctamente', xbmcgui.NOTIFICATION_INFO, 3000)
        xbmc.executebuiltin('Container.Refresh')
