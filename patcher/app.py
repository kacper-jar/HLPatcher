from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

import customtkinter as ctk

from patcher.core import EngineType, GameDetector, PatchContext
from patcher.ui import (
    AllPatchedPage,
    BasePage,
    FailurePage,
    LibraryPage,
    NavigationFooter,
    NoGamesPage,
    OptionsPage,
    PageHeader,
    ProgressPage,
    SelectionPage,
    SuccessPage,
    WarningPage,
    WelcomePage,
)

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("HLPatcher")
        self.geometry("420x620")
        self.minsize(420, 620)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_quit)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.context = PatchContext(
            script_dir=Path(__file__).resolve().parent.parent,
        )
        self.patching_error = ""

        self._header = PageHeader(self)
        self._header.pack(fill="x")

        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True)

        self.footer = NavigationFooter(
            self,
            on_quit=self._on_quit,
            on_back=self._on_back,
            on_next=self._on_next,
        )
        self.footer.pack(fill="x")

        self._pages: dict[str, type] = {}
        self._page_instances: dict[str, BasePage] = {}
        self._current_page_key: str = ""
        self._history: list[str] = []

        self._register_pages()
        self._check_xcode_cli_tools()
        self.show_page("welcome")

    def _register_pages(self):
        self._pages = {
            "welcome": WelcomePage,
            "library": LibraryPage,
            "selection": SelectionPage,
            "options": OptionsPage,
            "warning": WarningPage,
            "progress": ProgressPage,
            "success": SuccessPage,
            "failure": FailurePage,
            "no_games": NoGamesPage,
            "all_patched": AllPatchedPage,
        }

    def _check_xcode_cli_tools(self):
        try:
            subprocess.run(
                ["xcode-select", "-p"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            from tkinter import messagebox
            messagebox.showerror(
                "Xcode CLI Tools Missing",
                "Xcode Command Line Tools not found.\n\n"
                "Please install them using 'xcode-select --install' "
                "and relaunch HLPatcher.",
            )
            sys.exit(1)

    def show_page(self, page_key: str):
        if self._current_page_key and self._current_page_key in self._page_instances:
            current = self._page_instances[self._current_page_key]
            current.on_leave()
            current.pack_forget()

        if page_key not in self._page_instances:
            page_class = self._pages[page_key]
            self._page_instances[page_key] = page_class(self._content_frame, self)

        page = self._page_instances[page_key]
        page.pack(fill="both", expand=True)
        page.on_enter()

        self._header.set_title(page.get_title())
        self.footer.set_back_visible(page.show_back_button())
        self.footer.set_next_visible(page.show_next_button())
        self.footer.set_next_text(page.get_next_button_text())
        self.footer.set_next_enabled(True)
        self.footer.set_back_enabled(True)

        self._current_page_key = page_key

    def _invalidate_page(self, page_key: str):
        if page_key in self._page_instances:
            self._page_instances[page_key].destroy()
            del self._page_instances[page_key]

    def _on_quit(self):
        if self._current_page_key == "progress":
            page = self._page_instances.get(self._current_page_key)
            if hasattr(page, "stop_patching"):
                page.stop_patching()

        if self.context.working_dir.exists():
            shutil.rmtree(self.context.working_dir, ignore_errors=True)
        self.destroy()

    def _on_back(self):
        if not self._current_page_key:
            return

        page = self._page_instances.get(self._current_page_key)
        if not page or not page.can_go_back():
            return

        back_key = page.get_back_page_key()
        if back_key:
            if self._history:
                self._history.pop()
            self.show_page(back_key)

    def _on_next(self):
        if not self._current_page_key:
            return

        page = self._page_instances.get(self._current_page_key)
        if not page or not page.can_go_next():
            return

        page.on_leave()
        next_key = page.get_next_page_key()

        if next_key == "scan_and_route":
            self._scan_and_route()
            return

        if next_key == "check_source_warning":
            self._check_source_warning()
            return

        if next_key:
            self._history.append(self._current_page_key)
            self.show_page(next_key)

    def _scan_and_route(self):
        self._invalidate_page("selection")
        self._invalidate_page("no_games")
        self._invalidate_page("all_patched")

        detector = GameDetector(self.context.steam_library_path)
        games = detector.scan()
        self.context.games = games

        if not games:
            self.show_page("no_games")
            return

        all_patched = all(g.all_patched for g in games)
        if all_patched:
            self.show_page("all_patched")
            return

        self._history.append(self._current_page_key)
        self.show_page("selection")

    def _check_source_warning(self):
        has_source = any(
            c.engine_type == EngineType.SOURCE
            for c in self.context.selected_components
        )
        self._history.append(self._current_page_key)
        if has_source:
            self.show_page("warning")
        else:
            self.show_page("progress")
