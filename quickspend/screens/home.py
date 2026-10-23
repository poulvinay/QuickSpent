from datetime import datetime

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from ..formatting import date_text, money
from ..ui import GREEN, GREEN_PALE, RED, RED_PALE, Surface, centered_label, left_label, make_button



class HomeScreenMixin:
    def _build_home(self):
        layout = self._page("QuickSpend", settings=True)
        layout.add_widget(left_label("This month's cash flow", 30, 15))
        totals_row = BoxLayout(size_hint_y=None, height=dp(100), spacing=dp(10))
        in_card = Surface(orientation="vertical", padding=dp(8), spacing=dp(2), fill=GREEN, radius=18)
        out_card = Surface(orientation="vertical", padding=dp(8), spacing=dp(2), fill=RED, radius=18)
        in_card.add_widget(centered_label("Money in", 30, 14, (1, 1, 1, 1)))
        self.month_in_total = centered_label("₹0.00", 45, 21, (1, 1, 1, 1), True)
        out_card.add_widget(centered_label("Money out", 30, 14, (1, 1, 1, 1)))
        self.month_out_total = centered_label("₹0.00", 45, 21, (1, 1, 1, 1), True)
        in_card.add_widget(self.month_in_total)
        out_card.add_widget(self.month_out_total)
        totals_row.add_widget(in_card)
        totals_row.add_widget(out_card)
        layout.add_widget(totals_row)
        layout.add_widget(make_button("+  Add money", lambda *_: self.open_amount(), 64, 20))
        layout.add_widget(make_button("Expense history", lambda *_: self.open_history()))
        layout.add_widget(left_label("Recent activity", 38, 18, True))
        self.recent_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.recent_box.bind(minimum_height=self.recent_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.recent_box)
        layout.add_widget(scroll)
        self.home.add_widget(layout)

    def _start_of_month(self):
        return datetime.now().astimezone().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

    def refresh_home(self):
        income, outgoing = self.db.get_cashflow_since(self._start_of_month())
        self.month_in_total.text = money(income, self.currency)
        self.month_out_total.text = money(outgoing, self.currency)
        self._update_android_widget(income, outgoing)
        self.recent_box.clear_widgets()
        expenses = self.db.get_expenses(6)
        if not expenses:
            self.recent_box.add_widget(left_label("No expenses yet. Add your first one above.", 54, 15))
        for expense in expenses:
            _id, amount, currency, _category_id, name, flow, _note, spent_at = expense
            color = GREEN if flow == "In" else RED
            row = Surface(orientation="vertical", padding=(dp(12), dp(5)),
                          size_hint_y=None, height=dp(58), fill=GREEN_PALE if flow == "In" else RED_PALE,
                          radius=14)
            transaction_label = left_label(f"{name}  ·  {flow.upper()}  ·  {money(amount, currency)}", 28, 15, True)
            transaction_label.color = color
            row.add_widget(transaction_label)
            row.add_widget(left_label(date_text(spent_at), 20, 12))
            self.recent_box.add_widget(row)


    def go_home(self):
        self.refresh_home()
        self.screens.transition.direction = "right"
        self.screens.current = "home"

    def open_history(self):
        self.refresh_history()
        self.screens.transition.direction = "left"
        self.screens.current = "history"
