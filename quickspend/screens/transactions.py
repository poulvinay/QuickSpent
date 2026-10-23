import sqlite3

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from ..formatting import money, parse_amount_minor
from ..ui import flow_color, make_button, make_field, make_label



class TransactionScreenMixin:
    def _build_amount(self):
        layout = self._page(self.amount_screen, "Record money")
        layout.add_widget(make_label("Enter the amount you want to record", "Body", "large"))
        self.amount_input = make_field(
            "Amount in INR",
            numeric=True,
            error_text="Enter an amount greater than zero.",
            font_style="Headline",
            role="medium",
            halign="center",
            height=dp(76),
        )
        self.amount_input.bind(on_text_validate=lambda *_: self.go_to_categories())
        # The error text is drawn just below the field, so leave room for it.
        layout.add_widget(MDBoxLayout(self.amount_input, adaptive_height=True, padding=(0, 0, 0, dp(14))))
        self.note_input = make_field("Note (optional)")
        layout.add_widget(self.note_input)
        layout.add_widget(make_button(
            "Next · Choose category", lambda *_: self.go_to_categories(), 56, icon="arrow-right",
        ))
        layout.add_widget(make_button("Back to Home", lambda *_: self.go_home(), 48, "secondary"))
        layout.add_widget(Widget())

    def _build_category(self):
        layout = self._page(self.category_screen, "Choose a category")
        self.category_amount = make_label("", "Title", "medium", bold=True)
        layout.add_widget(self.category_amount)
        self.category_box = MDBoxLayout(orientation="vertical", spacing=dp(8), adaptive_height=True)
        self._category_signature = None
        scroll = MDScrollView()
        scroll.add_widget(self.category_box)
        layout.add_widget(scroll)
        layout.add_widget(make_button(
            "Add category", lambda *_: self.add_category_popup(), 52, "outlined", icon="plus",
        ))
        layout.add_widget(make_button(
            "Back to amount", lambda *_: self.open_amount(keep=True), 48, "secondary",
        ))

    def open_amount(self, keep=False, initial=""):
        if not keep:
            self.amount_input.text = initial
            self.note_input.text = ""
            self.amount_input.error = False
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
            self.amount_input.error = True
            return
        self.pending_amount = minor
        self.pending_note = self.note_input.text.strip()
        self.amount_input.focus = False
        self.category_amount.text = f"{money(minor, self.currency)} · Choose In or Out category"
        self.refresh_categories()
        self.screens.transition.direction = "left"
        self.screens.current = "category"

    def refresh_categories(self):
        categories = self.db.get_categories()
        # Material buttons are slow to create, so only rebuild after a change.
        signature = (categories, self.theme_cls.theme_style)
        if signature == self._category_signature:
            return
        self._category_signature = signature
        self.category_box.clear_widgets()
        for flow in ("Out", "In"):
            group = [item for item in categories if item[2] == flow]
            if not group:
                continue
            self.category_box.add_widget(make_label(
                "Money out" if flow == "Out" else "Money in",
                "Title", "small", flow_color(flow), bold=True, padding=(0, dp(8), 0, 0),
            ))
            variant = "expense" if flow == "Out" else "income"
            for category_id, name, _flow, _archived in group:
                self.category_box.add_widget(make_button(
                    name,
                    lambda _, cid=category_id: self.save_expense(cid),
                    56,
                    variant,
                    font_style="Title",
                    role="medium",
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
        if self._dismiss_overlay():
            return True
        if self.screens.current == "category":
            self.open_amount(keep=True)
            return True
        if self.screens.current in ("amount", "history"):
            self.go_home()
            return True
        return False
