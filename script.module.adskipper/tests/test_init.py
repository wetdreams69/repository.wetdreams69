"""
tests/test_init.py
~~~~~~~~~~~~~~~~~~
Tests de la factory start_ad_skipper() en adskipper/__init__.py.
Verifica el wiring de componentes, thread daemon y comportamiento de stop().
"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest
import adskipper
import adskipper.monitor as monitor_mod
from adskipper import start_ad_skipper, AdSkipper






_MINIMAL_MPD = (
    '<?xml version="1.0"?>'
    '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011">'
    '<Period id="c1" duration="PT120S"/>'
    "</MPD>"
)


def _fake_fetcher(content: str = _MINIMAL_MPD):
    """Creates a mock fetcher that returns content."""
    f = MagicMock()
    f.fetch.return_value = content
    return f






class TestStartAdSkipperReturnValues:

    def test_returns_tuple_of_skipper_and_thread(self):
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper("http://example.com/s.mpd")
        assert isinstance(skipper, AdSkipper)
        assert isinstance(thread, threading.Thread)
        skipper.stop()
        thread.join(timeout=1.0)

    def test_thread_is_daemon(self):
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper("http://example.com/s.mpd")
        assert thread.daemon is True
        skipper.stop()
        thread.join(timeout=1.0)

    def test_thread_is_alive_before_stop(self):
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper(
                "http://example.com/s.mpd",

            )
        time.sleep(0.1)
        assert thread.is_alive()
        skipper.stop()
        thread.join(timeout=1.0)


class TestStartAdSkipperStop:

    def test_stop_terminates_thread(self):
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper("http://example.com/s.mpd")
        skipper.stop()
        thread.join(timeout=2.0)
        assert not thread.is_alive(), "El thread no terminó tras skipper.stop()"

    def test_stop_calls_original_stop_if_present(self):
        """Bug #1 fix: _stop_all debe invocar el stop() original del skipper."""
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper("http://example.com/s.mpd")



        skipper.stop()
        thread.join(timeout=2.0)
        assert not thread.is_alive()


class TestStartAdSkipperOptions:

    def test_silent_notifier_when_notify_false(self):
        from adskipper.notifier import SilentNotifier
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper(
                "http://example.com/s.mpd",
                notify=False,
            )
        skipper.stop()
        thread.join(timeout=1.0)

        assert skipper.skip_count == 0

    def test_custom_duration_range(self):
        """min_duration and max_duration are passed to DurationAdDetector."""
        with patch("adskipper.HttpManifestFetcher", return_value=_fake_fetcher()):
            skipper, thread = start_ad_skipper(
                "http://example.com/s.mpd",
                min_duration=5.0,
                max_duration=10.0,
            )
        skipper.stop()
        thread.join(timeout=1.0)
        assert skipper is not None

    def test_extra_headers_forwarded(self):
        """extra_headers is passed to HttpManifestFetcher."""
        headers = {"Origin": "https://pluto.tv", "Referer": "https://pluto.tv/"}
        fetcher_instance = _fake_fetcher()

        with patch("adskipper.HttpManifestFetcher", return_value=fetcher_instance) as MockFetcher:
            skipper, thread = start_ad_skipper(
                "http://example.com/s.mpd",
                extra_headers=headers,
            )
        skipper.stop()
        thread.join(timeout=1.0)


        MockFetcher.assert_called_once()
        call_kwargs = MockFetcher.call_args
        assert call_kwargs.kwargs.get("headers") == headers or\
               (call_kwargs.args and call_kwargs.args[0] == headers),\
               f"HttpManifestFetcher no recibió los extra_headers: {call_kwargs}"
