"""
script.module.adskipper
~~~~~~~~~~~~~~~~~~~~~~~
Main entry point. Exposes the ``start_ad_skipper`` factory to
instantiate and start monitoring in a single step.
"""

import threading

from adskipper._compat import xbmc
from adskipper.period import Period
from adskipper.fetcher import HttpManifestFetcher
from adskipper.parser import MpdParser
from adskipper.loader import ManifestLoader
from adskipper.detector import DurationAdDetector, CompositeAdDetector
from adskipper.notifier import KodiNotifier, SilentNotifier
from adskipper.seeker import KodiSeeker
from adskipper.monitor import PlaybackMonitor
from adskipper.skipper import AdSkipper


__version__ = "2.0.0"

__all__ = [
    "Period",
    "HttpManifestFetcher",
    "MpdParser",
    "ManifestLoader",
    "DurationAdDetector",
    "CompositeAdDetector",
    "KodiNotifier",
    "SilentNotifier",
    "KodiSeeker",
    "PlaybackMonitor",
    "AdSkipper",
    "start_ad_skipper",
]


def start_ad_skipper(
    stream_url:       str,
    label:            str   = "AdSkipper",
    min_duration:     float = 15.0,
    max_duration:     float = 45.0,
    extra_headers:    dict[str, str] | None = None,
    notify:           bool  = True,
    notify_threshold: int   = 3,
    seek_offset:      float = 0.5,
    timeout:          int   = 10,
    start_delay:      float = 1.0,
) -> tuple["AdSkipper", threading.Thread]:
    """
    Factory function that builds, wires, and starts the AdSkipper background daemon.

    Returns immediately with the running components.

    Parameters
    ----------
    stream_url : str
        The MPD manifest URL.
    label : str, optional
        Addon name shown in the notification toast.
    min_duration : float, optional
        Minimum duration in seconds to consider a period an ad. Default 15.0.
    max_duration : float, optional
        Maximum duration in seconds to consider a period an ad. Default 45.0.
    extra_headers : dict, optional
        Optional HTTP headers for fetching the manifest.
    notify : bool, optional
        If False, disables UI notifications entirely. Default True.
    notify_threshold : int, optional
        Stop showing notifications after this many skips. Default 3.
    seek_offset : float, optional
        Seconds added after the ad ends to seek to. Default 0.5.
    timeout : int, optional
        HTTP timeout in seconds for manifest fetch. Default 10.
    start_delay : float, optional
        Wait this many seconds before polling the player. Default 1.0.

    Returns
    -------
    tuple[AdSkipper, threading.Thread]
        The configured Skipper instance and its active daemon thread.
        Call `skipper.stop()` and `thread.join()` to shut down cleanly.
    """

    loader = ManifestLoader(
        url     = stream_url,
        fetcher = HttpManifestFetcher(headers=extra_headers, timeout=timeout),
        parser  = MpdParser(),
    )

    if notify:
        notifier = KodiNotifier(label=label, threshold=notify_threshold)
    else:
        notifier = SilentNotifier()

    skipper = AdSkipper(
        periods  = loader.get_periods(),
        detector = DurationAdDetector(min_duration, max_duration),
        seeker   = KodiSeeker(offset=seek_offset),
        notifier = notifier,
    )

    monitor = PlaybackMonitor(on_position=skipper.on_position, start_delay=start_delay)
    thread  = threading.Thread(target=monitor.start, daemon=True)
    thread.start()

    original_stop = skipper.stop

    def _stop_all() -> None:
        monitor.stop()
        original_stop()

    skipper.stop = _stop_all

    return skipper, thread
