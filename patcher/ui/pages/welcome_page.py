import customtkinter as ctk
import patcher
from patcher.ui import BasePage, PageRoute


class WelcomePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        description = self._app.i18n.t("welcome_desc")
        desc_label = ctk.CTkLabel(self, text=description, justify="center")
        desc_label.pack(pady=(0, 10))

        trans_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        trans_frame.pack(fill="x", padx=20, pady=5)

        trans_title = ctk.CTkLabel(
            trans_frame,
            text=self._app.i18n.t("welcome_translations_title"),
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        trans_title.pack(fill="x", padx=15, pady=(10, 0))

        trans_label = ctk.CTkLabel(
            trans_frame,
            text=self._app.i18n.t("welcome_translations_desc"),
            anchor="w",
            wraplength=320,
            justify="left",
        )
        trans_label.pack(fill="x", padx=15, pady=(2, 10))

        trans_btn = ctk.CTkButton(
            trans_frame,
            text=self._app.i18n.t("welcome_translations_btn"),
            command=self._open_translation_site,
        )
        trans_btn.pack(fill="x", padx=15, pady=(0, 10))

        credits_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        credits_frame.pack(fill="x", padx=20, pady=5)

        credits_title = ctk.CTkLabel(
            credits_frame,
            text=self._app.i18n.t("welcome_credits_title"),
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        credits_title.pack(fill="x", padx=15, pady=(10, 5))

        credits_label = ctk.CTkLabel(
            credits_frame,
            text=self._app.i18n.t("welcome_credits_desc"),
            anchor="w",
            wraplength=320,
            justify="left",
        )
        credits_label.pack(fill="x", padx=15, pady=(2, 10))

        credits_btn = ctk.CTkButton(
            credits_frame,
            text=self._app.i18n.t("welcome_credits_btn"),
            command=self._open_credits_site,
        )
        credits_btn.pack(fill="x", padx=15, pady=(0, 10))

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

    def _open_translation_site(self):
        import webbrowser
        webbrowser.open("https://crowdin.com/project/hlpatcher")

    def _open_credits_site(self):
        import webbrowser
        webbrowser.open("https://hlpatcher.kzl21.ovh/#thanks-to")
