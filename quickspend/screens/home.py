from datetime import datetime

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from ..formatting import date_text, money
from ..ui import Surface, flow_color, make_button, make_label, theme



class HomeScreenMixin:
    def _build_home(self):
        layout = self._page(self.home, "QuickSpend", settings=True)
        layout.add_widget(make_label("This month's cash flow", "Title", "small"))
        totals_row = MDBoxLayout(adaptive_height=True, spacing=dp(12))
        in_card = Surface(orientation="vertical", padding=dp(16), spacing=dp(4),
                          adaptive_height=True, radius=20)
        out_card = Surface(orientation="vertical", padding=dp(16), spacing=dp(4),
                           adaptive_height=True, radius=20)
        in_card.add_widget(make_label("Money in", "Label", "large", halign="center"))
        self.month_in_total = make_label("₹0.00", "Headline", "small", bold=True, halign="center")
        out_card.add_widget(make_label("Money out", "Label", "large", halign="center"))
        self.month_out_total = make_label("₹0.00", "Headline", "small", bold=True, halign="center")
        in_card.add_widget(self.month_in_total)
        out_card.add_widget(self.month_out_total)
        totals_row.add_widget(in_card)
        totals_row.add_widget(out_card)
        self.month_total_cards = {"In": in_card, "Out": out_card}
        layout.add_widget(totals_row)
        layout.add_widget(make_button(
            "Add money", lambda *_: self.open_amount(), 64, icon="plus",
            font_style="Title", role="medium",
        ))
        layout.add_widget(make_button(
            "Expense history", lambda *_: self.open_history(), 52, "secondary", icon="history",
        ))
        layout.add_widget(make_label("Recent activity", "Title", "medium", bold=True))
        self.recent_box = MDBoxLayout(orientation="vertical", spacing=dp(8), adaptive_height=True)
        scroll = MDScrollView()
        scroll.add_widget(self.recent_box)
        layout.add_widget(scroll)

    def _start_of_month(self):
        return datetime.now().astimezone().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

    def _check_spending_limit(self):
        limit = self.db.get_spending_limit()
        if not limit:
            return False
        spent = self.db.get_outgoing_since(self._start_of_month())
        if spent >= limit:
            message = (
                f"You have spent {money(spent, self.currency)} this month, "
                f"reaching your limit of {money(limit, self.currency)}."
            )
            self._notify_spending_limit(message)
            self.show_message("Spending limit reached", message)
            return True
        return False

    def refresh_home(self):
        income, outgoing = self.db.get_cashflow_since(self._start_of_month())
        self.month_in_total.text = money(income, self.currency)
        self.month_out_total.text = money(outgoing, self.currency)
        for flow, card in self.month_total_cards.items():
            card.md_bg_color = flow_color(flow)
            for label in card.children:
                label.text_color = flow_color(flow, "on_main")
        self._update_android_widget(income, outgoing)
        self.recent_box.clear_widgets()
        expenses = self.db.get_expenses(6)
        if not expenses:
            self.recent_box.add_widget(make_label("No expenses yet. Add your first one above."))
        for expense in expenses:
            _id, amount, currency, _category_id, name, flow, _note, spent_at = expense
            row = Surface(orientation="vertical", padding=(dp(16), dp(10)), spacing=dp(2),
                          adaptive_height=True, fill=flow_color(flow, "container"), radius=12)
            row.add_widget(make_label(
                f"{name}  ·  {flow.upper()}  ·  {money(amount, currency)}",
                "Title", "small", flow_color(flow), bold=True,
            ))
            row.add_widget(make_label(
                date_text(spent_at), "Body", "small", theme().onSurfaceVariantColor,
            ))
            self.recent_box.add_widget(row)


    def go_home(self):
        self.refresh_home()
        self.screens.transition.direction = "right"
        self.screens.current = "home"

    def open_history(self):
        self.refresh_history()
        self.screens.transition.direction = "left"
        self.screens.current = "history"
