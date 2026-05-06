"""
tests/test_notifier.py
~~~~~~~~~~~~~~~~~~~~~~
Tests de KodiNotifier (threshold, llamadas a xbmcgui) y SilentNotifier.
"""

from unittest.mock import MagicMock, patch

import adskipper.notifier as notifier_mod
from adskipper.notifier import KodiNotifier, SilentNotifier
from tests.conftest     import make_ad_period






class TestSilentNotifier:

    def test_notify_does_nothing(self):
        """SilentNotifier.notify() must not raise or call anything."""
        n = SilentNotifier()
        period = make_ad_period()
        n.notify(period, skip_count=1)

    def test_multiple_calls_no_error(self):
        n = SilentNotifier()
        period = make_ad_period()
        for i in range(10):
            n.notify(period, skip_count=i)






class TestKodiNotifier:

    def _make_mock_dialog(self):
        mock_dialog_instance = MagicMock()
        mock_dialog_cls      = MagicMock(return_value=mock_dialog_instance)
        return mock_dialog_cls, mock_dialog_instance

    def test_notification_shown_within_threshold(self):
        dialog_cls, dialog_inst = self._make_mock_dialog()
        with patch.object(notifier_mod.xbmcgui, "Dialog", dialog_cls):
            n = KodiNotifier(label="TestAddon", threshold=3)
            n.notify(make_ad_period(), skip_count=1)
        dialog_inst.notification.assert_called_once()

    def test_notification_shown_at_threshold(self):
        dialog_cls, dialog_inst = self._make_mock_dialog()
        with patch.object(notifier_mod.xbmcgui, "Dialog", dialog_cls):
            n = KodiNotifier(label="TestAddon", threshold=3)
            n.notify(make_ad_period(), skip_count=3)
        dialog_inst.notification.assert_called_once()

    def test_notification_suppressed_above_threshold(self):
        dialog_cls, dialog_inst = self._make_mock_dialog()
        with patch.object(notifier_mod.xbmcgui, "Dialog", dialog_cls):
            n = KodiNotifier(label="TestAddon", threshold=3)
            n.notify(make_ad_period(), skip_count=4)
        dialog_inst.notification.assert_not_called()

    def test_notification_message_contains_duration(self):
        """The message must mention the ad duration."""
        dialog_cls, dialog_inst = self._make_mock_dialog()
        period = make_ad_period(duration=30.0)
        with patch.object(notifier_mod.xbmcgui, "Dialog", dialog_cls):
            n = KodiNotifier(label="Pluto", threshold=5)
            n.notify(period, skip_count=1)
        _, kwargs = dialog_inst.notification.call_args
        assert any("30" in str(v) for v in kwargs.values()),\
            "The notification message should mention the ad duration"

    def test_label_used_as_heading(self):
        dialog_cls, dialog_inst = self._make_mock_dialog()
        with patch.object(notifier_mod.xbmcgui, "Dialog", dialog_cls):
            n = KodiNotifier(label="MyAddon", threshold=5)
            n.notify(make_ad_period(), skip_count=1)
        _, kwargs = dialog_inst.notification.call_args
        assert "MyAddon" == kwargs.get("heading")

    def test_threshold_zero_never_notifies(self):
        dialog_cls, dialog_inst = self._make_mock_dialog()
        with patch.object(notifier_mod.xbmcgui, "Dialog", dialog_cls):
            n = KodiNotifier(label="X", threshold=0)
            n.notify(make_ad_period(), skip_count=1)
        dialog_inst.notification.assert_not_called()
