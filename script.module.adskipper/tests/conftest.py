"""
conftest.py
~~~~~~~~~~~
Fixtures y helpers compartidos entre todos los tests.
"""

import pytest
from unittest.mock import MagicMock, patch

from adskipper.period import Period






def make_period(
    id: str = "p1",
    start: float = 0.0,
    duration: float = 30.0,
) -> Period:
    """Creates a Period with end calculated from start + duration."""
    return Period(id=id, start=start, end=start + duration, duration=duration)


def make_ad_period(start: float = 10.0, duration: float = 30.0) -> Period:
    """Typical ad period (15-45 s) detected by DurationAdDetector."""
    return make_period(id="ad-1", start=start, duration=duration)


def make_content_period(start: float = 0.0, duration: float = 120.0) -> Period:
    """Content period (outside ad detection range)."""
    return make_period(id="content", start=start, duration=duration)






@pytest.fixture()
def mock_player():
    """Mock of xbmc.Player with isPlaying=True by default."""
    player = MagicMock()
    player.isPlaying.return_value = True
    player.getTime.return_value = 0.0
    return player


@pytest.fixture()
def patch_seeker_player(mock_player):
    """Patches xbmc.Player in the seeker namespace to intercept seekTime."""
    import adskipper.seeker as seeker_mod
    with patch.object(seeker_mod.xbmc, "Player", return_value=mock_player):
        yield mock_player


@pytest.fixture()
def patch_monitor_player(mock_player):
    """Patches xbmc.Player in the monitor namespace."""
    import adskipper.monitor as monitor_mod
    with patch.object(monitor_mod.xbmc, "Player", return_value=mock_player):
        yield mock_player
