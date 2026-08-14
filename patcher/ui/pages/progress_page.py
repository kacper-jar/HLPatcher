import customtkinter as ctk
import time
import threading
from patcher.ui import BasePage, PageRoute
from patcher.core import EngineType, Game, Patcher


class ProgressPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        self._status_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("progress_preparing"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._status_label.pack(pady=(20, 10))

        self._progress_bar = ctk.CTkProgressBar(self, width=340)
        self._progress_bar.pack(pady=10, padx=20)
        self._progress_bar.set(0)

        self._step_progress_bar = ctk.CTkProgressBar(self, width=340)
        self._step_progress_bar.pack(pady=(10, 10), padx=20)
        self._step_progress_bar.set(0)

        self._step_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("progress_step_format", current=0, total=0),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._step_label.pack(pady=(0, 10))

        self._elapsed_time_label = ctk.CTkLabel(
            self,
            text=self._app.i18n.t("progress_time_format", mins=0, secs=0),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray70"
        )
        self._elapsed_time_label.pack(pady=(5, 10))

        self._patching_thread = None
        self._patching_complete = False
        self._patching_error = None

    def on_enter(self):
        self._patching_complete = False
        self._patching_error = None
        self._progress_bar.set(0)
        self._step_progress_bar.set(0)
        self._status_label.configure(text=self._app.i18n.t("progress_preparing"))

        self._app.footer.set_next_enabled(False)
        self._app.footer.set_back_enabled(False)

        self._total_steps = 0
        self._current_step = 0
        self._start_time = time.time()
        self._update_timer()

        self._patching_thread = threading.Thread(target=self._run_patching, daemon=True)
        self._patching_thread.start()

    def _update_timer(self):
        if not self._patching_complete and not self._patching_error:
            elapsed = int(time.time() - self._start_time)
            mins, secs = divmod(elapsed, 60)
            self._elapsed_time_label.configure(text=self._app.i18n.t("progress_time_format", mins=mins, secs=secs))
            self.after(1000, self._update_timer)

    def _run_patching(self):
        try:
            context = self._app.context
            selected_games = self._build_selected_games()
            self.patcher = Patcher(
                context,
                self._app.config,
                log_callback=None,
                component_callback=self._on_component_start_threadsafe,
                step_callback=self._on_step_start_threadsafe
            )
            self._total_steps = self.patcher.get_total_steps(selected_games)
            self.patcher.run(selected_games)
            self._patching_complete = True
            self._on_patching_complete_threadsafe()
        except Exception as e:
            self._patching_error = str(e)
            self._on_patching_error_threadsafe(self._patching_error)

    def _build_selected_games(self) -> list[Game]:
        context = self._app.context
        selected_components = context.selected_components
        game_map: dict[str, Game] = {}

        for game in context.games:
            selected_for_game = [c for c in game.components if c in selected_components]
            if selected_for_game:
                if game.engine_type == EngineType.GOLDSRC:
                    engine_comp = next((c for c in game.components if c.name == "GoldSrc Engine"), None)
                    if engine_comp and engine_comp.needs_patch and engine_comp not in selected_for_game:
                        selected_for_game.insert(0, engine_comp)

                game_map[game.name] = Game(
                    name=game.name,
                    path=game.path,
                    engine_type=game.engine_type,
                    components=selected_for_game,
                )

        return list(game_map.values())

    def _on_component_start_threadsafe(self, component_name: str):
        self.after(0, self._on_component_start, component_name)

    def _on_component_start(self, component_name: str):
        self._status_label.configure(text=self._app.i18n.t("progress_patching_comp", component=component_name))
        if self._total_steps > 0:
            self._progress_bar.set(self._current_step / self._total_steps)
        self._current_step += 1

    def _on_step_start_threadsafe(self, current: int, total: int):
        self.after(0, self._on_step_start, current, total)

    def _on_step_start(self, current: int, total: int):
        self._step_label.configure(text=self._app.i18n.t("progress_step_format", current=current, total=total))
        if total > 0:
            self._step_progress_bar.set(current / total)

    def _on_patching_complete_threadsafe(self):
        self.after(0, self._on_patching_complete)

    def _on_patching_complete(self):
        if self._patching_error:
            return
        self._progress_bar.set(1.0)
        self._step_progress_bar.set(1.0)
        self._status_label.configure(text=self._app.i18n.t("progress_complete"))
        self._step_label.configure(text=self._app.i18n.t("progress_done"))
        self._app.router.show_page(PageRoute.SUCCESS)

    def _on_patching_error_threadsafe(self, error: str):
        self.after(0, self._on_patching_error_sync, error)

    def _on_patching_error_sync(self, error: str):
        self._app.patching_error = error
        self._app.router.show_page(PageRoute.FAILURE)

    def stop_patching(self):
        if hasattr(self, 'patcher') and self.patcher:
            self.patcher.stop()

    def get_title(self) -> str:
        return self._app.i18n.t("progress_title")

    def show_back_button(self) -> bool:
        return False

    def show_next_button(self) -> bool:
        return False
