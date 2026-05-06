"""
adskipper._compat
~~~~~~~~~~~~~~~~~
Minimal stubs for xbmc and xbmcgui to allow importing and
unit testing the module outside of Kodi.

If the module is loaded inside Kodi, it uses the real libraries.
"""

try:
    import xbmc
    import xbmcgui
except ImportError:
    import logging as _logging

    class _PlayerStub:
        def isPlaying(self) -> bool:
            return False

        def getTime(self) -> float:
            return 0.0

        def seekTime(self, time: float) -> None:
            pass

    class _XbmcStub:
        LOGDEBUG   = 10
        LOGINFO    = 20
        LOGWARNING = 30
        LOGERROR   = 40

        Player = _PlayerStub

        def log(self, msg: str, level: int = 20) -> None:
            _logging.log(level, "[kodi-stub] %s", msg)

    class _DialogStub:
        def notification(
            self, heading: str, message: str, time: int = 5000, sound: bool = True
        ) -> None:
            _logging.info("[kodi-toast] %s: %s", heading, message)

    class _XbmcguiStub:
        Dialog = _DialogStub

    xbmc    = _XbmcStub()
    xbmcgui = _XbmcguiStub()
