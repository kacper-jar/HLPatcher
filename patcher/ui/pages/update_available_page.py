import webbrowser
import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class UpdateAvailablePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        msg_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("update_msg"),
            justify="center",
            wraplength=350,
            font=ctk.CTkFont(size=14),
        )
        msg_label.pack(pady=(40, 20))

        if self._app.update_info:
            version_text = self._app.i18n.t("update_latest_version", version=self._app.update_info.latest_version)
            version_label = ctk.CTkLabel(
                self,
                text=version_text,
                font=ctk.CTkFont(weight="bold"),
            )
            version_label.pack(pady=(0, 20))

        self.github_button = ctk.CTkButton(
            self,
            text=self._app.i18n.t("update_btn"),
            command=self._open_github,
            fg_color="#27ae60",
            hover_color="#2ecc71",
        )
        self.github_button.pack(pady=20)

        skip_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("update_skip"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        skip_label.pack(side="bottom", pady=20)

    def _open_github(self):
        url = (
            self._app.update_info.release_url
            if self._app.update_info
            else "https://github.com/kacper-jar/HLPatcher/releases"
        )
        webbrowser.open(url)

    def get_title(self) -> str:
        return self._app.i18n.t("update_title")

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.LIBRARY

    def get_next_button_text(self) -> str:
        return self._app.i18n.t("btn_proceed")

    def show_back_button(self) -> bool:
        return True

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.WELCOME
