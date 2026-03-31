import sys
import xbmc
import xbmcgui
import xbmcplugin

from api import get_token, HEADERS_BASE, http_get
from constants import (
    URL_SEARCH,
    URL_CATEGORIES,
    URL_CATEGORY_ITEMS,
    URL_SERIES_SEASONS,
    SEARCH_PARAMS,
    CATEGORIES_PARAMS,
    CATEGORY_ITEMS_PARAMS,
    DEVICE_PARAMS,
    LOG_PREFIX_PLUTO,
)


def search(query):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    data = http_get(URL_SEARCH, headers, {**SEARCH_PARAMS, "q": query})
    xbmc.log(f"{LOG_PREFIX_PLUTO} Search OK", xbmc.LOGINFO)
    return [x for x in data.get("data", []) if x.get("type") in ["movie", "series"]]


def list_series(addon_handle, content_id):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Getting seasons", xbmc.LOGINFO)
        data = http_get(
            URL_SERIES_SEASONS.format(content_id=content_id),
            headers,
            DEVICE_PARAMS,
        )
        for season in data.get("seasons", []):
            num = season.get("number")
            li = xbmcgui.ListItem(label=f"Season {num}")
            url = f"{sys.argv[0]}?action=episodes&id={content_id}&season={num}"
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)
        xbmcplugin.endOfDirectory(addon_handle)
        return
    except Exception as e:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Seasons failed: {e}", xbmc.LOGWARNING)
    xbmc.log(f"{LOG_PREFIX_PLUTO} Fallback → play directo", xbmc.LOGINFO)
    from player import play
    play(addon_handle, content_id, {})


def list_episodes(addon_handle, content_id, season):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    data = http_get(
        URL_SERIES_SEASONS.format(content_id=content_id),
        headers,
        DEVICE_PARAMS,
    )
    for s in data.get("seasons", []):
        if str(s.get("number")) == season:
            for ep in s.get("episodes", []):
                title = ep.get("name", "Episode")
                ep_id = ep.get("_id")
                li = xbmcgui.ListItem(label=title)
                li.setProperty("IsPlayable", "true")
                url = f"{sys.argv[0]}?action=play&id={ep_id}"
                xbmcplugin.addDirectoryItem(addon_handle, url, li, False)
    xbmcplugin.endOfDirectory(addon_handle)


def list_categories(addon_handle, show_end_directory=True):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Getting categories from API", xbmc.LOGINFO)
        
        data = http_get(
            URL_CATEGORIES,
            headers,
            CATEGORIES_PARAMS,
        )
        
        categories = data.get("categories", [])
        xbmc.log(f"{LOG_PREFIX_PLUTO} Found {len(categories)} categories", xbmc.LOGINFO)
        
        for cat in categories:
            name = cat.get("name")
            cat_id = cat.get("_id")
            
            if not name or not cat_id:
                continue
            
            li = xbmcgui.ListItem(label=name)
            url = f"{sys.argv[0]}?action=category_items&id={cat_id}"
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)
        
        if show_end_directory:
            xbmcplugin.endOfDirectory(addon_handle)
    except Exception as e:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Categories failed: {e}", xbmc.LOGWARNING)
        if show_end_directory:
            xbmcplugin.endOfDirectory(addon_handle)


def list_category_items(addon_handle, category_id):
    """Obtiene los ítems de una categoría específica usando la API"""
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Getting category items for {category_id}", xbmc.LOGINFO)
        
        data = http_get(
            URL_CATEGORY_ITEMS.format(category_id=category_id),
            headers,
            CATEGORY_ITEMS_PARAMS,
        )
        
        for item in data.get("items", []):
            name = item.get("name")
            item_id = item.get("_id")
            item_type = item.get("type")
            
            li = xbmcgui.ListItem(label=name)
            
            if item_type == "series":
                url = f"{sys.argv[0]}?action=series&id={item_id}"
                xbmcplugin.addDirectoryItem(addon_handle, url, li, True)
            else:
                li.setProperty("IsPlayable", "true")
                url = f"{sys.argv[0]}?action=play&id={item_id}"
                xbmcplugin.addDirectoryItem(addon_handle, url, li, False)
        
        xbmcplugin.endOfDirectory(addon_handle)
    except Exception as e:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Category items failed: {e}", xbmc.LOGWARNING)
        xbmcplugin.endOfDirectory(addon_handle)
