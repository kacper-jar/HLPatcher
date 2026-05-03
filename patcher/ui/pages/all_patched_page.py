import customtkinter as ctk
from patcher.ui import BasePage


class AllPatchedPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        desc_text = (
            "All detected Half-Life components are already\n"
            "patched! No further action is required.\n\n"
            "If you're experiencing issues, try reinstalling\n"
            "the game through Steam and running HLPatcher again."
        )

        desc_label = ctk.CTkLabel(
            self,
            text=desc_text,
            justify="center",
        )
        desc_label.pack(pady=10)

    def get_title(self) -> str:
        return "All Games Already Patched"

    def show_next_button(self) -> bool:
        return False

    def get_back_page_key(self) -> str:
        return "library"
