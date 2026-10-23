from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldHelperText, MDTextFieldHintText

# Seed for the Material colour scheme when the device has no wallpaper colours.
TEAL = "#1F6E6B"

# Material 3 tones of QuickSpend's green (money in) and red (money out). They
# stay fixed under Material You so In and Out keep their meaning on any wallpaper.
FLOW_COLORS = {
    "Light": {
        "In": {"main": "#076D3E", "on_main": "#FFFFFF", "container": "#DDF4E0"},
        "Out": {"main": "#B02D29", "on_main": "#FFFFFF", "container": "#FFE9E6"},
    },
    "Dark": {
        "In": {"main": "#82D9A0", "on_main": "#00391D", "container": "#2C4032"},
        "Out": {"main": "#FFB4AC", "on_main": "#690006", "container": "#513431"},
    },
}

BUTTON_STYLES = {
    "primary": "filled",
    "secondary": "tonal",
    "outlined": "outlined",
    "text": "text",
    "danger": "filled",
    "income": "filled",
    "expense": "filled",
}


def theme():
    return MDApp.get_running_app().theme_cls


def flow_color(flow, role="main"):
    return get_color_from_hex(FLOW_COLORS[theme().theme_style][flow][role])


class Surface(MDBoxLayout):
    """A flat rounded container: a Material filled card without touch handling."""

    def __init__(self, fill=None, radius=16, **kwargs):
        super().__init__(radius=[dp(radius)], **kwargs)
        if fill is not None:
            self.md_bg_color = fill


class WideButton(MDButton):
    """An MDButton that fills its row and keeps its icon and label centred."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(size=self.adjust_pos)
        if self._button_text:
            self._button_text.bind(width=self.adjust_pos)

    def adjust_width(self, *_args):
        # The layout sets the width; MDButton would shrink it to the content.
        pass

    def adjust_pos(self, *_args):
        text, icon = self._button_text, self._button_icon
        gap = dp(8) if text and icon else 0
        content = (icon.width if icon else 0) + gap + (text.width if text else 0)
        x = (self.width - content) / 2
        if icon:
            icon.x = x
            x += icon.width + gap
        if text:
            text.x = x


def paint_button(button, variant):
    """Apply the colours of variants that are not part of the Material theme."""
    if variant == "danger":
        fill, ink = theme().errorColor, theme().onErrorColor
    elif variant in ("income", "expense"):
        flow = "In" if variant == "income" else "Out"
        fill, ink = flow_color(flow), flow_color(flow, "on_main")
    else:
        return
    button.theme_bg_color = "Custom"
    button.md_bg_color = fill
    if button._button_text:
        button._button_text.theme_text_color = "Custom"
        button._button_text.text_color = ink
    if button._button_icon:
        button._button_icon.theme_icon_color = "Custom"
        button._button_icon.icon_color = ink


def make_button(
    text,
    callback=None,
    height=52,
    variant="primary",
    icon=None,
    full_width=True,
    font_style="Label",
    role="large",
):
    parts = [MDButtonIcon(icon=icon)] if icon else []
    parts.append(MDButtonText(text=text, font_style=font_style, role=role))
    button_class = WideButton if full_width else MDButton
    button = button_class(*parts, style=BUTTON_STYLES[variant])
    button.theme_height = "Custom"
    button.size_hint_y = None
    button.height = dp(height)
    button.radius = [dp(height) / 2]
    if full_width:
        button.theme_width = "Custom"
        button.size_hint_x = 1
    paint_button(button, variant)
    button.text_label = parts[-1]
    if callback:
        button.bind(on_release=callback)
    return button


def make_field(hint, text="", numeric=False, error_text=None, **kwargs):
    parts = [MDTextFieldHintText(text=hint)]
    if error_text:
        parts.append(MDTextFieldHelperText(text=error_text, mode="on_error"))
    return MDTextField(
        *parts,
        text=text,
        mode="outlined",
        multiline=False,
        write_tab=False,
        input_filter="float" if numeric else None,
        input_type="number" if numeric else "text",
        keyboard_suggestions=not numeric,
        **kwargs,
    )


def make_label(text="", font_style="Body", role="large", color=None, bold=False, **kwargs):
    label = MDLabel(
        text=text,
        font_style=font_style,
        role=role,
        bold=bold,
        adaptive_height=True,
        # Adaptive labels only resize when their text renders; start empty
        # ones (error messages) collapsed instead of at Kivy's 100px default.
        height=0,
        **kwargs,
    )
    if color is not None:
        label.text_color = color
    return label
