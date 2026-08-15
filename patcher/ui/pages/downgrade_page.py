import hashlib
import customtkinter as ctk
from patcher.ui import BasePage, PageRoute


class DowngradePage(BasePage):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, app, **kwargs)

        self._check_job = None
        self._cards = {}

    def on_enter(self):
        for widget in self.winfo_children():
            widget.destroy()

        self._cards.clear()

        self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_frame.pack(fill="both", expand=True)

        context = self._app.context

        components_to_downgrade = []
        for game in context.games:
            for component in game.components:
                if component in context.selected_components and component.requires:
                    components_to_downgrade.append((game, component))

        for game, component in components_to_downgrade:
            card_frame = ctk.CTkFrame(self._scroll_frame, fg_color="gray20", corner_radius=8)
            card_frame.pack(fill="x", padx=20, pady=5)

            card_title = ctk.CTkLabel(
                card_frame,
                text=component.name,
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
            )
            card_title.pack(fill="x", padx=15, pady=(10, 10))

            card_btn = ctk.CTkButton(
                card_frame,
                text=self._app.i18n.t("downgrade_guide_btn"),
                command=lambda g=game, c=component: self._open_downgrade_guide(g, c),
            )
            card_btn.pack(fill="x", padx=15, pady=(0, 10))

            card_key = f"{game.name}_{component.name}"
            self._cards[card_key] = {
                'frame': card_frame,
                'btn': card_btn,
                'game': game,
                'component': component,
                'orig_fg': card_btn.cget("fg_color"),
                'orig_hover': card_btn.cget("hover_color")
            }

        if hasattr(self._app, "footer") and self._app.footer:
            self._app.footer.set_next_enabled(False)

        self._check_job = self.after(100, self._check_downgrades)

    def on_leave(self):
        if self._check_job:
            self.after_cancel(self._check_job)
            self._check_job = None

    def _open_downgrade_guide(self, game, component):
        from patcher.ui import BaseGuideWindow

        config = self._app.guide_registry.get_guide(component.subfolder)
        if config:
            guide = BaseGuideWindow(self, self._app, title=config.title)
            for step in config.steps:
                guide.add_step(
                    title_key=step.step_title,
                    desc_key=step.step_description,
                    command=step.step_command,
                    button_url=step.step_button_url,
                    button_text_key=step.step_button_text
                )
        else:
            pass

    def _check_downgrades(self):
        all_match = True
        remaining_count = 0
        context = self._app.context

        for card_key, card_info in self._cards.items():
            game = card_info['game']
            component = card_info['component']
            comp_match = True

            if component in context.selected_components and component.requires:
                for filename, expected_hash in component.requires.items():
                    file_path = game.path / filename
                    if not file_path.is_file():
                        comp_match = False
                        break

                    if expected_hash == "":
                        continue

                    try:
                        with open(file_path, "rb") as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        if file_hash != expected_hash:
                            comp_match = False
                            break
                    except Exception:
                        comp_match = False
                        break

            if comp_match:
                card_info['btn'].configure(
                    text=self._app.i18n.t("downgraded_success_btn"),
                    fg_color="green",
                    hover_color="dark green",
                    state="disabled"
                )
            else:
                all_match = False
                remaining_count += 1
                card_info['btn'].configure(
                    text=self._app.i18n.t("downgrade_guide_btn"),
                    fg_color=card_info['orig_fg'],
                    hover_color=card_info['orig_hover'],
                    state="normal"
                )

        if hasattr(self, "_status_label") and self._status_label.winfo_exists():
            if remaining_count > 0:
                self._status_label.configure(
                    text=self._app.i18n.t("downgrade_status_remaining", count=remaining_count),
                    text_color="#e74c3c"
                )
            else:
                self._status_label.configure(
                    text=self._app.i18n.t("downgrade_status_all"),
                    text_color="#2ecc71"
                )

        if hasattr(self._app, "footer") and self._app.footer:
            self._app.footer.set_next_enabled(all_match)

        self._check_job = self.after(1000, self._check_downgrades)

    def get_title(self) -> str:
        return self._app.i18n.t("downgrade_title")

    def get_next_page_key(self) -> PageRoute:
        return PageRoute.PROGRESS

    def get_back_page_key(self) -> PageRoute:
        return PageRoute.OPTIONS

    def get_next_button_text(self) -> str:
        return self._app.i18n.t("btn_patch")

    def get_custom_footer_widget(self, parent: ctk.CTkFrame) -> ctk.CTkFrame | None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._status_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(weight="bold", size=11),
            justify="center"
        )
        self._status_label.pack(expand=True, fill="both")
        return frame
