"""
tests/test_monitor.py
~~~~~~~~~~~~~~~~~~~~~
Tests de PlaybackMonitor: stop con threading.Event, callback, y
comportamiento cuando el player no está reproduciendo.
"""

import time
import threading
from unittest.mock import MagicMock, patch

import adskipper.monitor as monitor_mod
from adskipper.monitor import PlaybackMonitor






def _start_monitor(monitor: PlaybackMonitor) -> threading.Thread:
    """Starts the monitor in a daemon thread and returns it."""
    t = threading.Thread(target=monitor.start, daemon=True)
    t.start()
    return t






class TestPlaybackMonitorStop:

    def test_stop_terminates_thread(self):
        """stop() must cause the thread to terminate within 1 second."""
        monitor = PlaybackMonitor(
            on_position=lambda p: None,
            start_delay=0.0,
            poll_interval=0.05,
        )
        t = _start_monitor(monitor)
        time.sleep(0.05)
        monitor.stop()
        t.join(timeout=1.0)
        assert not t.is_alive(), "El thread del monitor no terminó tras stop()"

    def test_stop_idempotent(self):
        """Calling stop() multiple times must not raise exceptions."""
        monitor = PlaybackMonitor(
            on_position=lambda p: None,
            start_delay=0.0,
        )
        t = _start_monitor(monitor)
        monitor.stop()
        monitor.stop()
        t.join(timeout=1.0)


class TestPlaybackMonitorCallback:

    def test_on_position_called_while_playing(self):
        """on_position is called with the player time when isPlaying=True."""
        positions = []
        mock_player = MagicMock()
        mock_player.isPlaying.return_value = True
        mock_player.getTime.return_value = 42.0

        monitor = PlaybackMonitor(
            on_position=positions.append,
            start_delay=0.0,
            poll_interval=0.02,
        )
        with patch.object(monitor_mod.xbmc, "Player", return_value=mock_player):
            t = _start_monitor(monitor)
            time.sleep(0.1)
            monitor.stop()
            t.join(timeout=1.0)

        assert len(positions) > 0, "on_position nunca fue llamado"
        assert all(p == 42.0 for p in positions)

    def test_on_position_not_called_when_not_playing(self):
        """on_position is NOT called if isPlaying=False."""
        positions = []
        mock_player = MagicMock()
        mock_player.isPlaying.return_value = False

        monitor = PlaybackMonitor(
            on_position=positions.append,
            start_delay=0.0,
            poll_interval=0.02,
        )
        with patch.object(monitor_mod.xbmc, "Player", return_value=mock_player):
            t = _start_monitor(monitor)
            time.sleep(0.1)
            monitor.stop()
            t.join(timeout=1.0)

        assert positions == [], f"on_position fue llamado {len(positions)} veces cuando no debería"

    def test_fresh_player_instance_per_poll(self):
        """xbmc.Player() must be instantiated in each loop cycle."""
        player_factory = MagicMock()
        player_factory.return_value.isPlaying.return_value = False

        monitor = PlaybackMonitor(
            on_position=lambda p: None,
            start_delay=0.0,
            poll_interval=0.02,
        )
        with patch.object(monitor_mod.xbmc, "Player", player_factory):
            t = _start_monitor(monitor)
            time.sleep(0.1)
            monitor.stop()
            t.join(timeout=1.0)


        assert player_factory.call_count > 1,\
            "xbmc.Player() debería llamarse en cada iteración del loop"

    def test_poll_error_does_not_crash_thread(self):
        """An exception in isPlaying must not terminate the thread prematurely."""
        mock_player = MagicMock()
        mock_player.isPlaying.side_effect = RuntimeError("player exploded")

        monitor = PlaybackMonitor(
            on_position=lambda p: None,
            start_delay=0.0,
            poll_interval=0.02,
        )
        with patch.object(monitor_mod.xbmc, "Player", return_value=mock_player):
            t = _start_monitor(monitor)
            time.sleep(0.1)
            assert t.is_alive(), "El thread murió por una excepción en el poll"
            monitor.stop()
            t.join(timeout=1.0)
