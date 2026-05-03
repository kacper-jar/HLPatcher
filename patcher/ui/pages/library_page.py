import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from patcher.ui import BasePage

DEFAULT_STEAM_PATH = Path.home() / "Library" / "Application Support" / "Steam" / "steamapps" / "common"


class LibraryPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        hint_label = ctk.CTkLabel(
            self,
            text="Select the folder where your GoldSrc and Source games are installed.\n"
                 "If downloaded from Steam, this is the 'common' folder\n"
                 "inside your Steam library directory.",
            justify="center",
            font=ctk.CTkFont(size=12),
        )
        hint_label.pack(pady=(0, 15))

        path_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        path_frame.pack(fill="x", padx=20, pady=10)

        self._path_var = ctk.StringVar()

        self._path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self._path_var,
            width=300,
        )
        self._path_entry.pack(side="left", fill="x", expand=True, padx=(15, 5), pady=15)

        browse_button = ctk.CTkButton(
            path_frame,
            text="...",
            width=80,
            command=self._browse,
        )
        browse_button.pack(side="right", padx=(5, 15), pady=15)

        self._error_label = ctk.CTkLabel(
            self,
            text="",
            text_color="#e74c3c",
            font=ctk.CTkFont(size=12),
        )
        self._error_label.pack(pady=(10, 0))

    def on_enter(self):
        if not self._path_var.get():
            if DEFAULT_STEAM_PATH.exists():
                self._path_var.set(str(DEFAULT_STEAM_PATH))
            else:
                self._path_var.set("")
        self._error_label.configure(text="")

    def get_title(self) -> str:
        return "Select Your Games Folder"

    def _browse(self):
        initial = self._path_var.get()
        if not Path(initial).exists():
            initial = str(Path.home())

        folder = filedialog.askdirectory(
            title="Select games folder",
            initialdir=initial,
        )
        if folder:
            self._path_var.set(folder)
            self._error_label.configure(text="")

    def can_go_next(self) -> bool:
        path = Path(self._path_var.get())
        if not path.is_dir():
            self._error_label.configure(text="Selected path does not exist.")
            return False
        self._error_label.configure(text="")
        return True

    def on_leave(self):
        self._app.context.steam_library_path = Path(self._path_var.get())

    def get_next_page_key(self) -> str:
        return "scan_and_route"

    def get_back_page_key(self) -> str:
        return "welcome"
