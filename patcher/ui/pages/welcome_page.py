import customtkinter as ctk
import patcher
from patcher.ui import BasePage, PageRoute


class WelcomePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        description = self._app.i18n.t("welcome_desc")
        desc_label = ctk.CTkLabel(self, text=description, justify="center")
        desc_label.pack(pady=(0, 10))

        credits_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        credits_frame.pack(fill="x", padx=20, pady=5)

        credits_title = ctk.CTkLabel(
            credits_frame,
            text=self._app.i18n.t("welcome_thanks"),
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        credits_title.pack(fill="x", padx=15, pady=(10, 5))

        credits = [
            self._app.i18n.t("welcome_credits_1"),
            self._app.i18n.t("welcome_credits_2"),
            self._app.i18n.t("welcome_credits_3"),
        ]

        for credit in credits:
            credit_label = ctk.CTkLabel(
                credits_frame,
                text=f"- {credit}",
                anchor="w",
                wraplength=320,
                justify="left",
            )
            credit_label.pack(fill="x", padx=15, pady=2)

        closing_label = ctk.CTkLabel(
            credits_frame,
            text=self._app.i18n.t("welcome_thanks_closing"),
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        closing_label.pack(fill="x", padx=15, pady=(5, 10))

        note_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        note_frame.pack(fill="x", padx=20, pady=(5, 10))

        note_title = ctk.CTkLabel(
            note_frame,
            text=self._app.i18n.t("welcome_note_title"),
            font=ctk.CTkFont(weight="bold"),
            text_color="#f39c12",
            anchor="w",
        )
        note_title.pack(fill="x", padx=15, pady=(10, 0))

        note_label = ctk.CTkLabel(
            note_frame,
            text=self._app.i18n.t("welcome_note_desc"),
            anchor="w",
            wraplength=320,
            justify="left",
        )
        note_label.pack(fill="x", padx=15, pady=(2, 10))

    def get_title(self) -> str:
        return self._app.i18n.t("welcome_title", version=patcher.__version__)

    def show_back_button(self) -> bool:
        return False

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.LIBRARY

    def get_custom_footer_widget(self, parent: ctk.CTkFrame) -> ctk.CTkFrame | None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        lang_names = [self._app.i18n.get_language_name(code) for code in self._app.i18n.available_langs]
        current_name = self._app.i18n.get_language_name(self._app.i18n.current_lang)

        dropdown = ctk.CTkOptionMenu(
            frame,
            values=lang_names,
            width=120,
            command=self._on_lang_selected
        )
        dropdown.set(current_name)
        dropdown.pack(expand=True)
        return frame

    def _on_lang_selected(self, selected_name: str):
        for code in self._app.i18n.available_langs:
            if self._app.i18n.get_language_name(code) == selected_name:
                self._app.i18n.set_language(code)
                break
