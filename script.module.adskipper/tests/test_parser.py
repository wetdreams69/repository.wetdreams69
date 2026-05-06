"""
tests/test_parser.py
~~~~~~~~~~~~~~~~~~~~
Tests de MpdParser y la función auxiliar _parse_iso_duration.
"""

import pytest
from adskipper.parser import MpdParser, _parse_iso_duration






def _mpd(*period_tags: str) -> str:
    """Build a minimal MPD with the given <Period>s."""
    inner = "\n  ".join(period_tags)
    return (
        '<?xml version="1.0"?>\n'
        '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011">\n'
        f"  {inner}\n"
        "</MPD>"
    )






class TestParseIsoDuration:

    @pytest.mark.parametrize("value,expected", [
        ("PT30S",     30.0),
        ("PT1M",      60.0),
        ("PT1H",    3600.0),
        ("PT1H30M",  5400.0),
        ("PT1M30S",    90.0),
        ("PT1H1M1S", 3661.0),
        ("PT0S",       0.0),
        ("PT1.5S",     1.5),
        ("PT30.25S",  30.25),
        ("",           0.0),
        ("INVALID",    0.0),
    ])
    def test_parse(self, value, expected):
        assert _parse_iso_duration(value) == pytest.approx(expected)






class TestMpdParserErrors:

    def test_malformed_xml_returns_empty(self):
        parser = MpdParser()
        result = parser.parse("<not valid xml>>>")
        assert result == []

    def test_empty_string_returns_empty(self):
        parser = MpdParser()
        result = parser.parse("")
        assert result == []

    def test_no_periods_returns_empty(self):
        mpd = _mpd()
        parser = MpdParser()
        assert parser.parse(mpd) == []






class TestMpdParserPeriods:

    def test_single_period(self):
        mpd = _mpd('<Period id="p1" duration="PT60S"/>')
        periods = MpdParser().parse(mpd)
        assert len(periods) == 1
        assert periods[0].id == "p1"
        assert periods[0].start == pytest.approx(0.0)
        assert periods[0].duration == pytest.approx(60.0)
        assert periods[0].end == pytest.approx(60.0)

    def test_sequential_periods_accumulate_time(self):
        """Without start attribute, each period begins where the previous ends."""
        mpd = _mpd(
            '<Period id="c1" duration="PT60S"/>',
            '<Period id="ad" duration="PT30S"/>',
            '<Period id="c2" duration="PT120S"/>',
        )
        periods = MpdParser().parse(mpd)
        assert len(periods) == 3
        assert periods[0].start == pytest.approx(0.0)
        assert periods[1].start == pytest.approx(60.0)
        assert periods[2].start == pytest.approx(90.0)

    def test_explicit_start_attribute_takes_priority(self):
        """Bug #4 fix: Period@start debe usarse si está presente."""
        mpd = _mpd(
            '<Period id="c1"  start="PT0S"  duration="PT60S"/>',
            '<Period id="ad"  start="PT60S" duration="PT30S"/>',
            '<Period id="c2"  start="PT90S" duration="PT120S"/>',
        )
        periods = MpdParser().parse(mpd)
        assert periods[0].start == pytest.approx(0.0)
        assert periods[1].start == pytest.approx(60.0)
        assert periods[2].start == pytest.approx(90.0)

    def test_explicit_start_with_gap(self):
        """A jump in starts (e.g. SSAI stream with gap) is preserved."""
        mpd = _mpd(
            '<Period id="pre"     start="PT0S"   duration="PT10S"/>',
            '<Period id="ad-slot" start="PT10S"  duration="PT30S"/>',

            '<Period id="content" start="PT50S"  duration="PT200S"/>',
        )
        periods = MpdParser().parse(mpd)
        assert periods[2].start == pytest.approx(50.0)
        assert periods[2].end   == pytest.approx(250.0)

    def test_period_without_id_gets_empty_string(self):
        mpd = _mpd('<Period duration="PT30S"/>')
        periods = MpdParser().parse(mpd)
        assert periods[0].id == ""

    def test_period_without_duration_gets_zero(self):
        mpd = _mpd('<Period id="marker"/>')
        periods = MpdParser().parse(mpd)
        assert periods[0].duration == pytest.approx(0.0)

    def test_order_preserved(self):
        mpd = _mpd(
            '<Period id="a" duration="PT10S"/>',
            '<Period id="b" duration="PT20S"/>',
            '<Period id="c" duration="PT30S"/>',
        )
        periods = MpdParser().parse(mpd)
        assert [p.id for p in periods] == ["a", "b", "c"]
