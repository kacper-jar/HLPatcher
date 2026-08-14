import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class WarningPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        warning_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        warning_frame.pack(fill="x", padx=20, pady=10)

        warning_text = self._app.i18n.t("warning_text")

        warning_label = ctk.CTkLabel(
            warning_frame,
            text=warning_text,
            justify="left",
            anchor="w",
            wraplength=340,
        )
        warning_label.pack(fill="x", padx=15, pady=15)

    def get_title(self) -> str:
        return self._app.i18n.t("warning_title")

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.PROGRESS

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.OPTIONS

    def get_next_button_text(self) -> str:
        return self._app.i18n.t("btn_patch")
