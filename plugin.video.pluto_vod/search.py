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


def get_art(item):
    art = {}
    if not item:
        return art
    
    # Fanart / Landscape
    featured = item.get("featuredImage")
    if featured and isinstance(featured, dict):
        art["fanart"] = featured.get("path")
    
    # Poster (Vertical)
    covers = item.get("covers") or []
    for cover in covers:
        if not isinstance(cover, dict):
            continue
        if cover.get("aspectRatio") == "347:500":
            art["poster"] = cover.get("url")
            if not art.get("thumb"):
                art["thumb"] = cover.get("url")
            break
            
    # Thumb / Screenshot (Horizontal)
    for cover in covers:
        if not isinstance(cover, dict):
            continue
        if cover.get("aspectRatio") == "16:9":
            art["landscape"] = cover.get("url")
            art["fanart"] = cover.get("url")
            if not art.get("thumb"):
                art["thumb"] = cover.get("url")
            break

    if not art.get("icon") and art.get("thumb"):
        art["icon"] = art["thumb"]
        
    return art


def set_info(li, item, info_type="video"):
    if not item:
        return
    info = {
        "plot": item.get("description") or item.get("summary"),
        "title": item.get("name"),
    }
    
    genre = item.get("genre")
    if genre:
        info["genre"] = genre
        
    clip = item.get("clip", {})
    actors = clip.get("actors")
    if actors:
        info["cast"] = actors
    directors = clip.get("directors")
    if directors:
        info["director"] = ", ".join(directors) if isinstance(directors, list) else directors
        
    try:
        release_date = clip.get("originalReleaseDate")
        if release_date and len(release_date) >= 4:
            info["year"] = int(release_date[:4])
            if "T" in release_date:
                info["premiered"] = release_date.split("T")[0]
    except (ValueError, TypeError, Exception):
        pass

    rating = item.get("rating")
    if rating:
        info["mpaa"] = rating

    item_type = item.get("type")
    if item_type == "movie":
        info["mediatype"] = "movie"
    elif item_type == "series":
        info["mediatype"] = "tvshow"
    elif item_type == "episode":
        info["mediatype"] = "episode"
        info["season"] = item.get("season")
        info["episode"] = item.get("number")
        duration = item.get("duration")
        if duration:
            try:
                info["duration"] = int(float(duration) / 1000)
            except (ValueError, TypeError):
                pass
            
    li.setInfo(info_type, info)


def search(addon_handle, query):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    data = http_get(URL_SEARCH, headers, {**SEARCH_PARAMS, "q": query})
    xbmc.log(f"{LOG_PREFIX_PLUTO} Search OK", xbmc.LOGINFO)
    for r in data.get("data", []):
        if r.get("type") not in ["movie", "series"]:
            continue
        name = r.get("name")
        cid = r.get("_id") or r.get("id")
        type = r.get("type")

        li = xbmcgui.ListItem(label=name)
        li.setArt(get_art(r))
        set_info(li, r)

        if type == "series":
            url = f"{sys.argv[0]}?action=series&id={cid}"
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)
        else:
            li.setProperty("IsPlayable", "true")
            url = f"{sys.argv[0]}?action=play&id={cid}"
            xbmcplugin.addDirectoryItem(addon_handle, url, li, False)

    xbmcplugin.endOfDirectory(addon_handle)


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
            cache_name='fetch_season_episodes'
        )
        series_art = get_art(data)
        for season in data.get("seasons", []):
            num = season.get("number")
            li = xbmcgui.ListItem(label=f"Season {num}")
            li.setArt(series_art)
            set_info(li, data)
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
        cache_name='fetch_season_episodes'
    )
    for s in data.get("seasons", []):
        if str(s.get("number")) == season:
            for ep in s.get("episodes", []):
                title = ep.get("name", "Episode")
                ep_id = ep.get("_id")
                li = xbmcgui.ListItem(label=title)
                li.setArt(get_art(ep))
                set_info(li, ep)
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
            cache_name='fetch_category_data'
        )
        
        categories = data.get("categories", [])
        xbmc.log(f"{LOG_PREFIX_PLUTO} Found {len(categories)} categories", xbmc.LOGINFO)
        
        for cat in categories:
            name = cat.get("name")
            cat_id = cat.get("_id")
            
            if not name or not cat_id:
                continue
            
            li = xbmcgui.ListItem(label=name)
            set_info(li, cat)
            url = f"{sys.argv[0]}?action=category_items&id={cat_id}"
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)
        
        if show_end_directory:
            xbmcplugin.endOfDirectory(addon_handle)
    except Exception as e:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Categories failed: {e}", xbmc.LOGWARNING)
        if show_end_directory:
            xbmcplugin.endOfDirectory(addon_handle)


def list_category_items(addon_handle, category_id):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Getting category items for {category_id}", xbmc.LOGINFO)
        
        data = http_get(
            URL_CATEGORY_ITEMS.format(category_id=category_id),
            headers,
            CATEGORY_ITEMS_PARAMS,
            cache_name='fetch_video_details'
        )
        
        for item in data.get("items", []):
            name = item.get("name")
            item_id = item.get("_id")
            item_type = item.get("type")
            
            li = xbmcgui.ListItem(label=name)
            li.setArt(get_art(item))
            set_info(li, item)
            
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
