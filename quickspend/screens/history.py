from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sqlite3

from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.scrollview import MDScrollView

from ..formatting import date_text, money
from ..ui import Surface, flow_color, make_button, make_field, make_label, paint_button, theme



class TransactionRow(RecycleDataViewBehavior, Surface):
    """A history card. RecycleView only creates the visible ones and reuses them."""

    expense_id = NumericProperty()
    flow = StringProperty("Out")
    title = StringProperty()
    details = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=(dp(16), dp(12)), spacing=dp(4), **kwargs)
        app = MDApp.get_running_app()
        self._title = make_label("", "Title", "medium", bold=True, shorten=True, max_lines=1)
        self._details = make_label("", "Body", "medium", shorten=True, max_lines=1)
        self.bind(title=self._title.setter("text"), details=self._details.setter("text"))
        actions = MDBoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        actions.add_widget(make_button(
            "Edit", lambda *_: app.edit_expense_popup(self.expense_id), 40, "secondary",
            icon="pencil-outline",
        ))
        self._delete = make_button(
            "Delete", lambda *_: app.confirm_delete(self.expense_id), 40, "danger",
            icon="delete-outline",
        )
        actions.add_widget(self._delete)
        for widget in (self._title, self._details, Widget(), actions):
            self.add_widget(widget)

    def refresh_view_attrs(self, rv, index, data):
        super().refresh_view_attrs(rv, index, data)
        # Recolour on every refresh so recycled rows follow theme switches too.
        self.md_bg_color = flow_color(self.flow, "container")
        self._title.text_color = flow_color(self.flow)
        self._details.text_color = theme().onSurfaceVariantColor
        paint_button(self._delete, "danger")


