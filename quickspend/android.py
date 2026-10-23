from kivy.utils import platform

from .formatting import money
from .ui import left_label, make_button



class AndroidIntegrationMixin:
    def _android_bridge(self):
        if platform != "android":
            return None, None
        if self._android_bridge_class:
            return self._android_activity, self._android_bridge_class
        try:
            from jnius import autoclass

            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            bridge = autoclass("org.example.quickspend.QuickSpendBridge")
            self._quick_activity_class = autoclass("org.example.quickspend.QuickSpendActivity")
            self._android_activity = activity
            self._android_bridge_class = bridge
            return activity, bridge
        except Exception:
            return None, None

    def _update_android_widget(self, income, outgoing):
        activity, bridge = self._android_bridge()
        if bridge:
            bridge.updateWidget(activity, money(income, self.currency), money(outgoing, self.currency))

    def _consume_quick_entry_request(self, _dt):
        activity, bridge = self._android_bridge()
        if not bridge:
            return
        try:
            if self._quick_activity_class.consumeQuickEntryRequest():
                amount = str(self._quick_activity_class.consumeQuickEntryAmount())
                self.open_amount(initial=amount)
        except Exception:
            return

    def quick_access_popup(self):
        popup, content = self._dialog("Quick access", 510)
        content.add_widget(left_label(
            "Choose where you want an Add money entry point.", 44, 14
        ))
        content.add_widget(make_button(
            "Add home screen widget", lambda *_: self._request_android_action("pinWidget"),
            48, 15, "secondary",
        ))
        content.add_widget(make_button(
            "Pin Add money shortcut", lambda *_: self._request_android_action("pinAddMoneyShortcut"),
            48, 15, "secondary",
        ))
        content.add_widget(make_button(
            "Lockscreen / heads-up notification",
            lambda *_: self._request_android_action("showQuickAccessNotification"),
            48, 15, "secondary",
        ))
        content.add_widget(make_button(
            "Add Quick Settings tile", lambda *_: self._request_android_action("requestQuickSettingsTile"),
            48, 15, "secondary",
        ))
        content.add_widget(left_label(
            "Android controls lock screen and pop-up visibility. The bottom navigation bar cannot host app buttons; use the Quick Settings tile instead.",
            66, 12,
        ))
        content.add_widget(make_button("Done", lambda *_: popup.dismiss(), 44, 14))
        popup.open()

    def _request_android_action(self, method_name):
        activity, bridge = self._android_bridge()
        if not bridge:
            self.show_message("Android shortcut", "This shortcut is available in the Android app.")
            return
        try:
            result = getattr(bridge, method_name)(activity)
            if isinstance(result, bool) and not result:
                self.show_message("Shortcut unavailable", "This launcher or Android version does not support that shortcut.")
        except Exception as exc:
            self.show_message("Could not add shortcut", str(exc))

    def _settings_action(self, _dropdown, action):
        if action == "category":
            self.add_category_popup()
        elif action == "shortcuts":
            self.quick_access_popup()
        elif action == "widgets":
            self._request_android_action("pinWidget")
