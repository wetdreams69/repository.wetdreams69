"""
adskipper.seeker
~~~~~~~~~~~~~~~~
Performs a seek on the Kodi player.
"""

import time
from typing import Protocol

from adskipper._compat import xbmc

_LOG            = "[adskipper.seeker]"
_POST_SEEK_WAIT = 0.3


class Seeker(Protocol):
    def seek_to(self, position: float) -> None:
        """Seek the player to *position* seconds."""
        ...


class KodiSeeker:
    """
    Seeks ``xbmc.Player`` to an absolute position.

    Parameters
    ----------
    offset : float, optional
        Extra seconds added to the requested position before seeking.
        Useful to land a few frames past an ad boundary. Default 0.5 s.
    post_seek_wait : float, optional
        Seconds to sleep after ``seekTime()`` to let the player settle.
        Default 0.3 s.
    """

    def __init__(
        self,
        offset:         float = 0.5,
        post_seek_wait: float = _POST_SEEK_WAIT,
    ) -> None:
        self._offset         = offset
        self._post_seek_wait = post_seek_wait

    def seek_to(self, position: float) -> None:
        target = position + self._offset
        xbmc.log(f"{_LOG} Seeking to {target:.1f}s", xbmc.LOGDEBUG)
        try:
            xbmc.Player().seekTime(target)
            time.sleep(self._post_seek_wait)
        except Exception as exc:
            xbmc.log(f"{_LOG} Seek failed: {exc}", xbmc.LOGERROR)
            raise
