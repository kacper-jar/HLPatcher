import customtkinter as ctk
from patcher.ui import BasePage


class NoGamesPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        desc_text = (
            "No supported Half-Life or Source engine games were\n"
            "found in the selected Steam library folder.\n\n"
            "Make sure you selected the correct 'common' folder\n"
            "and that the games are installed."
        )

        desc_label = ctk.CTkLabel(
            self,
            text=desc_text,
            justify="center",
        )
        desc_label.pack(pady=10)

    def get_title(self) -> str:
        return "No Compatible Games Found"

    def show_next_button(self) -> bool:
        return False

    def get_back_page_key(self) -> str:
        return "library"
