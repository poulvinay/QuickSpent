from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.floatlayout import FloatLayout

from database import ExpenseDatabase
from quickspend import APP_VERSION
from quickspend.android import AndroidIntegrationMixin
from quickspend.screens.categories import CategoryActionsMixin
from quickspend.screens.dialogs import DialogMixin
from quickspend.screens.history import HistoryScreenMixin
from quickspend.screens.home import HomeScreenMixin
from quickspend.screens.transactions import TransactionScreenMixin
from quickspend.loading import StartupLoader


class SpendTrackerApp(
    HomeScreenMixin,
    TransactionScreenMixin,
    HistoryScreenMixin,
    CategoryActionsMixin,
    DialogMixin,
    AndroidIntegrationMixin,
    App,
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

        self.screens = ScreenManager(transition=SlideTransition(duration=0.15))
        self.home = Screen(name="home")
        self.amount_screen = Screen(name="amount")
        self.category_screen = Screen(name="category")
        self.history_screen = Screen(name="history")
        for screen in (self.home, self.amount_screen, self.category_screen, self.history_screen):
            self.screens.add_widget(screen)
        self._build_home()
        self._build_amount()
        self._build_category()
        self._build_history()
        self.refresh_home()
        Clock.schedule_interval(self._consume_quick_entry_request, 0.35)
        self.root_layout = FloatLayout()
        self.root_layout.add_widget(self.screens)
        self.startup_loader = StartupLoader("icon/loader-spritesheet.png")
        self.root_layout.add_widget(self.startup_loader)
        Clock.schedule_once(self._hide_native_loading_screen, 0.25)
        Clock.schedule_once(self._dismiss_startup_loader, 1.6)
        return self.root_layout

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
