from kodi.api import log
from core.cache import cache
from .bolaloca import resolve as resolve_bolaloca
from .futbollibre import resolve as resolve_futbollibre
from .hoca6 import resolve as resolve_hoca6
from .nebunexa import resolve as resolve_nebunexa
from .streamtp import resolve as resolve_streamtp
from .pracanes import resolve as resolve_pracanes
from .angulismo import resolve as resolve_angulismo
from .elcanaldeportivo import resolve as resolve_elcanaldeportivo
from .la14hd import resolve as resolve_la14hd

# Registry of resolvers: (match_function, resolve_function)
RESOLVER_REGISTRY = [
    (lambda u: "angulismo" in u or "cvattv" in u or "gigared" in u, resolve_angulismo),
    (lambda u: "bolaloca" in u, resolve_bolaloca),
    (lambda u: "la14hd" in u, resolve_la14hd),
    (lambda u: "elcanaldeportivo" in u, resolve_elcanaldeportivo),
    (lambda u: "tucanaldeportivo" in u or "canales.php" in u or "ksdjugfsddeports" in u, resolve_futbollibre),
    (lambda u: "hoca6" in u or "hoca8" in u or "cdn" in u, resolve_hoca6),
    (lambda u: "nebunexa" in u or "bestleague.world" in u, resolve_nebunexa),
    (lambda u: "streamtp" in u or "streamx550" in u, resolve_streamtp),
    (lambda u: "github.io" in u, resolve_pracanes),
]

def resolve_url(url, max_hops=3):
    original_url = url
    for _ in range(max_hops):
        # 1. Clean Proxy Prefixes
        url = _strip_proxies(url)
        
        # 2. Check Cache
        cached = cache.get(f'resolve:{url}')
        if cached:
            log(f'[Angulismo] Using cached resolution: {url}')
            return cached

        # 3. Find Resolver
        resolved = url
        for matcher, resolver_func in RESOLVER_REGISTRY:
            if matcher(url):
                try:
                    resolved = resolver_func(url)
                except Exception as e:
                    log(f'[Angulismo] Resolver error ({resolver_func.__name__}): {str(e)}')
                    resolved = None
                break
        else:
            # No resolver matched, we are done
            break
            
        if not resolved or resolved == url:
            break
            
        # Avoid loops if the base URL didn't change (only headers added)
        if '|' in resolved and resolved.split('|')[0] == url.split('|')[0]:
            url = resolved
            break
            
        log(f'[Angulismo] Hop {_+1}: {resolved}')
        url = resolved

    cache.set(f'resolve:{original_url}', url, ttl=3600)
    return url

def _strip_proxies(url):
    if "proxy" in url.lower() or url.count("http") > 1:
        headers_sep = url.find('|')
        second_http = url.find("http", 8)
        if second_http != -1 and (headers_sep == -1 or second_http < headers_sep):
            prefix = url[:second_http]
            if prefix.endswith('/') or prefix.endswith('='):
                new_url = url[second_http:]
                log(f'[Angulismo] Proxy stripped: {new_url}')
                return new_url
    return url
