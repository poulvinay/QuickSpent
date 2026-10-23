from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import SlideTransition
from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.utils.set_bars_colors import set_bars_colors

from database import ExpenseDatabase
from quickspend import APP_VERSION
from quickspend.android import AndroidIntegrationMixin
from quickspend.screens.categories import CategoryActionsMixin
from quickspend.screens.dialogs import DialogMixin
from quickspend.screens.history import HistoryScreenMixin
from quickspend.screens.home import HomeScreenMixin
from quickspend.screens.transactions import TransactionScreenMixin
from quickspend.loading import StartupLoader
from quickspend.ui import TEAL


class SpendTrackerApp(
    HomeScreenMixin,
    TransactionScreenMixin,
    HistoryScreenMixin,
    CategoryActionsMixin,
    DialogMixin,
    AndroidIntegrationMixin,
    MDApp,
):
    version = APP_VERSION

    def build(self):
        self.title = "QuickSpend"
        self.icon = "icon/finance-tracker-icon-square.png"
        self.db = ExpenseDatabase(f"{self.user_data_dir}/expenses.db")
        self.currency = "INR"
        self.pending_amount = 0
        self._android_activity = None
        self._android_bridge_class = None
        self._quick_activity_class = None
        Window.bind(on_keyboard=self._on_keyboard)

        self.theme_cls.theme_style_switch_animation = False
        self.theme_cls.theme_style = "Dark" if self._system_dark_mode() else "Light"
        self.theme_cls.primary_palette = TEAL

        self.screens = MDScreenManager(transition=SlideTransition(duration=0.15))
        self.home = MDScreen(name="home")
        self.amount_screen = MDScreen(name="amount")
        self.category_screen = MDScreen(name="category")
        self.history_screen = MDScreen(name="history")
        for screen in (self.home, self.amount_screen, self.category_screen, self.history_screen):
            self.screens.add_widget(screen)
        self._build_home()
        self._build_amount()
        self._build_category()
        self._build_history()
        self.refresh_home()
        self.refresh_categories()
        Clock.schedule_interval(self._consume_quick_entry_request, 0.35)
        Clock.schedule_interval(self._consume_configuration_change, 1)
        self.root_layout = MDFloatLayout()
        self.root_layout.add_widget(self.screens)
        self.startup_loader = StartupLoader("icon/loader-spritesheet.png")
        self.root_layout.add_widget(self.startup_loader)
        self._apply_surface_colors()
        self.theme_cls.on_colors = self._on_theme_colors
        Clock.schedule_once(self._hide_native_loading_screen, 0.25)
        Clock.schedule_once(self._dismiss_startup_loader, 1.6)
        return self.root_layout

    def on_resume(self):
        self.apply_system_theme()

    def _on_theme_colors(self):
        """Repaint the parts the Material theme does not colour by itself."""
        self._apply_surface_colors()
        self.refresh_home()
        self.refresh_categories()
        self.refresh_history()
        # Unchanged rows compare equal to the old data, so repaint them explicitly.
        self.history_list.refresh_from_data()

    def _apply_surface_colors(self):
        surface = self.theme_cls.surfaceColor
        self.root_layout.md_bg_color = surface
        # Light system bar icons on a dark surface and vice versa. The helper
        # needs the light navigation bar flag, which arrived in Android 8.0.
        if self._android_sdk_int() >= 26:
            icons = "Dark" if self.theme_cls.theme_style == "Light" else "Light"
            set_bars_colors(surface, surface, icons)

    @staticmethod
    def _hide_native_loading_screen(_dt):
        try:
            from android.loadingscreen import hide_loading_screen

            hide_loading_screen()
        except ImportError:
            # The Android module is only available in packaged builds.
            pass

    def _dismiss_startup_loader(self, _dt):
        if self.startup_loader.parent is self.root_layout:
            self.root_layout.remove_widget(self.startup_loader)
        self.startup_loader.stop()
