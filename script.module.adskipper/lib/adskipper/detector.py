"""
adskipper.detector
~~~~~~~~~~~~~~~~~~
Strategy interfaces and concrete implementations for deciding which
periods are ads.

Built-in strategies
-------------------
``DurationAdDetector``
    Flags periods whose duration falls within a configurable range.
    Works well for streams that use fixed-length pre-roll/mid-roll slots.

``CompositeAdDetector``
    Combines multiple detectors with AND or OR logic, letting you stack
    heuristics without modifying existing ones.

Custom strategy example::

    from adskipper.detector import AdDetector
    from adskipper.period   import Period

    class IdPrefixAdDetector:
        \"\"\"Flag periods whose id starts with 'ad-'.\"\"\"
        def is_ad(self, period: Period) -> bool:
            return period.id.startswith("ad-")
"""

from typing import Protocol

from adskipper.period import Period


class AdDetector(Protocol):
    """
    Structural interface for ad-detection strategies.
    """

    def is_ad(self, period: Period) -> bool:
        """Return True if *period* should be treated as an advertisement."""
        ...


class DurationAdDetector:
    """
    Flags periods whose duration falls within ``[min_duration, max_duration]``.

    Parameters
    ----------
    min_duration : float, optional
        Minimum duration in seconds (inclusive). Default 15.0.
    max_duration : float, optional
        Maximum duration in seconds (inclusive). Default 45.0.
    """

    def __init__(
        self,
        min_duration: float = 15.0,
        max_duration: float = 45.0,
    ) -> None:
        if min_duration < 0:
            raise ValueError("min_duration must be >= 0")
        if min_duration > max_duration:
            raise ValueError("min_duration cannot be > max_duration")
        self.min_duration = min_duration
        self.max_duration = max_duration

    def is_ad(self, period: Period) -> bool:
        return self.min_duration <= period.duration <= self.max_duration


class CompositeAdDetector:
    """
    Combines multiple :class:`AdDetector` strategies.

    Parameters
    ----------
    detectors : list[AdDetector]
        Strategies to evaluate.
    require_all : bool, optional
        If True, *all* detectors must agree (AND).
        If False, *any* detector suffices (OR). Default True.

    Example — require both duration AND id-prefix match::

        detector = CompositeAdDetector(
            [DurationAdDetector(15, 45), IdPrefixAdDetector()],
            require_all=True,
        )
    """

    def __init__(
        self,
        detectors: list[AdDetector],
        require_all: bool = True,
    ) -> None:
        self._detectors  = detectors
        self._require_all = require_all

    def is_ad(self, period: Period) -> bool:
        if self._require_all:
            return all(d.is_ad(period) for d in self._detectors)
        else:
            return any(d.is_ad(period) for d in self._detectors)
