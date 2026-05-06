"""
adskipper.skipper
~~~~~~~~~~~~~~~~~
Orchestrates ad detection, seeking, and notification.

``AdSkipper`` delegates entirely to the abstractions it receives.
Its only responsibility is coordinating the other components.
"""

import threading

from adskipper._compat import xbmc

from adskipper.period   import Period
from adskipper.detector import AdDetector
from adskipper.notifier import Notifier
from adskipper.seeker   import Seeker

_LOG       = "[adskipper.skipper]"
_LOOKAHEAD = 2.0


class AdSkipper:
    """
    Receives playback positions from PlaybackMonitor and skips ad periods
    by coordinating AdDetector, Seeker, and Notifier.

    Parameters
    ----------
    periods : list[Period]
        All periods from the manifest (not pre-filtered).
        AdSkipper calls detector.is_ad() at runtime so the same period list
        can be reused with different detectors.
    detector : AdDetector
        Strategy that classifies a period as an ad or not.
    seeker : Seeker
        Performs the actual seek on the player.
    notifier : Notifier
        Informs the user when an ad is skipped.
    lookahead : float, optional
        Seconds before a period start at which the skip is triggered. Default 2.0 s.
    """

    def __init__(
        self,
        periods:   list[Period],
        detector:  AdDetector,
        seeker:    Seeker,
        notifier:  Notifier,
        lookahead: float = _LOOKAHEAD,
    ) -> None:
        self._periods     = periods
        self._detector    = detector
        self._seeker      = seeker
        self._notifier    = notifier
        self._lookahead   = lookahead

        self._skipped:    set[float] = set()
        self._skip_count: int        = 0
        self._lock                   = threading.Lock()

        self._log_ad_slots()

    @property
    def skip_count(self) -> int:
        """Total number of ads skipped in this session."""
        return self._skip_count

    def stop(self) -> None:
        """Optional hook for the factory or addon to stop external resources."""
        pass

    def on_position(self, position: float) -> None:
        """
        Entry point called by PlaybackMonitor on every poll tick.

        Checks whether position is near the start of any unskipped ad period
        and triggers a skip if so.
        """
        for period in self._periods:
            if not self._detector.is_ad(period):
                continue
            if abs(position - period.start) < self._lookahead:
                with self._lock:
                    if period.start in self._skipped:
                        continue
                    self._execute_skip(period)
                break

    def on_playback_started(self, position: float) -> None:
        """
        Call once after the player starts to handle streams that begin
        inside an ad (e.g. live channels with mid-stream join).
        """
        for period in self._periods:
            if self._detector.is_ad(period) and period.contains(position):
                xbmc.log(
                    f"{_LOG} Playback started inside ad at {position:.1f}s ({period})",
                    xbmc.LOGINFO,
                )
                with self._lock:
                    self._execute_skip(period)
                break

    def _execute_skip(self, period: Period) -> None:
        self._skipped.add(period.start)
        self._skip_count += 1

        xbmc.log(
            f"{_LOG} Skipping ad #{self._skip_count} "
            f"({period.duration:.0f}s) end={period.end:.1f}s",
            xbmc.LOGINFO,
        )

        try:
            self._seeker.seek_to(period.end)
        except Exception as exc:
            xbmc.log(f"{_LOG} Seek error: {exc}", xbmc.LOGERROR)
            return

        self._notifier.notify(period, self._skip_count)

    def _log_ad_slots(self) -> None:
        ad_periods = [p for p in self._periods if self._detector.is_ad(p)]
        xbmc.log(
            f"{_LOG} {len(ad_periods)} ad slot(s) out of {len(self._periods)} period(s)",
            xbmc.LOGINFO,
        )
        for p in ad_periods:
            xbmc.log(f"{_LOG}   {p}", xbmc.LOGDEBUG)
