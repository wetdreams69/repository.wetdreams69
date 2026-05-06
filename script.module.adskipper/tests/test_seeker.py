"""
tests/test_seeker.py
~~~~~~~~~~~~~~~~~~~~
Tests de KodiSeeker: offset, llamada a seekTime y propagación de errores.
"""

import pytest
from unittest.mock import MagicMock, patch, call

import adskipper.seeker as seeker_mod
from adskipper.seeker import KodiSeeker






def _make_seeker(offset: float = 0.5, post_seek_wait: float = 0.0):
    """Creates a KodiSeeker with post_seek_wait=0 to not slow down tests."""
    return KodiSeeker(offset=offset, post_seek_wait=post_seek_wait)






class TestKodiSeeker:

    def test_offset_applied_to_seektime(self):
        """seek_to(10) with offset=0.5 must call seekTime(10.5)."""
        mock_player = MagicMock()
        with patch.object(seeker_mod.xbmc, "Player", return_value=mock_player):
            seeker = _make_seeker(offset=0.5)
            seeker.seek_to(10.0)
        mock_player.seekTime.assert_called_once_with(pytest.approx(10.5))

    def test_zero_offset(self):
        """With offset=0, seekTime must receive exactly the given position."""
        mock_player = MagicMock()
        with patch.object(seeker_mod.xbmc, "Player", return_value=mock_player):
            seeker = _make_seeker(offset=0.0)
            seeker.seek_to(42.0)
        mock_player.seekTime.assert_called_once_with(pytest.approx(42.0))

    def test_negative_offset(self):
        """A negative offset advances the landing point."""
        mock_player = MagicMock()
        with patch.object(seeker_mod.xbmc, "Player", return_value=mock_player):
            seeker = _make_seeker(offset=-1.0)
            seeker.seek_to(20.0)
        mock_player.seekTime.assert_called_once_with(pytest.approx(19.0))

    def test_fresh_player_instance_per_seek(self):
        """xbmc.Player() must be called in seek_to, not saved in __init__."""
        player_factory = MagicMock(return_value=MagicMock())
        with patch.object(seeker_mod.xbmc, "Player", player_factory):
            seeker = _make_seeker()
            seeker.seek_to(5.0)
            seeker.seek_to(10.0)

        assert player_factory.call_count == 2

    def test_seek_error_propagates(self):
        """If seekTime raises, the exception must propagate up."""
        mock_player = MagicMock()
        mock_player.seekTime.side_effect = RuntimeError("player not ready")
        with patch.object(seeker_mod.xbmc, "Player", return_value=mock_player):
            seeker = _make_seeker()
            with pytest.raises(RuntimeError, match="player not ready"):
                seeker.seek_to(10.0)

    def test_seek_to_float_position(self):
        """Accepts float positions with decimals."""
        mock_player = MagicMock()
        with patch.object(seeker_mod.xbmc, "Player", return_value=mock_player):
            seeker = _make_seeker(offset=0.0)
            seeker.seek_to(123.456)
        mock_player.seekTime.assert_called_once_with(pytest.approx(123.456))
