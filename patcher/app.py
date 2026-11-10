import logging
import shutil
import threading
from pathlib import Path
from queue import Empty, SimpleQueue
import customtkinter as ctk

import patcher
from patcher.core import (
    AppConfig,
    EngineType,
    GameDetector,
    GuideRegistry,
    I18n,
    PatchContext,
    Planner,
    UpdateInfo,
    Updater,
)
from patcher.ui import NavigationFooter, PageHeader, PageRoute, Router

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self._quitting = False

        self.title("HLPatcher")
        self.geometry("420x620")
        self.minsize(420, 620)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.createcommand("::tk::mac::Quit", self._on_quit)

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
        self.failure_report: Path | None = None
        self.update_info: UpdateInfo | None = None
        self._update_check_job: str | None = None

        locales_dir = self.context.script_dir / "data" / "locales"
        self.i18n = I18n(locales_dir)
        self.i18n.on_language_changed = self._on_language_changed

        guides_dir = self.context.script_dir / "data" / "guides"
        self.guide_registry = GuideRegistry(guides_dir)

        self._update_results: SimpleQueue[UpdateInfo | None] | None = self._start_update_check()

        self._header = PageHeader(self)
        self._header.pack(fill="x")

        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True, pady=(20, 0))

        self.footer = NavigationFooter(
            self,
            on_quit=self._on_quit,
            on_back=lambda: self.router.go_back(),
            on_next=lambda: self.router.go_next(),
        )
        self.footer.retranslate(self.i18n)
        self.footer.pack(fill="x")

        self.router = Router(self, self._content_frame, self._header, self.footer)
        self.router.route_interceptor = self._on_route_intercept
        self.router.show_page(PageRoute.WELCOME)

    def report_callback_exception(self, exc, val, tb):
        logger.error("Unhandled error in the interface", exc_info=(exc, val, tb))

    def _on_language_changed(self, lang_code: str):
        self.footer.retranslate(self.i18n)

        current = self.router.current_page_key
        self.router.invalidate_page(current)
        self.router.show_page(current)
        if current == PageRoute.WELCOME and self._update_check_job is not None:
            self.footer.set_next_enabled(False)

    def _start_update_check(self) -> SimpleQueue[UpdateInfo | None]:
        results: SimpleQueue[UpdateInfo | None] = SimpleQueue()

        def check():
            results.put(Updater().check_for_update(patcher.__version__))

        threading.Thread(target=check, daemon=True).start()
        return results

    def _resume_after_update_check(self):
        self._update_check_job = None
        if self.router.current_page_key == PageRoute.WELCOME:
            self.router.go_next()

    def _on_route_intercept(self, current_key: PageRoute, next_key: PageRoute) -> PageRoute | None:
        if next_key == PageRoute.SCAN_AND_ROUTE:
            self._scan_and_route()
            return PageRoute.HALT

        if next_key == PageRoute.CHECK_DOWNGRADE:
            self._check_downgrade_needed()
            return PageRoute.HALT

        if current_key == PageRoute.SELECTION and next_key == PageRoute.OPTIONS:
            if Planner(self.context.games).find_missing_dependencies(self.context.selected_components):
                return PageRoute.HL2_REQUIRED

        if current_key == PageRoute.WELCOME:
            if self._update_results is not None:
                try:
                    self.update_info = self._update_results.get_nowait()
                except Empty:
                    self.footer.set_next_enabled(False)
                    if self._update_check_job is None:
                        self._update_check_job = self.after(100, self._resume_after_update_check)
                    return PageRoute.HALT
                self._update_results = None

            if self.update_info and self.update_info.update_available:
                return PageRoute.UPDATE_AVAILABLE

        return None

    def _on_quit(self):
        if self._quitting:
            return
        self._quitting = True

        if self.router.current_page_key == PageRoute.PROGRESS:
            page = self.router.get_current_page()
            page.stop_patching()
            self._destroy_when_stopped(page)
            return

        self._cleanup_and_destroy()

    def _destroy_when_stopped(self, page):
        if page.is_patching():
            self.after(100, self._destroy_when_stopped, page)
            return
        self._cleanup_and_destroy()

    def _cleanup_and_destroy(self):
        if self._update_check_job is not None:
            self.after_cancel(self._update_check_job)
        if not self.config.debug and self.context.working_dir.exists():
            shutil.rmtree(self.context.working_dir, ignore_errors=True)
        self.destroy()

    def _scan_and_route(self):
        self.router.invalidate_page(PageRoute.SELECTION)
        self.router.invalidate_page(PageRoute.NO_GAMES)
        self.router.invalidate_page(PageRoute.ALL_PATCHED)

        detector = GameDetector(self.context.steam_library_path)
        games = detector.scan()
        self.context.games = games

        if not games:
            self.router.show_page(PageRoute.NO_GAMES)
            return

        all_patched = all(g.all_patched for g in games)
        if all_patched:
            self.router.show_page(PageRoute.ALL_PATCHED)
            return

        self.router.show_page(PageRoute.SELECTION)

    def _check_downgrade_needed(self):
        needs_downgrade = any(
            bool(c.downgrade_requires)
            for c in self.context.selected_components
        )
        if needs_downgrade:
            self.router.show_page(PageRoute.DOWNGRADE)
        else:
            self.router.show_page(PageRoute.PROGRESS)
