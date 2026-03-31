import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
from urllib.parse import parse_qsl
import json
import os

_URL = sys.argv[0]
_HANDLE = int(sys.argv[1])
_ADDON = xbmcaddon.Addon()

# Ruta del archivo de cache
CACHE_FILE = os.path.join(os.path.dirname(__file__), 'resources', 'channel_names_cache.json')

def load_channel_name_cache():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_channel_name_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Error guardando cache de nombres de canales: {e}", xbmc.LOGERROR)

def get_channel_name_from_youtube_addon(channel_id):
    """Obtiene el nombre del canal usando el addon de YouTube de Kodi o el cache."""
    cache = load_channel_name_cache()
    if channel_id in cache:
        return cache[channel_id]
    try:
        youtube_addon = xbmcaddon.Addon('plugin.video.youtube')
        channel_info_url = f'plugin://plugin.video.youtube/channel/{channel_id}/'
        json_query = {
            "jsonrpc": "2.0",
            "method": "Files.GetDirectory",
            "params": {
                "directory": channel_info_url,
                "media": "video",
                "properties": ["title", "plot", "art"]
            },
            "id": 1
        }
        response = xbmc.executeJSONRPC(json.dumps(json_query))
        result = json.loads(response)
        if 'result' in result and 'files' in result['result']:
            for file_info in result['result']['files']:
                if 'title' in file_info and file_info['title'] and file_info['title'] != channel_id:
                    title = file_info['title']
                    cache[channel_id] = title
                    save_channel_name_cache(cache)
                    return title
        # Si no se encuentra, usar fallback y guardar en cache
        fallback = get_channel_name_fallback(channel_id)
        cache[channel_id] = fallback
        save_channel_name_cache(cache)
        return fallback
    except Exception as e:
        log(f"Error obteniendo nombre del canal desde addon YouTube: {str(e)}", xbmc.LOGERROR)
        fallback = get_channel_name_fallback(channel_id)
        cache[channel_id] = fallback
        save_channel_name_cache(cache)
        return fallback

def get_channel_name_fallback(channel_id):
    return f'Canal {channel_id[:8]}...'

def get_channels():
    channels = _ADDON.getSetting('channel_ids').strip()
    return [c.strip() for c in channels.split(',') if c.strip()]

def log(message, level=xbmc.LOGDEBUG):
    xbmc.log(f"[{_ADDON.getAddonInfo('id')}] {message}", level)

def list_channels():
    channels = get_channels()
    log(f"Listando canales: {channels}")  # Log de depuración
    
    for channel_id in channels:
        channel_name = get_channel_name_from_youtube_addon(channel_id)
        youtube_url = f'plugin://plugin.video.youtube/channel/{channel_id}/?browse=1'
        log(f"Añadiendo canal: {channel_id} con nombre: {channel_name} y URL: {youtube_url}")  # Otro log útil
        
        list_item = xbmcgui.ListItem(label=channel_name)
        list_item.setArt({'icon': 'DefaultFolder.png'})
        list_item.setInfo('video', {'title': channel_name})
        
        xbmcplugin.addDirectoryItem(
            handle=_HANDLE,
            url=youtube_url,
            listitem=list_item,
            isFolder=True
        )
    
    xbmcplugin.endOfDirectory(_HANDLE)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    
    if not params:
        list_channels()
    else:
        list_channels()

if __name__ == '__main__':
    router(sys.argv[2][1:])
