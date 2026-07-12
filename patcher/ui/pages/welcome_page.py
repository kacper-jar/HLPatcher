import customtkinter as ctk
import patcher
from patcher.ui import BasePage, PageRoute


class WelcomePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        description = (
            "HLPatcher makes Half-Life and other Valve games\n"
            "playable on modern ARM Macs that only support\n"
            "64-bit applications."
        )
        desc_label = ctk.CTkLabel(self, text=description, justify="center")
        desc_label.pack(pady=(0, 10))

        credits_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        credits_frame.pack(fill="x", padx=20, pady=5)

        credits_title = ctk.CTkLabel(
            credits_frame,
            text="Thanks to:",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        credits_title.pack(fill="x", padx=15, pady=(10, 5))

        credits = [
            "Flying with Gauss team for Xash3D FWGS and HLSDK Portable",
            "Velaron for Counter-Strike 1.6 reverse-engineered client",
            "Nillerusr for Source Engine modifications",
        ]

        for credit in credits:
            credit_label = ctk.CTkLabel(
                credits_frame,
                text=f"- {credit}",
                anchor="w",
                wraplength=320,
                justify="left",
            )
            credit_label.pack(fill="x", padx=15, pady=2)

        closing_label = ctk.CTkLabel(
            credits_frame,
            text="Without them, HLPatcher wouldn't exist.",
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        closing_label.pack(fill="x", padx=15, pady=(5, 10))

    def get_title(self) -> str:
        return f"Welcome to HLPatcher ({patcher.__version__})"

    def show_back_button(self) -> bool:
        return False

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.LIBRARY
