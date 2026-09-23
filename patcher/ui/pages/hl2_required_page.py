import customtkinter as ctk

from patcher.ui.base_page import BasePage
from patcher.ui.page_route import PageRoute


class Hl2RequiredPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        desc_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("hl2_required_text"),
            justify="center",
            wraplength=350
        )
        desc_label.pack(pady=10)

    def get_title(self) -> str:
        return self._app.i18n.t("hl2_required_title")

    def get_next_page_key(self) -> PageRoute | None:
        return None

    def show_next_button(self) -> bool:
        return False

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.SELECTION
