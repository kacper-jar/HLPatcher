import webbrowser
import customtkinter as ctk
from patcher.ui import BasePage


class FailurePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        self._error_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        self._error_frame.pack(fill="x", padx=20, pady=10)

        error_title = ctk.CTkLabel(
            self._error_frame,
            text="Error Details",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        error_title.pack(fill="x", padx=15, pady=(10, 5))

        self._error_label = ctk.CTkLabel(
            self._error_frame,
            text="",
            justify="left",
            anchor="w",
            wraplength=340,
            text_color="#e74c3c",
        )
        self._error_label.pack(fill="x", padx=15, pady=(0, 15))

        help_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        help_frame.pack(fill="x", padx=20, pady=10)

        help_text = (
            "Please try patching again using 'Stable Mode'.\n"
            "If the issue persists, please copy the error details above along with your entire "
            "terminal output and create a new issue on GitHub repository using the button below."
        )

        help_label = ctk.CTkLabel(
            help_frame,
            text=help_text,
            justify="center",
            font=ctk.CTkFont(size=12),
            wraplength=340,
        )
        help_label.pack(pady=(10, 10), padx=15)

        issue_button = ctk.CTkButton(
            help_frame,
            text="Create New Issue on GitHub",
            command=self._open_github_issue,
        )
        issue_button.pack(pady=5)

        note_label = ctk.CTkLabel(
            help_frame,
            text="Note: GitHub account is required to submit an issue.",
            font=ctk.CTkFont(size=10),
        )
        note_label.pack(pady=(0, 10))

    def _open_github_issue(self):
        webbrowser.open("https://github.com/kacper-jar/HLPatcher/issues/new?template=bug_patcher.md")

    def on_enter(self):
        error_message = getattr(self._app, "patching_error", "Unknown error occurred.")
        self._error_label.configure(text=error_message)

    def get_title(self) -> str:
        return "Patching Failed"

    def show_back_button(self) -> bool:
        return False

    def show_next_button(self) -> bool:
        return False
