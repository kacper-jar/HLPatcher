import hashlib
import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class WarningPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        warning_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=8)
        warning_frame.pack(fill="x", padx=20, pady=10)

        warning_text = self._app.i18n.t("warning_text")

        warning_label = ctk.CTkLabel(
            warning_frame,
            text=warning_text,
            justify="left",
            anchor="w",
            wraplength=340,
        )
        warning_label.pack(fill="x", padx=15, pady=15)

        self._check_job = None

    def on_enter(self):
        if hasattr(self._app, "footer") and self._app.footer:
            self._app.footer.set_next_enabled(False)
        self._check_job = self.after(100, self._check_downgrades)

    def on_leave(self):
        if self._check_job:
            self.after_cancel(self._check_job)
            self._check_job = None

    def _check_downgrades(self):
        all_match = True
        context = self._app.context

        for component in context.selected_components:
            if not component.requires:
                continue

            game_path = None
            for game in context.games:
                if component in game.components:
                    game_path = game.path
                    break

            if not game_path:
                continue

            for filename, expected_hash in component.requires.items():
                file_path = game_path / filename
                if not file_path.is_file():
                    all_match = False
                    break

                if expected_hash == "":
                    continue

                try:
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    if file_hash != expected_hash:
                        all_match = False
                        break
                except Exception:
                    all_match = False
                    break

            if not all_match:
                break

        if hasattr(self._app, "footer") and self._app.footer:
            self._app.footer.set_next_enabled(all_match)

        self._check_job = self.after(1000, self._check_downgrades)

    def get_title(self) -> str:
        return self._app.i18n.t("warning_title")

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.PROGRESS

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.OPTIONS

    def get_next_button_text(self) -> str:
        return self._app.i18n.t("btn_patch")
