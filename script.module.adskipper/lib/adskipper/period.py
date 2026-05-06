"""
adskipper.period
~~~~~~~~~~~~~~~~
Domain model for MPEG-DASH periods.

A period represents a continuous segment of playback with a known duration,
without pulling in HTTP, XML, or Kodi dependencies.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Period:
    """
    Immutable value object representing one MPEG-DASH ``<Period>`` element.

    Attributes
    ----------
    id : str
        Value of the ``Period/@id`` attribute (empty string when absent).
    start : float
        Absolute start time in seconds from the beginning of the stream.
    end : float
        Absolute end time in seconds (``start + duration``).
    duration : float
        Period length in seconds.
    """

    id:       str
    start:    float
    end:      float
    duration: float

    def __post_init__(self) -> None:
        if self.duration < 0:
            raise ValueError(f"duration must be >= 0, got {self.duration}")
        expected_end = round(self.start + self.duration, 9)
        if abs(self.end - expected_end) > 1e-6:
            raise ValueError(
                f"end ({self.end}) != start + duration ({expected_end})"
            )

    def contains(self, position: float) -> bool:
        """Return True if *position* falls inside this period."""
        return self.start <= position < self.end

    def __str__(self) -> str:
        return (
            f"Period(id={self.id!r}, "
            f"start={self.start:.1f}s, "
            f"end={self.end:.1f}s, "
            f"duration={self.duration:.1f}s)"
        )
