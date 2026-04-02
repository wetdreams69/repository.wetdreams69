import json
import urllib.parse
import urllib.request
import uuid
import xbmc
from cache_manager import CacheManager

cache_manager = CacheManager()

from constants import (
    HEADERS_BASE,
    AUTH_PARAMS_START,
    URL_AUTH_START,
    LOG_PREFIX_PLUTO,
)


def build_url(url, params=None):
    if not params:
        return url
    return f"{url}?{urllib.parse.urlencode(params)}"


def http_get(url, headers=None, params=None, cache_name=None):
    if cache_name:
        cached_data = cache_manager.get(cache_name, url, params)
        if cached_data:
            xbmc.log(f"{LOG_PREFIX_PLUTO} Usando caché para: {cache_name}", xbmc.LOGDEBUG)
            return cached_data

    headers = headers or HEADERS_BASE
    final_url = build_url(url, params)
    req = urllib.request.Request(final_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        data = json.loads(res.read().decode())
        if cache_name:
            cache_manager.set(cache_name, data, url, params)
        return data


def get_token():
    cached_token = cache_manager.get('csrf_token')
    if cached_token:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Usando token cacheado", xbmc.LOGINFO)
        return cached_token

    params = AUTH_PARAMS_START.copy()
    params.update({
        "clientID": str(uuid.uuid4()),
        "deviceId": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
    })
    data = http_get(URL_AUTH_START, params=params)
    token = data["sessionToken"]
    cache_manager.set('csrf_token', token)
    xbmc.log(f"{LOG_PREFIX_PLUTO} Token obtenido y cacheado", xbmc.LOGINFO)
    return token
