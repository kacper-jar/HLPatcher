import customtkinter as ctk
import threading
from patcher.ui import BasePage
from patcher.core import Game, Patcher


class ProgressPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        self._status_label = ctk.CTkLabel(
            self,
            text="Preparing to patch...",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._status_label.pack(pady=(20, 10))

        self._progress_bar = ctk.CTkProgressBar(self, width=340)
        self._progress_bar.pack(pady=10, padx=20)
        self._progress_bar.set(0)

        self._patching_thread = None
        self._patching_complete = False
        self._patching_error = None

    def on_enter(self):
        self._patching_complete = False
        self._patching_error = None
        self._progress_bar.set(0)
        self._status_label.configure(text="Preparing to patch...")

        self._app.footer.set_next_enabled(False)
        self._app.footer.set_back_enabled(False)

        self._total_steps = 0
        self._current_step = 0

        self._patching_thread = threading.Thread(target=self._run_patching, daemon=True)
        self._patching_thread.start()

    def _run_patching(self):
        try:
            context = self._app.context
            selected_games = self._build_selected_games()
            self.patcher = Patcher(
                context,
                log_callback=None,
                component_callback=self._on_component_start_threadsafe
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
        self._status_label.configure(text=f"Patching: {component_name}")
        if self._total_steps > 0:
            self._progress_bar.set(self._current_step / self._total_steps)
        self._current_step += 1

    def _on_patching_complete_threadsafe(self):
        self.after(0, self._on_patching_complete)

    def _on_patching_complete(self):
        if self._patching_error:
            return
        self._progress_bar.set(1.0)
        self._status_label.configure(text="Patching complete!")
        self._app.show_page("success")

    def _on_patching_error_threadsafe(self, error: str):
        self.after(0, self._on_patching_error_sync, error)

    def _on_patching_error_sync(self, error: str):
        self._app.patching_error = error
        self._app.show_page("failure")

    def stop_patching(self):
        if hasattr(self, 'patcher') and self.patcher:
            self.patcher.stop()

    def get_title(self) -> str:
        return "Patching"

    def show_back_button(self) -> bool:
        return False

    def show_next_button(self) -> bool:
        return False
