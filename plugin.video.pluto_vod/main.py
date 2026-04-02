import sys
import urllib.parse
import xbmcplugin
import xbmcgui

from search import search, list_series, list_episodes, list_categories, list_category_items
from player import play

addon_handle = int(sys.argv[1])
ad_skipper_data = {}


def router():
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))

    action = params.get("action")

    if action == "search":
        query = xbmcgui.Dialog().input("Buscar")

        if not query:
            return

        search(addon_handle, query)

    elif action == "categories":
        list_categories(addon_handle)

    elif action == "category_items":
        list_category_items(addon_handle, params["id"])

    elif action == "series":
        list_series(addon_handle, params["id"])

    elif action == "episodes":
        list_episodes(addon_handle, params["id"], params["season"])

    elif action == "play":
        play(addon_handle, params["id"], ad_skipper_data)

    else:
        # Mostrar opción de búsqueda
        li = xbmcgui.ListItem(label="Buscar")
        url = f"{sys.argv[0]}?action=search"
        xbmcplugin.addDirectoryItem(addon_handle, url, li, True)

        # Mostrar todas las categorías directamente
        list_categories(addon_handle, show_end_directory=False)
        
        xbmcplugin.endOfDirectory(addon_handle)


router()
