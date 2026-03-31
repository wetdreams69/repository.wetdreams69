import time
import xbmc
import xbmcgui

from constants import LOG_PREFIX_AD_SKIP


class AdSkipper:
    def __init__(self, ad_periods):
        self.player = xbmc.Player()
        self.ad_periods = ad_periods
        self.skip_count = 0
        self.monitoring = False
        self._skipped_ads = set()
        for ad in ad_periods:
            xbmc.log(
                f"{LOG_PREFIX_AD_SKIP} Ad detected: {ad['start']:.1f}s -> {ad['end']:.1f}s "
                f"(duration: {ad['duration']:.1f}s)",
                xbmc.LOGINFO
            )
        
    def start_monitoring(self):
        self.monitoring = True
        xbmc.log(
            f"{LOG_PREFIX_AD_SKIP} Started monitoring - {len(self.ad_periods)} ads detected",
            xbmc.LOGINFO
        )
        self.check_initial_position()
        while self.monitoring:
            try:
                if self.player.isPlaying():
                    self.check_and_skip()
                time.sleep(0.2)
            except Exception as e:
                xbmc.log(f"{LOG_PREFIX_AD_SKIP} Error: {e}", xbmc.LOGDEBUG)
    
    def check_initial_position(self):
        try:
            time.sleep(1)
            if self.player.isPlaying():
                current_pos = self.player.getTime()
                xbmc.log(f"{LOG_PREFIX_AD_SKIP} Initial position: {current_pos:.1f}s", xbmc.LOGINFO)
                for ad in self.ad_periods:
                    if ad['start'] <= current_pos < ad['end']:
                        xbmc.log(
                            f"{LOG_PREFIX_AD_SKIP} 🚫 Started inside ad at {current_pos:.1f}s "
                            f"(ad: {ad['start']:.1f}s-{ad['end']:.1f}s)",
                            xbmc.LOGINFO
                        )
                        self.skip_ad(ad)
                        break
        except Exception as e:
            xbmc.log(f"{LOG_PREFIX_AD_SKIP} Initial check error: {e}", xbmc.LOGDEBUG)
    
    def check_and_skip(self):
        try:
            current_pos = self.player.getTime()
            for ad in self.ad_periods:
                if abs(current_pos - ad['start']) < 2.0:
                    if ad['start'] not in self._skipped_ads:
                        self.skip_ad(ad)
                        break
        except Exception as e:
            xbmc.log(f"{LOG_PREFIX_AD_SKIP} Check error: {e}", xbmc.LOGDEBUG)
    
    def skip_ad(self, ad):
        try:
            self._skipped_ads.add(ad['start'])
            self.skip_count += 1
            xbmc.log(
                f"{LOG_PREFIX_AD_SKIP} 🚫 Skipping ad #{self.skip_count} ({ad['duration']:.0f}s)",
                xbmc.LOGINFO
            )
            if self.skip_count <= 3:
                dialog = xbmcgui.Dialog()
                dialog.notification(
                    "Pluto TV", 
                    f"Skipping ad ({ad['duration']:.0f}s)", 
                    xbmcgui.NOTIFICATION_INFO, 
                    2000
                )
            jump_to = ad['end'] + 0.5
            self.player.seekTime(jump_to)
            time.sleep(0.3)
        except Exception as e:
            xbmc.log(f"{LOG_PREFIX_AD_SKIP} Skip error: {e}", xbmc.LOGERROR)
    
    def stop(self):
        self.monitoring = False
