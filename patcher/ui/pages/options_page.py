import customtkinter as ctk
from patcher.ui import BasePage
from patcher.core import PatchMode


class OptionsPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        mode_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        mode_frame.pack(fill="x", padx=20, pady=10)

        mode_title = ctk.CTkLabel(
            mode_frame,
            text="Patch Mode",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        mode_title.pack(fill="x", padx=15, pady=(10, 5))

        self._mode_var = ctk.StringVar(value=PatchMode.LATEST.value)

        latest_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Latest",
            variable=self._mode_var,
            value=PatchMode.LATEST.value,
        )
        latest_radio.pack(fill="x", padx=15, pady=2)

        latest_desc = ctk.CTkLabel(
            mode_frame,
            text="Uses the most up-to-date code. May be unstable.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        )
        latest_desc.pack(fill="x", padx=35, pady=(0, 5))

        stable_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Stable",
            variable=self._mode_var,
            value=PatchMode.STABLE.value,
        )
        stable_radio.pack(fill="x", padx=15, pady=2)

        stable_desc = ctk.CTkLabel(
            mode_frame,
            text="Uses specific versions known to work. Recommended if Latest fails.",
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
            text="Backup",
            font=ctk.CTkFont(weight="bold"),
            anchor="w",
        )
        backup_title.pack(fill="x", padx=15, pady=(10, 5))

        self._backup_var = ctk.BooleanVar(value=True)

        backup_checkbox = ctk.CTkCheckBox(
            backup_frame,
            text="Create backup before patching",
            variable=self._backup_var,
        )
        backup_checkbox.pack(fill="x", padx=15, pady=5)

        backup_desc = ctk.CTkLabel(
            backup_frame,
            text="Backup will be stored in your Documents folder.",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="w",
        )
        backup_desc.pack(fill="x", padx=35, pady=(0, 10))

    def on_leave(self):
        self._app.context.patch_mode = PatchMode(self._mode_var.get())
        self._app.context.create_backup = self._backup_var.get()

    def get_title(self) -> str:
        return "Patching Options"

    def get_next_page_key(self) -> str:
        return "check_source_warning"

    def get_back_page_key(self) -> str:
        return "selection"
