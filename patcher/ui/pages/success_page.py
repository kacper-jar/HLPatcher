import customtkinter as ctk
from patcher.ui import BasePage


class SuccessPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        warning_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        warning_frame.pack(fill="x", padx=20, pady=10)

        warning_title = ctk.CTkLabel(
            warning_frame,
            text=self._app.i18n.t("success_warning_title"),
            font=ctk.CTkFont(weight="bold"),
            text_color="#f39c12",
            anchor="w",
        )
        warning_title.pack(fill="x", padx=15, pady=(10, 5))

        warning_label = ctk.CTkLabel(
            warning_frame,
            text=self._app.i18n.t("success_warning_text"),
            justify="left",
            anchor="w",
            wraplength=340,
        )
        warning_label.pack(fill="x", padx=15, pady=(0, 15))

        enjoy_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("success_enjoy"),
            font=ctk.CTkFont(size=14),
        )
        enjoy_label.pack(pady=10)

    def get_title(self) -> str:
        return self._app.i18n.t("success_title")

    def show_back_button(self) -> bool:
        return False

    def show_next_button(self) -> bool:
        return False
