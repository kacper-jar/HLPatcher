import customtkinter as ctk
from patcher.ui import BasePage


class WarningPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        warning_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        warning_frame.pack(fill="x", padx=20, pady=10)

        warning_text = (
            "Before proceeding, you MUST switch your Half-Life 2\n"
            "installation to the 'steam_legacy' branch.\n\n"
            "To do this:\n"
            "1. Open Steam\n"
            "2. Right-click Half-Life 2 -> Properties\n"
            "3. Go to Betas\n"
            "4. Select 'steam_legacy - Pre-20th Anniversary Build'\n\n"
            "Failure to do so will result in a broken game.\n\n"
            "Click Next once the branch is changed and Steam\n"
            "finishes downgrading the files."
        )

        warning_label = ctk.CTkLabel(
            warning_frame,
            text=warning_text,
            justify="left",
            anchor="w",
            wraplength=340,
        )
        warning_label.pack(fill="x", padx=15, pady=15)

    def get_title(self) -> str:
        return "Before you continue!"

    def get_next_page_key(self) -> str:
        return "progress"

    def get_back_page_key(self) -> str:
        return "options"
