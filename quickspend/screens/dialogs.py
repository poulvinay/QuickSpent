from kivy.graphics import (
    Color,
    Ellipse,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Rotate,
    RoundedRectangle,
)
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup

from ..ui import INK, PAPER, TEAL, Surface, left_label, make_button


class _SettingsButton(Button):
    """A font-independent settings cog drawn with Kivy canvas shapes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(*INK)
            self._teeth = []
            for angle in range(0, 360, 45):
                PushMatrix()
                rotation = Rotate(angle=angle)
                tooth = Rectangle(size=(dp(6), dp(5)))
                PopMatrix()
                self._teeth.append((rotation, tooth))
            self._cog = Ellipse()
            Color(0.88, 0.92, 0.90, 1)
            self._center_hole = Ellipse()
        self.bind(pos=self._sync_glyph, size=self._sync_glyph)
        self._sync_glyph()

    def _sync_glyph(self, *_args):
        cx, cy = self.center
        self._cog.pos = (cx - dp(8), cy - dp(8))
        self._cog.size = (dp(16), dp(16))
        self._center_hole.pos = (cx - dp(3), cy - dp(3))
        self._center_hole.size = (dp(6), dp(6))
        for rotation, tooth in self._teeth:
            rotation.origin = (cx, cy)
            tooth.pos = (cx - dp(3), cy + dp(6))


class DialogMixin:
    def _page(self, title, settings=False):
        layout = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(10))
        with layout.canvas.before:
            Color(0.96, 0.97, 0.95, 1)
            layout._background = RoundedRectangle(pos=layout.pos, size=layout.size, radius=[dp(0)])
        layout.bind(pos=lambda widget, value: setattr(widget._background, "pos", value))
        layout.bind(size=lambda widget, value: setattr(widget._background, "size", value))
        if settings:
            header = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))
            header.add_widget(left_label(title, 54, 25, True))
            self.settings_dropdown = DropDown(
                auto_width=False,
                width=dp(206),
                max_height=dp(172),
            )
            self.settings_dropdown.container.padding = dp(8)
            self.settings_dropdown.container.spacing = dp(6)
            self.settings_dropdown.bind(on_select=self._settings_action)
            actions = (
                ("Add Category", "category"),
                ("Shortcuts", "shortcuts"),
                ("Widgets", "widgets"),
            )
            for label, action in actions:
                item = make_button(label, height=48, font_size=15, variant="secondary")
                item.size_hint_x = None
                item.width = dp(190)
                item.bind(
                    on_release=lambda button, value=action: self.settings_dropdown.select(value)
                )
                self.settings_dropdown.add_widget(item)
            settings_button = _SettingsButton(
                size_hint_y=None,
                height=dp(48),
                background_normal="",
                background_down="",
                background_color=(0, 0, 0, 0),
            )
            with settings_button.canvas.before:
                Color(0.88, 0.92, 0.90, 1)
                settings_button._surface = RoundedRectangle(
                    pos=settings_button.pos,
                    size=settings_button.size,
                    radius=[dp(14)],
                )
            settings_button.bind(
                pos=lambda widget, value: setattr(widget._surface, "pos", value),
                size=lambda widget, value: setattr(widget._surface, "size", value),
            )
            settings_button.size_hint_x = None
            settings_button.width = dp(52)
            settings_button.bind(on_release=lambda button: self.settings_dropdown.open(button))
            header.add_widget(settings_button)
            layout.add_widget(header)
        else:
            layout.add_widget(left_label(title, 54, 25, True))
        return layout

    def _dialog(self, title, height, auto_dismiss=True):
        body = Surface(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10),
            fill=(1, 1, 1, 1),
            radius=20,
        )
        popup = Popup(
            title=title,
            content=body,
            size_hint=(0.92, None),
            height=dp(height),
            auto_dismiss=auto_dismiss,
            background="",
            background_color=PAPER,
            title_color=INK,
            title_align="center",
            separator_color=TEAL,
            title_size=sp(18),
        )
        return popup, body

    def show_message(self, title, message):
        popup, content = self._dialog(title, 200)
        content.add_widget(left_label(message, 70, 15))
        content.add_widget(make_button("OK", lambda *_: popup.dismiss(), 48, 15))
        popup.open()
