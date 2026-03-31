import json
import urllib.parse
import urllib.request
import uuid
import xbmc

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


def http_get(url, headers=None, params=None):
    headers = headers or HEADERS_BASE
    final_url = build_url(url, params)
    req = urllib.request.Request(final_url, headers=headers)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())


def get_token():
    params = AUTH_PARAMS_START.copy()
    params.update({
        "clientID": str(uuid.uuid4()),
        "deviceId": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
    })
    data = http_get(URL_AUTH_START, params=params)
    xbmc.log(f"{LOG_PREFIX_PLUTO} Token obtenido", xbmc.LOGINFO)
    return data["sessionToken"]
