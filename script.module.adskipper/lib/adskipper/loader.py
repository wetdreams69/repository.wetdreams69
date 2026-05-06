"""
adskipper.loader
~~~~~~~~~~~~~~~~
Composes ``ManifestFetcher`` and ``MpdParser`` into a single high-level
object and adds in-memory caching.
"""

from adskipper._compat import xbmc

from adskipper.fetcher import HttpManifestFetcher, ManifestFetcher
from adskipper.parser  import MpdParser
from adskipper.period  import Period

_LOG = "[adskipper.loader]"


class ManifestLoader:
    """
    Coordinates fetching and parsing the manifest, keeping the result in memory.

    Parameters
    ----------
    url : str
        MPEG-DASH ``.mpd`` manifest URL.
    fetcher : ManifestFetcher, optional
        Transport implementation. Defaults to ``HttpManifestFetcher()``.
    parser : MpdParser, optional
        XML parsing implementation. Defaults to ``MpdParser()``.
    cache_errors : bool, optional
        If True, a failed fetch will cache an empty result. If False,
        subsequent calls will retry the fetch. Defaults to True.
    """

    def __init__(
        self,
        url:          str,
        fetcher:      ManifestFetcher | None = None,
        parser:       MpdParser | None       = None,
        cache_errors: bool                   = True,
    ) -> None:
        self._url          = url
        self._fetcher      = fetcher or HttpManifestFetcher()
        self._parser       = parser  or MpdParser()
        self._cache_errors = cache_errors
        self._cache:       list[Period] | None = None

    def get_periods(self) -> list[Period]:
        """
        Return all periods from the manifest.

        Results are cached; call :meth:`invalidate` to force a fresh fetch.
        """
        if self._cache is not None:
            return self._cache

        try:
            raw = self._fetcher.fetch(self._url)
            periods = self._parser.parse(raw)
            self._cache = periods
            return periods
        except Exception as exc:
            xbmc.log(f"{_LOG} Fetch error: {exc}", xbmc.LOGERROR)
            if self._cache_errors:
                self._cache = []
            return []

    def invalidate(self) -> None:
        """Discard the cached periods so the next call re-fetches."""
        self._cache = None
