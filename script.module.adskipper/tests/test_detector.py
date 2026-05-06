"""
tests/test_detector.py
~~~~~~~~~~~~~~~~~~~~~~
Tests de DurationAdDetector y CompositeAdDetector.
"""

import pytest
from adskipper.period   import Period
from adskipper.detector import DurationAdDetector, CompositeAdDetector
from tests.conftest     import make_period


def _period(duration: float, id: str = "p") -> Period:
    return make_period(id=id, start=0.0, duration=duration)






class TestDurationAdDetector:

    def test_period_at_min_boundary_is_ad(self):
        det = DurationAdDetector(min_duration=15.0, max_duration=45.0)
        assert det.is_ad(_period(15.0)) is True

    def test_period_at_max_boundary_is_ad(self):
        det = DurationAdDetector(min_duration=15.0, max_duration=45.0)
        assert det.is_ad(_period(45.0)) is True

    def test_period_inside_range_is_ad(self):
        det = DurationAdDetector(min_duration=15.0, max_duration=45.0)
        assert det.is_ad(_period(30.0)) is True

    def test_period_below_min_is_not_ad(self):
        det = DurationAdDetector(min_duration=15.0, max_duration=45.0)
        assert det.is_ad(_period(14.9)) is False

    def test_period_above_max_is_not_ad(self):
        det = DurationAdDetector(min_duration=15.0, max_duration=45.0)
        assert det.is_ad(_period(45.1)) is False

    def test_zero_duration_not_ad_with_positive_min(self):
        det = DurationAdDetector(min_duration=15.0, max_duration=45.0)
        assert det.is_ad(_period(0.0)) is False

    def test_default_range(self):
        det = DurationAdDetector()
        assert det.min_duration == 15.0
        assert det.max_duration == 45.0

    def test_invalid_range_raises_value_error(self):
        with pytest.raises(ValueError):
            DurationAdDetector(min_duration=45.0, max_duration=15.0)

    def test_negative_min_raises_value_error(self):
        with pytest.raises(ValueError):
            DurationAdDetector(min_duration=-1.0, max_duration=30.0)

    def test_equal_min_max_exact_match_is_ad(self):
        det = DurationAdDetector(min_duration=30.0, max_duration=30.0)
        assert det.is_ad(_period(30.0)) is True
        assert det.is_ad(_period(30.001)) is False






class TestCompositeAdDetector:

    class _AlwaysAd:
        def is_ad(self, period: Period) -> bool:
            return True

    class _NeverAd:
        def is_ad(self, period: Period) -> bool:
            return False

    class _IdPrefixAd:
        def is_ad(self, period: Period) -> bool:
            return period.id.startswith("ad-")

    def _p(self, id: str = "p", duration: float = 30.0) -> Period:
        return _period(duration, id=id)



    def test_and_both_true_is_ad(self):
        det = CompositeAdDetector([self._AlwaysAd(), self._AlwaysAd()], require_all=True)
        assert det.is_ad(self._p()) is True

    def test_and_one_false_not_ad(self):
        det = CompositeAdDetector([self._AlwaysAd(), self._NeverAd()], require_all=True)
        assert det.is_ad(self._p()) is False

    def test_and_both_false_not_ad(self):
        det = CompositeAdDetector([self._NeverAd(), self._NeverAd()], require_all=True)
        assert det.is_ad(self._p()) is False



    def test_or_both_true_is_ad(self):
        det = CompositeAdDetector([self._AlwaysAd(), self._AlwaysAd()], require_all=False)
        assert det.is_ad(self._p()) is True

    def test_or_one_true_is_ad(self):
        det = CompositeAdDetector([self._AlwaysAd(), self._NeverAd()], require_all=False)
        assert det.is_ad(self._p()) is True

    def test_or_both_false_not_ad(self):
        det = CompositeAdDetector([self._NeverAd(), self._NeverAd()], require_all=False)
        assert det.is_ad(self._p()) is False



    def test_default_is_and(self):
        det = CompositeAdDetector([self._AlwaysAd(), self._NeverAd()])
        assert det.is_ad(self._p()) is False



    def test_duration_and_id_prefix_combo(self):
        det = CompositeAdDetector(
            [DurationAdDetector(15, 45), self._IdPrefixAd()],
            require_all=True,
        )
        assert det.is_ad(self._p(id="ad-1",     duration=30.0)) is True
        assert det.is_ad(self._p(id="content",  duration=30.0)) is False
        assert det.is_ad(self._p(id="ad-1",     duration=60.0)) is False
