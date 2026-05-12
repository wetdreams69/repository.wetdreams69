import uuid
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import threading

from api import get_token, HEADERS_BASE, http_get
from adskipper import start_ad_skipper
from constants import (
    URL_EPISODES,
    URL_STREAM_STITCHER,
    URL_DRM_LICENSE,
    AUTH_PARAMS,
    DEVICE_PARAMS,
    AD_MIN_DURATION,
    AD_MAX_DURATION,
    IST_HEADERS,
    MIME_TYPE_DASH,
    INPUTSTREAM_NAME,
    DRM_LICENSE_TYPE,
    LOG_PREFIX_PLUTO,
    LOG_PREFIX_AD_SKIP,
)


def play(addon_handle, content_id, ad_skipper_data):
    token = get_token()
    headers = HEADERS_BASE.copy()
    headers["Authorization"] = f"Bearer {token}"
    try:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Getting episode: {content_id}", xbmc.LOGINFO)
        data = http_get(
            URL_EPISODES.format(content_id=content_id),
            headers,
            DEVICE_PARAMS,
        )
        stitched = data.get("stitched", {})
        paths = stitched.get("paths", [])
        dash_path = None
        for p in paths:
            if p.get("type") == "mpd":
                dash_path = p.get("path")
                break
        if not dash_path:
            raise ValueError("No DASH stream found")
        client_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        params = AUTH_PARAMS.copy()
        params.update({
            "advertisingId": "",
            "clientID": client_id,
            "deviceId": client_id,
            "sessionID": session_id,
            "sid": session_id,
            "userId": "",
            "jwt": token,
            "masterJWTPassthrough": "true",
            "includeExtendedEvents": "true",
        })
        base = URL_STREAM_STITCHER
        stream = f"{base}/v2{dash_path}?{urllib.parse.urlencode(params)}"
        xbmc.log(f"{LOG_PREFIX_PLUTO} Stream URL built", xbmc.LOGINFO)

        addon = xbmcaddon.Addon()
        if addon.getSettingBool("ads_skipper"):
            skipper, thread = start_ad_skipper(
                stream_url=stream,
                label="Pluto TV",
                min_duration=AD_MIN_DURATION,
                max_duration=AD_MAX_DURATION,
                extra_headers={
                    "Origin": "https://pluto.tv",
                    "Referer": "https://pluto.tv/",
                }
            )
            ad_skipper_data['skipper'] = skipper
            ad_skipper_data['thread'] = thread
        
        li = xbmcgui.ListItem(path=stream)
        li.setMimeType(MIME_TYPE_DASH)
        li.setProperty("inputstream", INPUTSTREAM_NAME)
        li.setProperty("inputstream.adaptive.manifest_headers", IST_HEADERS)
        li.setProperty("inputstream.adaptive.stream_headers", IST_HEADERS)
        li.setProperty("inputstream.adaptive.license_type", DRM_LICENSE_TYPE)
        li.setProperty(
            "inputstream.adaptive.license_key",
            f"{URL_DRM_LICENSE.format(token=token)}"
            f"|User-Agent=Mozilla/5.0&Content-Type=application/octet-stream"
            f"|R{{SSM}}|",
        )
        li.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(addon_handle, True, li)
    except Exception as e:
        xbmc.log(f"{LOG_PREFIX_PLUTO} play failed: {e}", xbmc.LOGERROR)
        import traceback
        xbmc.log(f"{LOG_PREFIX_PLUTO} Traceback: {traceback.format_exc()}", xbmc.LOGERROR)
        dialog = xbmcgui.Dialog()
        dialog.ok("Error", f"Could not play content: {str(e)}")
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
