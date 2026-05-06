"""
adskipper.monitor
~~~~~~~~~~~~~~~~~
Polls the Kodi player at a fixed interval and forwards the current
playback position to a callback.
"""

import threading
import time
from typing import Callable

from adskipper._compat import xbmc

_LOG = "[adskipper.monitor]"


class PlaybackMonitor:
    """
    Background worker that samples ``xbmc.Player().getTime()`` and feeds it
    to a consumer (usually the ``AdSkipper``).

    Parameters
    ----------
    on_position : Callable[[float], None]
        Function called on every poll tick with the current playback time.
    poll_interval : float, optional
        Seconds to wait between polls. Default 0.2 s (200 ms).
    start_delay : float, optional
        Initial sleep before polling begins. Default 1.0 s.
    """

    def __init__(
        self,
        on_position:   Callable[[float], None],
        poll_interval: float = 0.2,
        start_delay:   float = 1.0,
    ) -> None:
        self._on_position   = on_position
        self._poll_interval = poll_interval
        self._start_delay   = start_delay
        self._stop_event    = threading.Event()

    def start(self) -> None:
        """
        Run the polling loop synchronously until :meth:`stop` is called.

        Typically run inside a daemon thread.
        """
        self._stop_event.clear()
        xbmc.log(f"{_LOG} Polling started (interval={self._poll_interval}s)", xbmc.LOGINFO)

        time.sleep(self._start_delay)

        while not self._stop_event.is_set():
            try:
                player = xbmc.Player()
                if player.isPlaying():
                    pos = player.getTime()
                    self._on_position(pos)
            except Exception as exc:
                xbmc.log(f"{_LOG} Poll error: {exc}", xbmc.LOGDEBUG)

            self._stop_event.wait(self._poll_interval)

        xbmc.log(f"{_LOG} Polling stopped", xbmc.LOGINFO)

    def stop(self) -> None:
        """Signal the polling loop to exit on the next iteration."""
        self._stop_event.set()
