"""
adskipper.fetcher
~~~~~~~~~~~~~~~~~
Retrieves the raw MPD manifest content over HTTP.
"""

import urllib.request
from typing import Protocol

from adskipper._compat import xbmc

_LOG = "[adskipper.fetcher]"

_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0",
}


class ManifestFetcher(Protocol):
    def fetch(self, url: str) -> str:
        """Return the raw manifest text for *url*."""
        ...


class HttpManifestFetcher:
    """
    Fetches an MPD manifest via ``urllib.request``.

    Parameters
    ----------
    headers : dict, optional
        HTTP headers sent with every request.
        Merged on top of ``_DEFAULT_HEADERS``; caller-supplied values win.
    timeout : int, optional
        Socket timeout in seconds (default 10).
    """

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        timeout: int = 10,
    ) -> None:
        self._headers = {**_DEFAULT_HEADERS, **(headers or {})}
        self._timeout = timeout

    def fetch(self, url: str) -> str:
        """
        Retrieve *url* and return its body decoded as UTF-8.

        Raises
        ------
        OSError
            On network errors, timeouts, or non-2xx responses.
        """
        xbmc.log(f"{_LOG} GET {url}", xbmc.LOGINFO)
        req = urllib.request.Request(url, headers=self._headers)
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return resp.read().decode("utf-8")
