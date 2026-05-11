from core.cache import cache
import xbmcgui
cache.clear()
xbmcgui.Dialog().notification('Angulismo TV', 'Cache limpiado correctamente', xbmcgui.NOTIFICATION_INFO, 3000)
