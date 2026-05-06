"""
tests/test_skipper.py
~~~~~~~~~~~~~~~~~~~~~
Tests de AdSkipper: detección, skip único, contador, notificador y
manejo de seek fallido.
"""

from unittest.mock import MagicMock, call

import pytest
from adskipper.period   import Period
from adskipper.detector import DurationAdDetector
from adskipper.notifier import SilentNotifier
from adskipper.skipper  import AdSkipper
from tests.conftest     import make_ad_period, make_content_period, make_period






class RecordingSeeker:
    """Seeker that records all requested positions without touching the player."""
    def __init__(self):
        self.seeks: list[float] = []

    def seek_to(self, position: float) -> None:
        self.seeks.append(position)


class FailingSeeker:
    """Seeker that always raises."""
    def seek_to(self, position: float) -> None:
        raise RuntimeError("seek failed")


class RecordingNotifier:
    """Notifier that records received skips."""
    def __init__(self):
        self.calls: list[tuple] = []

    def notify(self, period: Period, skip_count: int) -> None:
        self.calls.append((period, skip_count))


def _make_skipper(
    periods=None,
    seeker=None,
    notifier=None,
    detector=None,
    lookahead: float = 2.0,
) -> tuple[AdSkipper, RecordingSeeker, RecordingNotifier]:
    seeker   = seeker   or RecordingSeeker()
    notifier = notifier or RecordingNotifier()
    detector = detector or DurationAdDetector()
    skipper  = AdSkipper(
        periods   = periods or [],
        detector  = detector,
        seeker    = seeker,
        notifier  = notifier,
        lookahead = lookahead,
    )
    return skipper, seeker, notifier






class TestOnPosition:

    def test_skip_triggered_at_ad_start(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad])
        skipper.on_position(10.0)
        assert seeker.seeks == [40.0]

    def test_skip_triggered_within_lookahead(self):
        """The position can be up to lookahead seconds before the start."""
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad], lookahead=2.0)
        skipper.on_position(9.0)
        assert seeker.seeks == [40.0]

    def test_no_skip_outside_lookahead(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad], lookahead=2.0)
        skipper.on_position(5.0)
        assert seeker.seeks == []

    def test_same_ad_not_skipped_twice(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad])
        skipper.on_position(10.0)
        skipper.on_position(10.0)
        assert len(seeker.seeks) == 1

    def test_content_period_not_skipped(self):
        content = make_content_period(start=0.0, duration=120.0)
        skipper, seeker, _ = _make_skipper(periods=[content])
        skipper.on_position(0.5)
        assert seeker.seeks == []

    def test_multiple_ads_all_skipped(self):
        ad1 = make_period(id="ad-1", start=10.0, duration=30.0)
        ad2 = make_period(id="ad-2", start=100.0, duration=15.0)
        skipper, seeker, _ = _make_skipper(periods=[ad1, ad2])
        skipper.on_position(10.0)
        skipper.on_position(100.0)
        assert seeker.seeks == [40.0, 115.0]

    def test_skip_count_increments(self):
        ad1 = make_period(id="ad-1", start=10.0,  duration=30.0)
        ad2 = make_period(id="ad-2", start=100.0, duration=20.0)
        skipper, _, _ = _make_skipper(periods=[ad1, ad2])
        assert skipper.skip_count == 0
        skipper.on_position(10.0)
        assert skipper.skip_count == 1
        skipper.on_position(100.0)
        assert skipper.skip_count == 2

    def test_notifier_called_after_seek(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, _, notifier = _make_skipper(periods=[ad])
        skipper.on_position(10.0)
        assert len(notifier.calls) == 1
        period_notified, count = notifier.calls[0]
        assert period_notified == ad
        assert count == 1






class TestOnPositionSeekFailed:

    def test_notifier_not_called_when_seek_fails(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        notifier = RecordingNotifier()
        skipper, _, _ = _make_skipper(
            periods=[ad],
            seeker=FailingSeeker(),
            notifier=notifier,
        )
        skipper.on_position(10.0)

        assert notifier.calls == []

    def test_skip_count_increments_even_if_seek_fails(self):
        """skip_count increments before the seek (current design)."""
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, _, _ = _make_skipper(periods=[ad], seeker=FailingSeeker())
        skipper.on_position(10.0)
        assert skipper.skip_count == 1






class TestOnPlaybackStarted:

    def test_skip_if_started_inside_ad(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad])
        skipper.on_playback_started(position=15.0)
        assert seeker.seeks == [40.0]

    def test_no_skip_if_started_before_ad(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad])
        skipper.on_playback_started(position=5.0)
        assert seeker.seeks == []

    def test_no_skip_if_started_after_ad(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, seeker, _ = _make_skipper(periods=[ad])
        skipper.on_playback_started(position=40.0)
        assert seeker.seeks == []

    def test_skip_count_incremented(self):
        ad = make_ad_period(start=10.0, duration=30.0)
        skipper, _, _ = _make_skipper(periods=[ad])
        skipper.on_playback_started(position=15.0)
        assert skipper.skip_count == 1