class HistoryScreenMixin:
    def _build_history(self):
        layout = self._page(self.history_screen, "Money in and out")
        self._history_month = datetime.now().astimezone().strftime("%Y-%m")
        self._history_day = None
        self._day_picker = None

        filters = MDBoxLayout(adaptive_height=True, spacing=dp(12))
        month_group = MDBoxLayout(orientation="vertical", spacing=dp(4), adaptive_height=True)
        day_group = MDBoxLayout(orientation="vertical", spacing=dp(4), adaptive_height=True)
        month_group.add_widget(make_label("Month", "Label", "large", bold=True))
        day_group.add_widget(make_label("Day", "Label", "large", bold=True))
        self.month_filter = make_button(
            "", lambda *_: self.open_history_month_menu(), 44, "outlined",
            icon="calendar-month-outline",
        )
        self.day_filter = make_button(
            "All days", lambda *_: self.open_history_day_picker(), 44, "outlined",
            icon="calendar-today",
        )
        month_group.add_widget(self.month_filter)
        day_group.add_widget(self.day_filter)
        filters.add_widget(month_group)
        filters.add_widget(day_group)
        layout.add_widget(filters)

        self.history_empty = make_label()
        layout.add_widget(self.history_empty)
        self.history_list = RecycleView()
        rows = RecycleBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            # Padding and buttons are in dp; the two text lines grow with font size.
            default_size=(None, dp(76) + sp(48)),
            default_size_hint=(1, None),
            size_hint_y=None,
        )
        rows.bind(minimum_height=rows.setter("height"))
        self.history_list.add_widget(rows)
        # Set after the layout exists; RecycleView drops a viewclass given earlier.
        self.history_list.viewclass = TransactionRow
        layout.add_widget(self.history_list)
        layout.add_widget(make_button("Add money", lambda *_: self.open_amount(), 52, icon="plus"))
        layout.add_widget(make_button("Back", lambda *_: self.go_home(), 48, "secondary"))
        self._update_history_filters()

    @staticmethod
    def _month_label(month):
        return datetime.strptime(month, "%Y-%m").strftime("%b %Y")

    def _update_history_filters(self):
        self.month_filter.text_label.text = self._month_label(self._history_month)
        if self._history_day is None:
            self.day_filter.text_label.text = "All days"
        else:
            day = datetime.strptime(f"{self._history_month}-{self._history_day:02d}", "%Y-%m-%d")
            self.day_filter.text_label.text = day.strftime("%b %d")

    def open_history_month_menu(self):
        current_month = datetime.now().astimezone().strftime("%Y-%m")
        months = set(self.db.get_expense_months()) | {current_month, self._history_month}
        self.month_menu = MDDropdownMenu(
            caller=self.month_filter,
            items=[
                {
                    "text": self._month_label(month),
                    "on_release": lambda value=month: self._select_history_month(value),
                }
                for month in sorted(months, reverse=True)
            ],
            max_height=dp(320),
        )
        self.month_menu.open()

    def _select_history_month(self, month):
        self.month_menu.dismiss()
        self._history_month = month
        self._history_day = None
        self.refresh_history()

    def open_history_day_picker(self):
        if self._day_picker is None:
            # The calendar is slow to build, so it is created once and reused.
            self._day_picker = MDModalDatePicker(
                supporting_text="Select day",
                text_button_cancel="All days",
                text_button_ok="OK",
            )
            self._day_picker.bind(
                on_ok=self._on_history_day_picked,
                on_cancel=self._on_history_all_days,
            )
            # The pencil switches to typed date entry, which this filter doesn't use.
            edit_button = self._day_picker.ids.icon_button
            edit_button.opacity, edit_button.disabled = 0, True
        picker = self._day_picker
        if picker.parent is not None:
            # Still animating closed; reopening now would crash and the pending
            # close animation would then remove the reopened picker.
            return
        if picker._menu_year_selection_is_open:
            # Always reopen on the calendar, not the year list left open last time.
            picker.open_menu_year_selection()
        year, month = (int(part) for part in self._history_month.split("-"))
        today = date.today()
        if self._history_day is not None:
            selected = date(year, month, self._history_day)
        elif (today.year, today.month) == (year, month):
            selected = today
        else:
            selected = date(year, month, 1)
        picker.today = today
        picker.sel_year, picker.sel_month, picker.sel_day = selected.year, selected.month, selected.day
        picker.update_calendar(year, month)
        picker.open()

    def _on_history_day_picked(self, picker):
        picked = picker.get_date()[0]
        picker.dismiss()
        self._history_month = picked.strftime("%Y-%m")
        self._history_day = picked.day
        self.refresh_history()

    def _on_history_all_days(self, picker):
        picker.dismiss()
        self._history_day = None
        self.refresh_history()

    def refresh_history(self):
        self._update_history_filters()
        expenses = self.db.get_expenses(300, month=self._history_month, day=self._history_day)
        self.history_empty.text = "" if expenses else "No transactions match this date filter."
        rows = []
        for expense in expenses:
            expense_id, amount, currency, _cid, category, flow, note, spent_at = expense
            sign = "+" if flow == "In" else "-"
            rows.append({
                "expense_id": expense_id,
                "flow": flow,
                "title": f"{flow.upper()} · {category} · {sign}{money(amount, currency)}",
                "details": f"{date_text(spent_at)}" + (f" · {note}" if note else ""),
            })
        self.history_list.data = rows

    def edit_expense_popup(self, expense_id):
        expense = self.db.get_expense(expense_id)
        if not expense:
            return
        _id, amount, _currency, category_id, _flow, note, spent_at = expense
        dialog, content, actions = self._dialog("Edit transaction", auto_dismiss=False)
        amount_field = make_field("Amount in INR", f"{Decimal(amount) / 100:.2f}", numeric=True)
        note_field = make_field("Note (optional)", note)
        categories = self.db.get_categories(include_archived=True)
        names = {row[0]: (row[1], row[2]) for row in categories}
        selected = [category_id]
        category_button = make_button(
            f"Category: {names.get(category_id, ('Choose', 'Out'))[1]} · {names.get(category_id, ('Choose', 'Out'))[0]}",
            None,
            48,
            "secondary",
            icon="tag-outline",
        )
        error = make_label("", "Body", "small", theme().errorColor)
        content.add_widget(amount_field); content.add_widget(category_button); content.add_widget(note_field); content.add_widget(error)
        def choose_category(*_):
            chooser, choices, _choice_actions = self._dialog(
                "Choose category", "Select the category and money direction."
            )
            choices_list = MDBoxLayout(orientation="vertical", spacing=dp(8), adaptive_height=True)
            choices_scroll = MDScrollView(size_hint_y=None, height=min(dp(320), len(names) * dp(56)))
            choices_scroll.add_widget(choices_list)
            choices.add_widget(choices_scroll)
            for cid, (name, flow) in names.items():
                def select(_, selected_id=cid, selected_name=name, selected_flow=flow):
                    selected[0] = selected_id
                    category_button.text_label.text = f"Category: {selected_flow} · {selected_name}"
                    chooser.dismiss()
                variant = "income" if flow == "In" else "expense"
                choices_list.add_widget(make_button(f"{flow.upper()} · {name}", select, 48, variant))
            chooser.open()
        category_button.bind(on_release=choose_category)
        def save_edit(*_):
            try:
                value = Decimal(amount_field.text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                self.db.update_expense(expense_id, int(value * 100), selected[0], note_field.text, spent_at)
            except (InvalidOperation, ValueError, sqlite3.Error) as exc:
                error.text = f"Enter a valid amount. {exc}"
                amount_field.error = True
                return
            dialog.dismiss(); self.refresh_history(); self.refresh_home()
        actions.add_widget(self._dialog_button("Cancel", lambda *_: dialog.dismiss()))
        actions.add_widget(self._dialog_button("Save changes", save_edit, "primary"))
        dialog.open()

    def confirm_delete(self, expense_id):
        dialog, _content, actions = self._dialog(
            "Delete transaction", "Delete this transaction? This cannot be undone."
        )
        def remove(*_):
            self.db.delete_expense(expense_id); dialog.dismiss(); self.refresh_history(); self.refresh_home()
        actions.add_widget(self._dialog_button("Cancel", lambda *_: dialog.dismiss()))
        actions.add_widget(self._dialog_button("Delete", remove, "danger"))
        dialog.open()
