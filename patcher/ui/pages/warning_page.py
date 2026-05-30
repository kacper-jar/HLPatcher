import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class WarningPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        warning_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        warning_frame.pack(fill="x", padx=20, pady=10)

        warning_text = (
            "Before proceeding, you MUST switch your game\n"
            "installations to the correct legacy branches.\n\n"
            "Set these games in this order (to avoid resets),\n"
            "skipping any you are not patching:\n"
            "1. Half-Life: Source\n"
            "2. Half-Life 2: Episode One\n"
            "3. Half-Life 2: Episode Two\n"
            "4. Half-Life 2: Lost Coast\n"
            "5. Half-Life 2\n"
            "6. Portal\n\n"
            "To do this:\n"
            "1. Open Steam\n"
            "2. Right-click Game -> Properties\n"
            "3. Go to Betas\n"
            "4. Select 'steam_legacy' (or 'beta' for Portal)\n\n"
            "Failure to do so will result in a broken game.\n\n"
            "Click Next once the branches are changed and Steam\n"
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
        return "Before You Continue!"

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.PROGRESS

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.OPTIONS

    def get_next_button_text(self) -> str:
        return "Patch"
