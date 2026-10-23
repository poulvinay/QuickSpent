import calendar
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sqlite3

from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView

from ..formatting import date_text, money
from ..ui import (
    GREEN,
    GREEN_PALE,
    INK,
    RED,
    RED_PALE,
    Surface,
    left_label,
    make_button,
    make_field,
)



class HistoryScreenMixin:
    def _build_history(self):
        layout = self._page("Money in and out")
        now = datetime.now().astimezone()
        current_month = now.strftime("%Y-%m")
        month_keys = sorted(set(self.db.get_expense_months()) | {current_month}, reverse=True)
        self._month_by_label = {
            datetime.strptime(month, "%Y-%m").strftime("%b %Y"): month
            for month in month_keys
        }

        filters = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(10))
        month_group = BoxLayout(orientation="vertical", spacing=dp(2))
        day_group = BoxLayout(orientation="vertical", spacing=dp(2))
        month_group.add_widget(left_label("Month", 18, 12, True))
        day_group.add_widget(left_label("Day", 18, 12, True))
        self.month_filter = Spinner(
            text=now.strftime("%b %Y"),
            values=tuple(self._month_by_label),
            size_hint=(1, None),
            height=dp(42),
            font_size=sp(14),
            color=INK,
            background_normal="",
            background_down="",
            background_color=(0.88, 0.92, 0.90, 1),
        )
        self.day_filter = Spinner(
            text="All days",
            values=self._day_values(current_month),
            size_hint=(1, None),
            height=dp(42),
            font_size=sp(14),
            color=INK,
            background_normal="",
            background_down="",
            background_color=(0.88, 0.92, 0.90, 1),
        )
        month_group.add_widget(self.month_filter)
        day_group.add_widget(self.day_filter)
        filters.add_widget(month_group)
        filters.add_widget(day_group)
        self.month_filter.bind(text=self._on_history_month_selected)
        self.day_filter.bind(text=lambda *_: self.refresh_history())
        layout.add_widget(filters)

        self.history_box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        self.history_box.bind(minimum_height=self.history_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.history_box)
        layout.add_widget(scroll)
        layout.add_widget(make_button("+  Add money", lambda *_: self.open_amount()))
        layout.add_widget(make_button("Back", lambda *_: self.go_home(), 46, 15))
        self.history_screen.add_widget(layout)

    @staticmethod
    def _day_values(month):
        year, month_number = (int(part) for part in month.split("-"))
        days_in_month = calendar.monthrange(year, month_number)[1]
        return ("All days", *(str(day) for day in range(1, days_in_month + 1)))

    def _on_history_month_selected(self, _spinner, selected_label):
        month = self._month_by_label.get(selected_label)
        if month is None:
            return
        self.day_filter.values = self._day_values(month)
        self.day_filter.text = "All days"
        self.refresh_history()

    def refresh_history(self):
        self.history_box.clear_widgets()
        month = self._month_by_label.get(self.month_filter.text)
        day = None if self.day_filter.text == "All days" else self.day_filter.text
        expenses = self.db.get_expenses(300, month=month, day=day)
        if not expenses:
            self.history_box.add_widget(
                left_label("No transactions match this date filter.", 56)
            )
        for expense in expenses:
            expense_id, amount, currency, _cid, category, flow, note, spent_at = expense
            row = Surface(orientation="vertical", size_hint_y=None, height=dp(126), spacing=dp(3),
                          padding=(dp(10), dp(6)), fill=GREEN_PALE if flow == "In" else RED_PALE,
                          radius=14)
            sign = "+" if flow == "In" else "-"
            transaction_label = left_label(f"{flow.upper()} · {category} · {sign}{money(amount, currency)}", 38, 16, True)
            transaction_label.color = GREEN if flow == "In" else RED
            row.add_widget(transaction_label)
            row.add_widget(left_label(f"{date_text(spent_at)}" + (f" · {note}" if note else ""), 24, 13))
            actions = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
            actions.add_widget(make_button("Edit", lambda _, eid=expense_id: self.edit_expense_popup(eid), 34, 13, "secondary"))
            actions.add_widget(make_button("Delete", lambda _, eid=expense_id: self.confirm_delete(eid), 34, 13, "danger"))
            row.add_widget(actions)
            self.history_box.add_widget(row)

    def edit_expense_popup(self, expense_id):
        expense = self.db.get_expense(expense_id)
        if not expense:
            return
        _id, amount, _currency, category_id, _flow, note, spent_at = expense
        popup, content = self._dialog("Edit transaction", 380, auto_dismiss=False)
        amount_field = make_field("Amount in INR", f"{Decimal(amount) / 100:.2f}", numeric=True)
        note_field = make_field("Note (optional)", note)
        categories = self.db.get_categories(include_archived=True)
        names = {row[0]: (row[1], row[2]) for row in categories}
        selected = [category_id]
        category_button = make_button(
            f"Category: {names.get(category_id, ('Choose', 'Out'))[1]} · {names.get(category_id, ('Choose', 'Out'))[0]}",
            None,
            48,
            15,
            "secondary",
        )
        error = left_label("", 30, 13)
        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save = make_button("Save changes", height=46, font_size=15)
        cancel = make_button("Cancel", height=46, font_size=15, variant="secondary")
        buttons.add_widget(save)
        buttons.add_widget(cancel)
        content.add_widget(amount_field); content.add_widget(category_button); content.add_widget(note_field); content.add_widget(error); content.add_widget(buttons)
        def choose_category(*_):
            chooser, choices = self._dialog("Choose category", 440)
            choices.add_widget(left_label("Select the category and money direction.", 38, 14))
            choices_scroll = ScrollView()
            choices_list = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
            choices_list.bind(minimum_height=choices_list.setter("height"))
            choices_scroll.add_widget(choices_list)
            choices.add_widget(choices_scroll)
            for cid, (name, flow) in names.items():
                def select(_, selected_id=cid, selected_name=name, selected_flow=flow):
                    selected[0] = selected_id
                    category_button.text = f"Category: {selected_flow} · {selected_name}"
                    chooser.dismiss()
                variant = "income" if flow == "In" else "expense"
                choices_list.add_widget(make_button(f"{flow.upper()} · {name}", select, 48, 15, variant))
            chooser.open()
        category_button.bind(on_release=choose_category)
        def save_edit(*_):
            try:
                value = Decimal(amount_field.text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                self.db.update_expense(expense_id, int(value * 100), selected[0], note_field.text, spent_at)
            except (InvalidOperation, ValueError, sqlite3.Error) as exc:
                error.text = f"Enter a valid amount. {exc}"
                return
            popup.dismiss(); self.refresh_history(); self.refresh_home()
        save.bind(on_release=save_edit); cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()

    def confirm_delete(self, expense_id):
        popup, content = self._dialog("Delete transaction", 190)
        content.add_widget(left_label("Delete this transaction? This cannot be undone.", 55, 15))
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        cancel = make_button("Cancel", height=48, font_size=15, variant="secondary")
        delete = make_button("Delete", height=48, font_size=15, variant="danger")
        buttons.add_widget(cancel)
        buttons.add_widget(delete)
        content.add_widget(buttons)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        def remove(*_):
            self.db.delete_expense(expense_id); popup.dismiss(); self.refresh_history(); self.refresh_home()
        delete.bind(on_release=remove); popup.open()
