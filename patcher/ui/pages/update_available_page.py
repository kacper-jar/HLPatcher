import webbrowser
import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class UpdateAvailablePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        msg = (
            "A new version of HLPatcher is available!\n\n"
            "Using an outdated version may lead to broken game installs "
            "or compatibility issues with modern macOS versions."
        )

        msg_label = ctk.CTkLabel(
            self,
            text=msg,
            justify="center",
            wraplength=350,
            font=ctk.CTkFont(size=14),
        )
        msg_label.pack(pady=(40, 20))

        if self._app.update_info:
            version_text = f"Latest version: v{self._app.update_info.latest_version}"
            version_label = ctk.CTkLabel(
                self,
                text=version_text,
                font=ctk.CTkFont(weight="bold"),
            )
            version_label.pack(pady=(0, 20))

        self.github_button = ctk.CTkButton(
            self,
            text="Open GitHub Releases",
            command=self._open_github,
            fg_color="#27ae60",
            hover_color="#2ecc71",
        )
        self.github_button.pack(pady=20)

        skip_label = ctk.CTkLabel(
            self,
            text="You can proceed without updating, but it is not recommended.",
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
        return "Update Available"

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.LIBRARY

    def get_next_button_text(self) -> str:
        return "Proceed"

    def show_back_button(self) -> bool:
        return True

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.WELCOME
