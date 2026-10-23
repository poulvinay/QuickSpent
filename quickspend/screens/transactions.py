import sqlite3

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from ..formatting import money, parse_amount_minor
from ..ui import GREEN, RED, Surface, left_label, make_button, make_field



class TransactionScreenMixin:
    def _build_amount(self):
        layout = self._page("Record money")
        layout.add_widget(left_label("Enter the amount you want to record", 50, 18))
        amount_card = Surface(orientation="vertical", padding=dp(8), size_hint_y=None,
                              height=dp(92), fill=(1, 1, 1, 1), radius=16)
        self.amount_input = make_field(
            "0.00", numeric=True, height=76, font_size=32, halign="center"
        )
        self.amount_input.write_tab = False
        self.amount_input.bind(on_text_validate=lambda *_: self.go_to_categories())
        amount_card.add_widget(self.amount_input)
        layout.add_widget(amount_card)
        layout.add_widget(left_label("Amount in INR", 28, 14))
        self.note_input = make_field("Note (optional)", height=50)
        layout.add_widget(self.note_input)
        self.amount_error = left_label("", 34, 14)
        self.amount_error.color = (0.75, 0.12, 0.12, 1)
        layout.add_widget(self.amount_error)
        layout.add_widget(make_button("Next · Choose category", lambda *_: self.go_to_categories(), 58))
        layout.add_widget(make_button("Back to Home", lambda *_: self.go_home(), 48, 15, "secondary"))
        layout.add_widget(Label())
        self.amount_screen.add_widget(layout)

    def _build_category(self):
        layout = self._page("Choose a category")
        self.category_amount = left_label("", 48, 17, True)
        layout.add_widget(self.category_amount)
        self.category_box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        self.category_box.bind(minimum_height=self.category_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.category_box)
        layout.add_widget(scroll)
        layout.add_widget(make_button("+  Add category", lambda *_: self.add_category_popup()))
        layout.add_widget(make_button("Back to amount", lambda *_: self.open_amount(keep=True), 46, 15))
        self.category_screen.add_widget(layout)

    def open_amount(self, keep=False, initial=""):
        if not keep:
            self.amount_input.text = initial
            self.note_input.text = ""
            self.amount_error.text = ""
        self.screens.transition.direction = "left"
        self.screens.current = "amount"
        Clock.schedule_once(lambda *_: self._focus_amount(), 0.2)

    def _focus_amount(self):
        if self.screens.current == "amount":
            self.amount_input.focus = True

    def go_to_categories(self):
        try:
            minor = parse_amount_minor(self.amount_input.text)
        except ValueError:
            self.amount_error.text = "Enter an amount greater than zero."
            return
        self.pending_amount = minor
        self.pending_note = self.note_input.text.strip()
        self.amount_input.focus = False
        self.category_amount.text = f"{money(minor, self.currency)} · Choose In or Out category"
        self.refresh_categories()
        self.screens.transition.direction = "left"
        self.screens.current = "category"

    def refresh_categories(self):
        self.category_box.clear_widgets()
        categories = self.db.get_categories()
        for flow in ("Out", "In"):
            group = [item for item in categories if item[2] == flow]
            if not group:
                continue
            heading = left_label("Money out" if flow == "Out" else "Money in", 38, 16, True)
            heading.color = RED if flow == "Out" else GREEN
            self.category_box.add_widget(heading)
            variant = "expense" if flow == "Out" else "income"
            for category_id, name, _flow, _archived in group:
                self.category_box.add_widget(make_button(
                    name,
                    lambda _, cid=category_id: self.save_expense(cid),
                    58,
                    18,
                    variant,
                ))

    def save_expense(self, category_id):
        category = next((row for row in self.db.get_categories() if row[0] == category_id), None)
        try:
            self.db.add_expense(self.pending_amount, category_id, note=getattr(self, "pending_note", ""), currency_code=self.currency)
        except sqlite3.Error as exc:
            self.show_message("Could not save expense", str(exc))
            return
        self.go_home()
        self.show_message("Money recorded", f"Added {money(self.pending_amount, self.currency)} as {category[1] if category else 'a transaction'}.")

    def _on_keyboard(self, _window, key, *_args):
        if key not in (27, 1001):
            return False
        if self.screens.current == "category":
            self.open_amount(keep=True)
            return True
        if self.screens.current in ("amount", "history"):
            self.go_home()
            return True
        return False
