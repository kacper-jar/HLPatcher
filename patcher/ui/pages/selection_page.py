import customtkinter as ctk
from patcher.ui import BasePage


class SelectionPage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        hint_label = ctk.CTkLabel(
            self,
            text="Check the games you want to patch.\nAlready patched games are shown but disabled.",
            justify="center",
            font=ctk.CTkFont(size=12),
        )
        hint_label.pack(pady=(0, 10))

        self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color="gray20", corner_radius=8)
        self._scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self._checkbox_vars: dict[str, ctk.BooleanVar] = {}
        self._parent_children: dict[str, list[str]] = {}

    def on_enter(self):
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._checkboxes.clear()
        self._checkbox_vars.clear()
        self._parent_children.clear()

        games = self._app.context.games
        for game in games:
            self._create_game_group(game)

    def _create_game_group(self, game):
        parent_key = f"parent_{game.name}"
        parent_var = ctk.BooleanVar(value=False)
        self._checkbox_vars[parent_key] = parent_var

        parent_frame = ctk.CTkFrame(self._scroll_frame, fg_color="gray25", corner_radius=6)
        parent_frame.pack(fill="x", padx=5, pady=(10, 2))

        child_keys = []

        parent_checkbox = ctk.CTkCheckBox(
            parent_frame,
            text=game.name,
            variable=parent_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda gn=game.name: self._on_parent_toggle(gn),
        )
        parent_checkbox.pack(fill="x", padx=10, pady=8)
        self._checkboxes[parent_key] = parent_checkbox

        has_unpatchable = True
        for component in game.components:
            child_key = f"child_{game.name}_{component.name}"
            child_var = ctk.BooleanVar(value=False)
            self._checkbox_vars[child_key] = child_var
            child_keys.append(child_key)

            is_disabled = not component.needs_patch
            status_text = " (already patched)" if is_disabled else ""

            child_checkbox = ctk.CTkCheckBox(
                self._scroll_frame,
                text=f"  {component.name}{status_text}",
                variable=child_var,
                font=ctk.CTkFont(size=12),
                command=lambda gn=game.name: self._on_child_toggle(gn),
            )

            if is_disabled:
                child_checkbox.configure(state="disabled")
                child_var.set(False)
            else:
                has_unpatchable = False

            child_checkbox.pack(fill="x", padx=25, pady=2)
            self._checkboxes[child_key] = child_checkbox

        self._parent_children[game.name] = child_keys

        if has_unpatchable:
            parent_checkbox.configure(state="disabled")

    def _on_parent_toggle(self, game_name: str):
        parent_key = f"parent_{game_name}"
        parent_checked = self._checkbox_vars[parent_key].get()

        for child_key in self._parent_children.get(game_name, []):
            checkbox = self._checkboxes[child_key]
            if str(checkbox.cget("state")) != "disabled":
                self._checkbox_vars[child_key].set(parent_checked)

    def _on_child_toggle(self, game_name: str):
        parent_key = f"parent_{game_name}"
        child_keys = self._parent_children.get(game_name, [])

        all_checked = all(
            self._checkbox_vars[ck].get()
            for ck in child_keys
            if str(self._checkboxes[ck].cget("state")) != "disabled"
        )
        self._checkbox_vars[parent_key].set(all_checked)

    def can_go_next(self) -> bool:
        return any(v.get() for k, v in self._checkbox_vars.items() if k.startswith("child_"))

    def on_leave(self):
        selected = []
        for game in self._app.context.games:
            for component in game.components:
                child_key = f"child_{game.name}_{component.name}"
                if child_key in self._checkbox_vars and self._checkbox_vars[child_key].get():
                    selected.append(component)
        self._app.context.selected_components = selected

    def get_title(self) -> str:
        return "Select Games to Patch"

    def get_next_page_key(self) -> str:
        return "options"

    def get_back_page_key(self) -> str:
        return "library"
