from __future__ import annotations

import customtkinter as ctk
from abc import abstractmethod


class BasePage(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._app = app

    @abstractmethod
    def get_title(self) -> str:
        pass

    def on_enter(self):
        pass

    def on_leave(self):
        pass

    def can_go_next(self) -> bool:
        return True

    def can_go_back(self) -> bool:
        return True

    def get_next_page_key(self) -> str | None:
        return None

    def get_back_page_key(self) -> str | None:
        return None

    def show_back_button(self) -> bool:
        return True

    def show_next_button(self) -> bool:
        return True

    def get_next_button_text(self) -> str:
        return "Next"


class PageHeader(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=60, corner_radius=0, **kwargs)
        self.pack_propagate(False)

        self._title_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self._title_label.pack(fill="x", padx=20, pady=15)

    def set_title(self, title: str):
        self._title_label.configure(text=title)


class NavigationFooter(ctk.CTkFrame):
    def __init__(self, parent, on_quit, on_back, on_next, **kwargs):
        super().__init__(parent, height=50, corner_radius=0, **kwargs)
        self.pack_propagate(False)

        self.columnconfigure(1, weight=1)

        self._quit_button = ctk.CTkButton(
            self,
            text="Quit",
            width=80,
            command=on_quit,
            fg_color="#c0392b",
            hover_color="#e74c3c",
        )
        self._quit_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self._back_button = ctk.CTkButton(
            self,
            text="Back",
            width=80,
            command=on_back,
            fg_color="gray40",
            hover_color="gray50",
        )
        self._back_button.grid(row=0, column=2, padx=(0, 5), pady=10, sticky="e")

        self._next_button = ctk.CTkButton(
            self,
            text="Next",
            width=80,
            command=on_next,
        )
        self._next_button.grid(row=0, column=3, padx=10, pady=10, sticky="e")

    def set_back_visible(self, visible: bool):
        if visible:
            self._back_button.grid(row=0, column=2, padx=(0, 5), pady=10, sticky="e")
        else:
            self._back_button.grid_remove()

    def set_next_visible(self, visible: bool):
        if visible:
            self._next_button.grid(row=0, column=3, padx=10, pady=10, sticky="e")
        else:
            self._next_button.grid_remove()

    def set_next_text(self, text: str):
        self._next_button.configure(text=text)

    def set_next_enabled(self, enabled: bool):
        self._next_button.configure(state="normal" if enabled else "disabled")

    def set_back_enabled(self, enabled: bool):
        self._back_button.configure(state="normal" if enabled else "disabled")
