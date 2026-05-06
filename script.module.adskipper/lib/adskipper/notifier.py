"""
adskipper.notifier
~~~~~~~~~~~~~~~~~~
Abstracts how the user is informed about a skipped ad.

Example — suppress all notifications::

    from adskipper.notifier import SilentNotifier
    from adskipper.skipper  import AdSkipper

    skipper = AdSkipper(ad_periods, notifier=SilentNotifier())
"""

from typing import Protocol

from adskipper._compat import xbmc, xbmcgui
from adskipper.period  import Period

_LOG = "[adskipper.notifier]"


class Notifier(Protocol):
    def notify(self, period: Period, skip_count: int) -> None:
        """Display (or log, or queue) a notification for the skipped *period*."""
        ...


class KodiNotifier:
    """
    Shows a Kodi notification toast (``xbmcgui.Dialog().notification``).

    Parameters
    ----------
    label : str
        Addon name or title used as the notification heading.
    threshold : int, optional
        Stop showing notifications after this many skips to avoid annoying
        the user on ad-heavy streams. Default 3.
    """

    def __init__(
        self,
        label:     str,
        threshold: int = 3,
    ) -> None:
        self._label     = label
        self._threshold = threshold

    def notify(self, period: Period, skip_count: int) -> None:
        if skip_count > self._threshold:
            return

        msg = f"Skipped ad ({period.duration:.0f}s)"
        if skip_count == self._threshold:
            msg += " (notifications disabled)"

        xbmc.log(f"{_LOG} Showing skip notification", xbmc.LOGDEBUG)
        xbmcgui.Dialog().notification(
            heading = self._label,
            message = msg,
            time    = 5000,
            sound   = False,
        )


class SilentNotifier:
    """No-op notifier. Satisfies the protocol without displaying anything."""

    def notify(self, period: Period, skip_count: int) -> None:
        pass
