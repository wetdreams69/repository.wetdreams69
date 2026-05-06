"""
tests/test_period.py
~~~~~~~~~~~~~~~~~~~~
Tests del modelo de dominio Period.
"""

import pytest
from adskipper.period import Period
from tests.conftest import make_period

class TestPeriodValidation:
    """Period.__post_init__ must validate input data."""

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError, match="duration must be >= 0"):
            Period(id="x", start=0.0, end=-10.0, duration=-10.0)

    def test_end_mismatch_raises(self):
        with pytest.raises(ValueError, match="end .* != start \+ duration"):
            Period(id="x", start=10.0, end=5.0, duration=30.0)

    def test_valid_period_creation(self):
        p = Period(id="x", start=10.0, end=40.0, duration=30.0)
        assert p.end == 40.0


class TestPeriodContains:
    """Period.contains() must return True if start <= pos < end."""

    def test_at_start_boundary_included(self):
        p = make_period(start=10.0, duration=10.0)
        assert p.contains(10.0) is True

    def test_inside_period(self):
        p = make_period(start=10.0, duration=10.0)
        assert p.contains(15.0) is True

    def test_at_end_boundary_excluded(self):
        p = make_period(start=10.0, duration=10.0)
        assert p.contains(20.0) is False

    def test_just_before_start(self):
        p = make_period(start=10.0, duration=10.0)
        assert p.contains(9.999) is False

    def test_just_after_end(self):
        p = make_period(start=10.0, duration=10.0)
        assert p.contains(20.001) is False

    def test_zero_duration_period(self):
        """A period of 0 duration contains no position."""
        p = Period(id="empty", start=5.0, end=5.0, duration=0.0)
        assert p.contains(5.0) is False


class TestPeriodImmutability:
    """Period must be immutable (frozen dataclass)."""

    def test_cannot_set_id(self):
        p = make_period()
        with pytest.raises((AttributeError, TypeError)):
            p.id = "hacked"  # type: ignore[misc]

    def test_cannot_set_start(self):
        p = make_period()
        with pytest.raises((AttributeError, TypeError)):
            p.start = 999.0  # type: ignore[misc]

    def test_is_hashable(self):
        """frozen=True guarantees that Period can be used in sets/dicts."""
        p = make_period()
        s = {p}
        assert p in s


class TestPeriodStr:
    """__str__ must include id, start, end and duration."""

    def test_str_contains_all_fields(self):
        p = Period(id="ad-1", start=5.0, end=35.0, duration=30.0)
        s = str(p)
        assert "ad-1" in s
        assert "5.0" in s
        assert "35.0" in s
        assert "30.0" in s
