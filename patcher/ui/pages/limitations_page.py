import customtkinter as ctk
import webbrowser
from patcher.ui import BasePage, PageRoute


class LimitationsPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        multiplayer_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        multiplayer_frame.pack(fill="x", padx=20, pady=5)

        multiplayer_title = ctk.CTkLabel(
            multiplayer_frame,
            text=self._app.i18n.t("limitations_multiplayer_title"),
            font=ctk.CTkFont(weight="bold"),
            text_color="#f39c12",
            anchor="w",
        )
        multiplayer_title.pack(fill="x", padx=15, pady=(10, 0))

        multiplayer_label = ctk.CTkLabel(
            multiplayer_frame,
            text=self._app.i18n.t("limitations_multiplayer_desc"),
            anchor="w",
            wraplength=320,
            justify="left",
        )
        multiplayer_label.pack(fill="x", padx=15, pady=(2, 10))

        singleplayer_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        singleplayer_frame.pack(fill="x", padx=20, pady=5)

        singleplayer_title = ctk.CTkLabel(
            singleplayer_frame,
            text=self._app.i18n.t("limitations_singleplayer_title"),
            font=ctk.CTkFont(weight="bold"),
            text_color="#f39c12",
            anchor="w",
        )
        singleplayer_title.pack(fill="x", padx=15, pady=(10, 0))

        singleplayer_label = ctk.CTkLabel(
            singleplayer_frame,
            text=self._app.i18n.t("limitations_singleplayer_desc"),
            anchor="w",
            wraplength=320,
            justify="left",
        )
        singleplayer_label.pack(fill="x", padx=15, pady=(2, 10))

        issues_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        issues_frame.pack(fill="x", padx=20, pady=5)

        issues_title = ctk.CTkLabel(
            issues_frame,
            text=self._app.i18n.t("limitations_issues_title"),
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        issues_title.pack(fill="x", padx=15, pady=(10, 5))

        issues_btn = ctk.CTkButton(
            issues_frame,
            text=self._app.i18n.t("limitations_issues_btn"),
            command=self._open_issues_site,
        )
        issues_btn.pack(fill="x", padx=15, pady=(0, 10))

    def get_title(self) -> str:
        return self._app.i18n.t("limitations_title")

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.CHECK_DOWNGRADE

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.OPTIONS

    def get_next_button_text(self) -> str:
        needs_downgrade = any(
            bool(c.requires)
            for c in self._app.context.selected_components
        )
        return self._app.i18n.t("btn_next") if needs_downgrade else self._app.i18n.t("btn_patch")

    def _open_issues_site(self):
        webbrowser.open("https://github.com/kzl21/HLPatcher/issues")
