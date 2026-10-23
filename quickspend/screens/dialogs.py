from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.appbar import (
    MDActionTopAppBarButton,
    MDTopAppBar,
    MDTopAppBarTitle,
    MDTopAppBarTrailingButtonContainer,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)
from kivymd.uix.menu import MDDropdownMenu

from ..ui import make_button


class DialogMixin:
    def _page(self, screen, title, settings=False):
        """Add a top app bar to ``screen`` and return the content column below it."""
        app_bar = MDTopAppBar(MDTopAppBarTitle(text=title), type="small")
        if settings:
            self.settings_button = MDActionTopAppBarButton(
                icon="dots-vertical",
                on_release=lambda *_: self.open_settings_menu(),
            )
            app_bar.add_widget(MDTopAppBarTrailingButtonContainer(self.settings_button))
        layout = MDBoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(8), dp(16), dp(16)),
            spacing=dp(12),
        )
        screen.add_widget(MDBoxLayout(app_bar, layout, orientation="vertical"))
        return layout

    def open_settings_menu(self):
        actions = (
            ("Add category", "shape-plus-outline", "category"),
            ("Shortcuts", "gesture-tap-button", "shortcuts"),
            ("Widgets", "widgets-outline", "widgets"),
        )
        self.settings_menu = MDDropdownMenu(
            caller=self.settings_button,
            items=[
                {
                    "text": label,
                    "leading_icon": icon,
                    "on_release": lambda value=action: self._settings_action(value),
                }
                for label, icon, action in actions
            ],
        )
        self.settings_menu.open()

    def _dialog(self, title, text="", auto_dismiss=True):
        """Return a Material dialog plus its content and action containers."""
        content = MDDialogContentContainer(orientation="vertical", spacing=dp(12))
        actions = MDDialogButtonContainer(Widget(), spacing=dp(8))
        parts = [MDDialogHeadlineText(text=title)]
        if text:
            parts.append(MDDialogSupportingText(text=text))
        dialog = MDDialog(*parts, content, actions, auto_dismiss=auto_dismiss)
        return dialog, content, actions

    @staticmethod
    def _dialog_button(text, callback, variant="text"):
        return make_button(text, callback, 40, variant, full_width=False)

    def _dismiss_overlay(self):
        """Close the front-most dialog, menu or picker. They don't handle Back."""
        for widget in Window.children:
            if widget is self.root or not hasattr(widget, "dismiss"):
                continue
            # Closed overlays stay in the window while their hide animation runs.
            if not getattr(widget, "_is_open", True) or not getattr(widget, "is_open", True):
                continue
            for child in widget.walk():
                # A focused field would keep taking key presses once hidden.
                if getattr(child, "focus", False):
                    child.focus = False
            widget.dismiss()
            return True
        return False

    def show_message(self, title, message):
        dialog, _content, actions = self._dialog(title, message)
        actions.add_widget(self._dialog_button("OK", lambda *_: dialog.dismiss()))
        dialog.open()
