import customtkinter as ctk
from patcher.ui import BasePage, PageRoute
from patcher.core import PatchMode, EngineType


class OptionsPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        mode_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        mode_frame.pack(fill="x", padx=20, pady=10)

        mode_title = ctk.CTkLabel(
            mode_frame,
            text=self._app.i18n.t("options_mode_title"),
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        mode_title.pack(fill="x", padx=15, pady=(10, 5))

        self._mode_var = ctk.StringVar(value=PatchMode.LATEST.value)

        latest_radio = ctk.CTkRadioButton(
            mode_frame,
            text=self._app.i18n.t("options_mode_latest"),
            variable=self._mode_var,
            value=PatchMode.LATEST.value,
        )
        latest_radio.pack(fill="x", padx=15, pady=2)

        latest_desc = ctk.CTkLabel(
            mode_frame,
            text=self._app.i18n.t("options_mode_latest_desc"),
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        )
        latest_desc.pack(fill="x", padx=35, pady=(0, 5))

        stable_radio = ctk.CTkRadioButton(
            mode_frame,
            text=self._app.i18n.t("options_mode_stable"),
            variable=self._mode_var,
            value=PatchMode.STABLE.value,
        )
        stable_radio.pack(fill="x", padx=15, pady=2)

        stable_desc = ctk.CTkLabel(
            mode_frame,
            text=self._app.i18n.t("options_mode_stable_desc"),
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
            wraplength=320,
        )
        stable_desc.pack(fill="x", padx=35, pady=(0, 10))

        backup_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        backup_frame.pack(fill="x", padx=20, pady=10)

        backup_title = ctk.CTkLabel(
            backup_frame,
            text=self._app.i18n.t("options_backup_title"),
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        backup_title.pack(fill="x", padx=15, pady=(10, 5))

        self._backup_var = ctk.BooleanVar(value=True)

        backup_checkbox = ctk.CTkCheckBox(
            backup_frame,
            text=self._app.i18n.t("options_backup_check"),
            variable=self._backup_var,
        )
        backup_checkbox.pack(fill="x", padx=15, pady=5)

        backup_desc = ctk.CTkLabel(
            backup_frame,
            text=self._app.i18n.t("options_backup_desc"),
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        )
        backup_desc.pack(fill="x", padx=35, pady=(0, 10))

    def on_leave(self):
        self._app.context.patch_mode = PatchMode(self._mode_var.get())
        self._app.context.create_backup = self._backup_var.get()

    def get_title(self) -> str:
        return self._app.i18n.t("options_title")

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.LIMITATIONS

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.SELECTION

    def get_next_button_text(self) -> str:
        return self._app.i18n.t("btn_next")
