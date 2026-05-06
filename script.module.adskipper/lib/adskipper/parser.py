"""
adskipper.parser
~~~~~~~~~~~~~~~~
Turns raw MPD XML into an ordered list of ``Period`` objects.
"""

import re
import xml.etree.ElementTree as ET

from adskipper.period import Period


def _parse_iso_duration(duration_str: str) -> float:
    """Convert an ISO 8601 duration string to total seconds."""
    if not duration_str:
        return 0.0

    pattern = r"^PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?$"
    match = re.match(pattern, duration_str)
    if not match:
        return 0.0

    hours   = float(match.group(1)) if match.group(1) else 0.0
    minutes = float(match.group(2)) if match.group(2) else 0.0
    seconds = float(match.group(3)) if match.group(3) else 0.0

    return (hours * 3600) + (minutes * 60) + seconds


class MpdParser:
    """
    Parses MPEG-DASH XML manifests.
    """

    def parse(self, xml_string: str) -> list[Period]:
        """
        Parse *xml_string* and return all extracted periods in order.

        Returns an empty list if the XML is malformed or no periods are found.
        """
        if not xml_string.strip():
            return []

        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError:
            return []

        return self._extract_periods(root)

    def _extract_periods(self, root: ET.Element) -> list[Period]:
        ns = {"mpd": "urn:mpeg:dash:schema:mpd:2011"}
        periods: list[Period] = []

        current_time = 0.0

        for p_elem in root.findall(".//mpd:Period", ns) or root.findall(".//Period"):
            p_id = p_elem.get("id", "")
            
            start_attr = p_elem.get("start")
            if start_attr:
                current_time = _parse_iso_duration(start_attr)
            
            duration_attr = p_elem.get("duration", "")
            duration = _parse_iso_duration(duration_attr)
            
            period = Period(
                id=p_id,
                start=current_time,
                end=current_time + duration,
                duration=duration,
            )
            periods.append(period)

            current_time += duration

        return periods
