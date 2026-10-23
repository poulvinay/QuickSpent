from kivy.utils import platform

from .formatting import money
from .ui import make_button, make_label, theme



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

    @staticmethod
    def _android_sdk_int():
        if platform != "android":
            return 0
        try:
            from jnius import autoclass

            return autoclass("android.os.Build$VERSION").SDK_INT
        except Exception:
            return 0

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

    def _system_dark_mode(self):
        activity, bridge = self._android_bridge()
        if not bridge:
            return False
        try:
            return bool(bridge.isNightMode(activity))
        except Exception:
            return False

    def apply_system_theme(self, refresh_colors=False):
        theme_style = "Dark" if self._system_dark_mode() else "Light"
        if self.theme_cls.theme_style != theme_style:
            # Changing the style also regenerates the colour scheme.
            self.theme_cls.theme_style = theme_style
        elif refresh_colors:
            # Material You colours follow the wallpaper, which may have changed.
            self.theme_cls.set_colors()

    def _consume_configuration_change(self, _dt):
        activity, bridge = self._android_bridge()
        if not bridge:
            return
        try:
            changed = self._quick_activity_class.consumeConfigurationChange()
        except Exception:
            return
        if changed:
            self.apply_system_theme(refresh_colors=True)

    def quick_access_popup(self):
        dialog, content, actions = self._dialog(
            "Quick access", "Choose where you want an Add money entry point."
        )
        entry_points = (
            ("Add home screen widget", "widgets-outline", "pinWidget"),
            ("Pin Add money shortcut", "pin-outline", "pinAddMoneyShortcut"),
            ("Lockscreen / heads-up notification", "bell-ring-outline", "showQuickAccessNotification"),
            ("Add Quick Settings tile", "toggle-switch-outline", "requestQuickSettingsTile"),
        )
        for label, icon, method_name in entry_points:
            content.add_widget(make_button(
                label,
                lambda *_, name=method_name: self._request_android_action(name),
                48,
                "secondary",
                icon=icon,
            ))
        content.add_widget(make_label(
            "Android controls lock screen and pop-up visibility. The bottom navigation bar cannot host app buttons; use the Quick Settings tile instead.",
            "Body", "small", theme().onSurfaceVariantColor,
        ))
        actions.add_widget(self._dialog_button("Done", lambda *_: dialog.dismiss()))
        dialog.open()

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

    def _settings_action(self, action):
        self.settings_menu.dismiss()
        if action == "category":
            self.add_category_popup()
        elif action == "shortcuts":
            self.quick_access_popup()
        elif action == "widgets":
            self._request_android_action("pinWidget")
