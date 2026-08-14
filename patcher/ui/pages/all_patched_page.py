import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class AllPatchedPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        desc_text = self._app.i18n.t("all_patched_desc")

        desc_label = ctk.CTkLabel(
            self,
            text=desc_text,
            justify="center",
        )
        desc_label.pack(pady=10)

    def get_title(self) -> str:
        return self._app.i18n.t("all_patched_title")

    def show_next_button(self) -> bool:
        return False

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.LIBRARY
