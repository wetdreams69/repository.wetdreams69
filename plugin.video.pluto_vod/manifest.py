import re
import urllib.request
import xml.etree.ElementTree as ET
import xbmc

from constants import LOG_PREFIX_PLUTO


def get_periods_from_manifest(stream_url):
    try:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Fetching manifest for periods", xbmc.LOGINFO)
        req = urllib.request.Request(
            stream_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Origin": "https://pluto.tv",
                "Referer": "https://pluto.tv/",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            mpd_content = res.read().decode('utf-8')
        
        ns = {'mpd': 'urn:mpeg:dash:schema:mpd:2011'}
        root = ET.fromstring(mpd_content)
        periods = []
        current_time = 0
        
        for period in root.findall('.//mpd:Period', ns):
            period_id = period.get('id', '')
            duration_str = period.get('duration', '')
            duration = 0
            if duration_str:
                match = re.match(r'PT(\d+(?:\.\d+)?)S', duration_str)
                if match:
                    duration = float(match.group(1))
            
            periods.append({
                'start': current_time,
                'end': current_time + duration,
                'duration': duration,
                'id': period_id
            })
            xbmc.log(
                f"{LOG_PREFIX_PLUTO} Period: {period_id[:40]}... start={current_time:.1f}s, duration={duration:.1f}s",
                xbmc.LOGDEBUG
            )
            current_time += duration
        return periods
    except Exception as e:
        xbmc.log(f"{LOG_PREFIX_PLUTO} Error getting periods: {e}", xbmc.LOGERROR)
        return []


def filter_ad_periods(periods, min_duration=15, max_duration=45):
    return [p for p in periods if min_duration <= p['duration'] <= max_duration]
