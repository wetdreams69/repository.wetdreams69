URL_AUTH_START = "https://boot.pluto.tv/v4/start"
URL_SEARCH = "https://service-media-search.clusters.pluto.tv/v1/search"
URL_CATEGORIES = "https://service-vod.clusters.pluto.tv/v4/vod/categories"
URL_CATEGORY_ITEMS = "https://service-vod.clusters.pluto.tv/v4/vod/categories/{category_id}/items"
URL_SERIES_SEASONS = "https://service-vod.clusters.pluto.tv/v4/vod/series/{content_id}/seasons"
URL_EPISODES = "https://service-vod.clusters.pluto.tv/v4/vod/episodes/{content_id}"
URL_ON_DEMAND = "https://pluto.tv/on-demand"
URL_STREAM_STITCHER = "https://cfd-v4-service-stitcher-dash-use1-1.prd.pluto.tv"
URL_DRM_LICENSE = "https://service-concierge.clusters.pluto.tv/v1/wv/alt?jwt={token}"

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://pluto.tv",
    "Referer": "https://pluto.tv/",
}

IST_HEADERS = (
    "User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    "&Origin=https://pluto.tv"
    "&Referer=https://pluto.tv/"
)

AUTH_PARAMS = {
    "appName": "web",
    "appVersion": "9.20.0-89258290264838515e264f5b051b7c1602a58482",
    "clientModelNumber": "1.0.0",
    "deviceDNT": "false",
    "deviceMake": "chrome",
    "deviceModel": "web",
    "deviceType": "web",
    "deviceVersion": "142.0.0",
    "serverSideAds": "false",
}

AUTH_PARAMS_START = {
    "appName": "web",
    "appVersion": "na",
    "clientModelNumber": "na",
    "serverSideAds": "false",
    "deviceMake": "unknown",
    "deviceModel": "web",
    "deviceType": "web",
    "deviceVersion": "unknown",
    "drmCapabilities": "widevine:L3",
}

SEARCH_PARAMS = {
    "limit": 50,
}

CATEGORIES_PARAMS = {
    "includeItems": "false",
    "includeCategoryFields": "description,iconSvg",
    "sort": "number:asc",
}

CATEGORY_ITEMS_PARAMS = {
    "offset": 0,
    "page": 1,
}

DEVICE_PARAMS = {
    "deviceType": "web",
}

AD_MIN_DURATION = 15
AD_MAX_DURATION = 45

DRM_LICENSE_TYPE = "com.widevine.alpha"
MIME_TYPE_DASH = "application/dash+xml"
INPUTSTREAM_NAME = "inputstream.adaptive"

LOG_PREFIX_PLUTO = "[PLUTO]"
LOG_PREFIX_AD_SKIP = "[AD SKIP]"
