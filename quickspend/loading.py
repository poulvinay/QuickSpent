"""Startup animation shown while QuickSpend finishes initializing."""

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image


class StartupLoader(FloatLayout):
    """Play the WebM-derived sprite sheet once over the first app screen."""

    FRAME_WIDTH = 150
    FRAME_HEIGHT = 150
    COLUMNS = 5
    ROWS = 9
    FRAME_RATE = 30

    def __init__(self, sprite_sheet, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self._background = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_background, size=self._sync_background)
        self._frames = self._load_frames(sprite_sheet)
        self._frame_index = 0
        self._image = Image(
            texture=self._frames[0],
            size_hint=(None, None),
            size=(dp(150), dp(150)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.add_widget(self._image)
        self._animation = Clock.schedule_interval(self._advance, 1 / self.FRAME_RATE)

    def _sync_background(self, *_args):
        self._background.pos = self.pos
        self._background.size = self.size

    @classmethod
    def _load_frames(cls, sprite_sheet):
        texture = CoreImage(sprite_sheet).texture
        frames = []
        for row in range(cls.ROWS):
            # Kivy texture coordinates start at the bottom-left; the sheet is
            # arranged from the top-left in normal reading order.
            y = (cls.ROWS - 1 - row) * cls.FRAME_HEIGHT
            for column in range(cls.COLUMNS):
                frames.append(
                    texture.get_region(
                        column * cls.FRAME_WIDTH,
                        y,
                        cls.FRAME_WIDTH,
                        cls.FRAME_HEIGHT,
                    )
                )
        return frames

    def _advance(self, _dt):
        self._frame_index += 1
        if self._frame_index >= len(self._frames):
            self.stop()
            return False
        self._image.texture = self._frames[self._frame_index]
        return True

    def stop(self):
        if self._animation is not None:
            self._animation.cancel()
            self._animation = None
