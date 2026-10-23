import sqlite3

from kivymd.uix.segmentedbutton import (
    MDSegmentButtonLabel,
    MDSegmentedButton,
    MDSegmentedButtonItem,
)

from ..ui import make_field, make_label, theme



class CategoryActionsMixin:
    def add_category_popup(self):
        self.category_form_popup()

    def category_form_popup(self):
        dialog, content, actions = self._dialog("Add category", auto_dismiss=False)
        name_input = make_field("Category name")
        selected_flow = ["Out"]
        flow_label = make_label("Type: Out (money going out)", "Body", "medium", bold=True)
        choose_in = MDSegmentedButtonItem(MDSegmentButtonLabel(text="Money in"))
        choose_out = MDSegmentedButtonItem(MDSegmentButtonLabel(text="Money out"), active=True)
        flow_buttons = MDSegmentedButton(choose_in, choose_out)

        def set_flow(flow, *_):
            selected_flow[0] = flow
            flow_label.text = f"Type: {flow} (money {'coming in' if flow == 'In' else 'going out'})"

        choose_in.bind(on_release=lambda *_: set_flow("In"))
        choose_out.bind(on_release=lambda *_: set_flow("Out"))
        error = make_label("", "Body", "small", theme().errorColor)
        content.add_widget(name_input)
        content.add_widget(flow_label)
        content.add_widget(flow_buttons)
        content.add_widget(error)
        def save_category(*_):
            try:
                self.db.add_category(name_input.text, selected_flow[0])
            except (ValueError, sqlite3.IntegrityError) as exc:
                error.text = "That category already exists." if isinstance(exc, sqlite3.IntegrityError) else str(exc)
                name_input.error = True
                return
            dialog.dismiss()
            self.refresh_categories()
            self.refresh_home()
        actions.add_widget(self._dialog_button("Cancel", lambda *_: dialog.dismiss()))
        actions.add_widget(self._dialog_button("Save", save_category, "primary"))
        dialog.open()
