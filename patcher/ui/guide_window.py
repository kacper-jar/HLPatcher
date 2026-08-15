import webbrowser
import customtkinter as ctk


class BaseGuideWindow(ctk.CTkToplevel):
    def __init__(self, parent, app, title: str = "", width: int = 600, height: int = 620, **kwargs):
        super().__init__(parent, **kwargs)
        self._app = app

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.resizable(False, False)

        self.transient(parent)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=20, pady=15)

        self.content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.footer_frame = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.footer_frame.pack(fill="x")
        self.footer_frame.pack_propagate(False)

        self.footer_frame.columnconfigure(0, weight=1)

        self.close_button = ctk.CTkButton(
            self.footer_frame,
            text="Close",
            width=80,
            command=self.destroy,
        )
        self.close_button.grid(row=0, column=0, padx=10, pady=10)

    def set_title(self, title: str):
        self.title(title)
        self.title_label.configure(text=title)

    def add_step(self, title_key: str, desc_key: str, command: str = "", button_url: str = "",
                 button_text_key: str = ""):
        card = ctk.CTkFrame(self.content_frame, fg_color="gray20", corner_radius=8)
        card.pack(fill="x", padx=20, pady=5)

        title_label = ctk.CTkLabel(
            card,
            text=self._app.i18n.t(title_key),
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(10, 5))

        desc_label = ctk.CTkLabel(
            card,
            text=self._app.i18n.t(desc_key),
            wraplength=500,
            justify="left",
            anchor="w"
        )
        desc_label.pack(fill="x", padx=15, pady=(0, 10))

        if command:
            cmd_container = ctk.CTkFrame(card, fg_color="black", corner_radius=6)
            cmd_container.pack(fill="x", padx=15, pady=(0, 10))

            cmd_box = ctk.CTkTextbox(
                cmd_container,
                font=ctk.CTkFont(family="Courier", size=12),
                fg_color="transparent",
                text_color="gray90",
                height=60,
                wrap="word"
            )
            cmd_box.insert("0.0", command)
            cmd_box.configure(state="disabled")
            cmd_box.pack(side="left", fill="x", expand=True, padx=5, pady=5)

            def copy_to_clipboard(text=command):
                self.clipboard_clear()
                self.clipboard_append(text)

            copy_btn = ctk.CTkButton(
                cmd_container,
                text="Copy",
                width=50,
                height=24,
                command=copy_to_clipboard
            )
            copy_btn.pack(side="right", padx=10, pady=10, anchor="ne")

        if button_url:
            btn_text = self._app.i18n.t(button_text_key) if button_text_key else self._app.i18n.t("btn_open_link")
            btn = ctk.CTkButton(
                card,
                text=btn_text,
                command=lambda url=button_url: webbrowser.open(url)
            )
            btn.pack(fill="x", padx=15, pady=(0, 10))
