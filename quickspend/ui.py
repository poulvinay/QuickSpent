from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

INK = (0.10, 0.16, 0.18, 1)
MUTED = (0.36, 0.43, 0.44, 1)
TEAL = (0.12, 0.43, 0.42, 1)
PAPER = (0.96, 0.97, 0.95, 1)
GREEN = (0.12, 0.48, 0.29, 1)
GREEN_PALE = (0.89, 0.96, 0.91, 1)
RED = (0.72, 0.20, 0.18, 1)
RED_PALE = (1.0, 0.92, 0.91, 1)


class Surface(BoxLayout):
    def __init__(self, fill=(1, 1, 1, 1), radius=18, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*fill)
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._sync_shape, size=self._sync_shape)

    def _sync_shape(self, *_):
        self.shape.pos = self.pos
        self.shape.size = self.size


def make_button(text, callback=None, height=52, font_size=17, variant="primary"):
    styles = {
        "primary": (TEAL, (1, 1, 1, 1)),
        "secondary": ((0.88, 0.92, 0.90, 1), INK),
        "danger": (RED, (1, 1, 1, 1)),
        "income": (GREEN, (1, 1, 1, 1)),
        "expense": (RED, (1, 1, 1, 1)),
    }
    fill, text_color = styles[variant]
    button = Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        font_size=sp(font_size),
        color=text_color,
        background_normal="",
        background_down="",
        background_color=(0, 0, 0, 0),
    )
    with button.canvas.before:
        Color(*fill)
        button._surface = RoundedRectangle(pos=button.pos, size=button.size, radius=[dp(14)])
    button.bind(pos=lambda widget, value: setattr(widget._surface, "pos", value))
    button.bind(size=lambda widget, value: setattr(widget._surface, "size", value))
    if callback:
        button.bind(on_release=callback)
    return button


def make_field(hint, text="", numeric=False, height=52, font_size=17, halign="left"):
    return TextInput(
        text=text,
        hint_text=hint,
        multiline=False,
        input_filter="float" if numeric else None,
        input_type="number" if numeric else "text",
        keyboard_suggestions=not numeric,
        size_hint_y=None,
        height=dp(height),
        font_size=sp(font_size),
        halign=halign,
        padding=(dp(14), dp(13)),
        foreground_color=INK,
        hint_text_color=MUTED,
        cursor_color=TEAL,
        background_normal="",
        background_active="",
        background_color=(1, 1, 1, 1),
    )


def left_label(text, height=36, font_size=16, bold=False):
    label = Label(
        text=text,
        color=INK,
        size_hint_y=None,
        height=dp(height),
        font_size=sp(font_size),
        bold=bold,
        halign="left",
        valign="middle",
    )
    label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
    return label


def centered_label(text, height=36, font_size=16, color=INK, bold=False):
    label = Label(
        text=text,
        color=color,
        size_hint_y=None,
        height=dp(height),
        font_size=sp(font_size),
        bold=bold,
        halign="center",
        valign="middle",
    )
    label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
    return label
