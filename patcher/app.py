from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path

import customtkinter as ctk

from patcher.core import AppConfig, EngineType, GameDetector, PatchContext, UpdateInfo, Updater
from patcher.ui import (
    BasePage,
    NavigationFooter,
    PageHeader,
    Router
)

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config

        self.title("HLPatcher")
        self.geometry("420x620")
        self.minsize(420, 620)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_quit)

        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        self.after(200, lambda: self.attributes("-topmost", False))

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.context = PatchContext(
            script_dir=Path(__file__).resolve().parent.parent,
        )
        self.patching_error = ""
        self.update_info: UpdateInfo | None = None

        self._start_update_check()

        self._header = PageHeader(self)
        self._header.pack(fill="x")

        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True, pady=(20, 0))

        self.footer = NavigationFooter(
            self,
            on_quit=self._on_quit,
            on_back=lambda: getattr(self, 'router', None) and self.router.go_back(),
            on_next=lambda: getattr(self, 'router', None) and self.router.go_next(),
        )
        self.footer.pack(fill="x")

        self.router = Router(self, self._content_frame, self._header, self.footer)
        self.router.route_interceptor = self._on_route_intercept
        self.router.show_page("welcome")

    def _start_update_check(self):
        def check():
            import patcher

            updater = Updater()
            self.update_info = updater.check_for_update(patcher.__version__)

        threading.Thread(target=check, daemon=True).start()

    def _on_route_intercept(self, current_key: str, next_key: str) -> str | None:
        if next_key == "scan_and_route":
            self._scan_and_route()
            return "HALT"

        if next_key == "check_source_warning":
            self._check_source_warning()
            return "HALT"

        if (
                current_key == "welcome"
                and self.update_info
                and self.update_info.update_available
        ):
            return "update_available"

        return None

    def _on_quit(self):
        if getattr(self, "router", None) and self.router.current_page_key == "progress":
            page = self.router.get_current_page()
            if hasattr(page, "stop_patching"):
                page.stop_patching()

        if not self.config.debug and self.context.working_dir.exists():
            shutil.rmtree(self.context.working_dir, ignore_errors=True)
        self.destroy()

    def _scan_and_route(self):
        self.router.invalidate_page("selection")
        self.router.invalidate_page("no_games")
        self.router.invalidate_page("all_patched")

        detector = GameDetector(self.context.steam_library_path)
        games = detector.scan()
        self.context.games = games

        if not games:
            self.router.show_page("no_games")
            return

        all_patched = all(g.all_patched for g in games)
        if all_patched:
            self.router.show_page("all_patched")
            return

        self.router.push_history(self.router.current_page_key)
        self.router.show_page("selection")

    def _check_source_warning(self):
        has_source = any(
            c.engine_type == EngineType.SOURCE
            for c in self.context.selected_components
        )
        self.router.push_history(self.router.current_page_key)
        if has_source:
            self.router.show_page("warning")
        else:
            self.router.show_page("progress")
