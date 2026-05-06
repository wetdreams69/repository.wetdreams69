"""
tests/test_loader.py
~~~~~~~~~~~~~~~~~~~~
Tests de ManifestLoader: caché, invalidación, errores de fetch y
inyección de fetcher/parser.
"""

from unittest.mock import MagicMock, call

import pytest
from adskipper.loader import ManifestLoader
from adskipper.period import Period
from tests.conftest   import make_period






def _make_fetcher(content: str = "") -> MagicMock:
    fetcher = MagicMock()
    fetcher.fetch.return_value = content
    return fetcher


def _make_parser(periods=None) -> MagicMock:
    parser = MagicMock()
    parser.parse.return_value = periods or []
    return parser


_SAMPLE_PERIODS = [
    make_period(id="c1", start=0.0,  duration=60.0),
    make_period(id="ad", start=60.0, duration=30.0),
]






class TestManifestLoaderCache:

    def test_get_periods_returns_parsed_result(self):
        loader = ManifestLoader(
            url     = "http://example.com/stream.mpd",
            fetcher = _make_fetcher("xml"),
            parser  = _make_parser(_SAMPLE_PERIODS),
        )
        periods = loader.get_periods()
        assert periods == _SAMPLE_PERIODS

    def test_get_periods_cached_after_first_call(self):
        fetcher = _make_fetcher("xml")
        parser  = _make_parser(_SAMPLE_PERIODS)
        loader  = ManifestLoader(url="http://x.com/s.mpd", fetcher=fetcher, parser=parser)

        loader.get_periods()
        loader.get_periods()


        fetcher.fetch.assert_called_once()
        parser.parse.assert_called_once()

    def test_invalidate_forces_refetch(self):
        fetcher = _make_fetcher("xml")
        parser  = _make_parser(_SAMPLE_PERIODS)
        loader  = ManifestLoader(url="http://x.com/s.mpd", fetcher=fetcher, parser=parser)

        loader.get_periods()
        loader.invalidate()
        loader.get_periods()

        assert fetcher.fetch.call_count == 2
        assert parser.parse.call_count == 2

    def test_invalidate_then_cache_again(self):
        fetcher = _make_fetcher("xml")
        parser  = _make_parser(_SAMPLE_PERIODS)
        loader  = ManifestLoader(url="http://x.com/s.mpd", fetcher=fetcher, parser=parser)

        loader.get_periods()
        loader.invalidate()
        loader.get_periods()
        loader.get_periods()

        assert fetcher.fetch.call_count == 2


class TestManifestLoaderFetchError:

    def test_fetch_exception_returns_empty_list(self):
        fetcher = MagicMock()
        fetcher.fetch.side_effect = OSError("connection refused")
        loader = ManifestLoader(url="http://bad.com/s.mpd", fetcher=fetcher)
        result = loader.get_periods()
        assert result == []

    def test_fetch_error_result_is_cached(self):
        """El resultado vacío de un fetch fallido también se cachea."""
        fetcher = MagicMock()
        fetcher.fetch.side_effect = OSError("timeout")
        loader = ManifestLoader(url="http://bad.com/s.mpd", fetcher=fetcher)

        loader.get_periods()
        loader.get_periods()

        assert fetcher.fetch.call_count == 1


class TestManifestLoaderDefaults:

    def test_default_fetcher_and_parser_injected(self):
        """ManifestLoader must work without explicit fetcher/parser (uses defaults)."""
        loader = ManifestLoader(url="http://example.com/s.mpd")

        assert loader is not None

    def test_url_passed_to_fetcher(self):
        url     = "http://cdn.example.com/live.mpd"
        fetcher = _make_fetcher("<MPD/>")
        parser  = _make_parser([])
        loader  = ManifestLoader(url=url, fetcher=fetcher, parser=parser)
        loader.get_periods()
        fetcher.fetch.assert_called_once_with(url)

    def test_raw_content_passed_to_parser(self):
        raw_xml = "<MPD xmlns='urn:mpeg:dash:schema:mpd:2011'/>"
        fetcher = _make_fetcher(raw_xml)
        parser  = _make_parser([])
        loader  = ManifestLoader(url="http://x.com/s.mpd", fetcher=fetcher, parser=parser)
        loader.get_periods()
        parser.parse.assert_called_once_with(raw_xml)
