import sqlite3

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from ..ui import left_label, make_button, make_field



class CategoryActionsMixin:
    def add_category_popup(self):
        self.category_form_popup()

    def category_form_popup(self):
        popup, content = self._dialog("Add category", 360, auto_dismiss=False)
        name_input = make_field("Category name")
        selected_flow = ["Out"]
        flow_label = left_label("Type: Out (money going out)", 32, 14, True)
        flow_buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        choose_in = make_button("Money in", height=46, font_size=14, variant="income")
        choose_out = make_button("Money out", height=46, font_size=14, variant="expense")
        flow_buttons.add_widget(choose_in)
        flow_buttons.add_widget(choose_out)

        def set_flow(flow, *_):
            selected_flow[0] = flow
            flow_label.text = f"Type: {flow} (money {'coming in' if flow == 'In' else 'going out'})"

        choose_in.bind(on_release=lambda *_: set_flow("In"))
        choose_out.bind(on_release=lambda *_: set_flow("Out"))
        error = left_label("", 34, 14)
        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        save = make_button("Save", height=48, font_size=15)
        cancel = make_button("Cancel", height=48, font_size=15, variant="secondary")
        buttons.add_widget(save)
        buttons.add_widget(cancel)
        content.add_widget(name_input)
        content.add_widget(flow_label)
        content.add_widget(flow_buttons)
        content.add_widget(error)
        content.add_widget(buttons)
        def save_category(*_):
            try:
                self.db.add_category(name_input.text, selected_flow[0])
            except (ValueError, sqlite3.IntegrityError) as exc:
                error.text = "That category already exists." if isinstance(exc, sqlite3.IntegrityError) else str(exc)
                return
            popup.dismiss()
            self.refresh_categories()
            self.refresh_home()
        save.bind(on_release=save_category)
        cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()
