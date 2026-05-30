from __future__ import annotations

import re
from typing import Callable

from patcher.ui import BasePage, PageRoute


def _camel_to_snake(name: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class Router:
    def __init__(self, app, content_frame, header, footer):
        self.app = app
        self.content_frame = content_frame
        self.header = header
        self.footer = footer

        self._pages: dict[PageRoute, type] = {}
        self._page_instances: dict[PageRoute, BasePage] = {}
        self.current_page_key: PageRoute | None = None
        self._history: list[PageRoute] = []

        self.route_interceptor: Callable[[PageRoute, PageRoute], PageRoute | None] | None = None

        self._register_pages()

    def _register_pages(self):
        for cls in BasePage.__subclasses__():
            if cls.__name__ == "BasePage":
                continue
            key_str = _camel_to_snake(cls.__name__.replace('Page', ''))
            try:
                key = PageRoute(key_str)
                self._pages[key] = cls
            except ValueError:
                pass

    def show_page(self, page_key: PageRoute):
        if self.current_page_key and self.current_page_key in self._page_instances:
            current = self._page_instances[self.current_page_key]
            current.on_leave()
            current.pack_forget()

        if page_key not in self._page_instances:
            if page_key not in self._pages:
                raise ValueError(f"Page '{page_key}' not registered.")
            page_class = self._pages[page_key]
            self._page_instances[page_key] = page_class(self.content_frame, self.app)

        page = self._page_instances[page_key]
        page.pack(fill="both", expand=True)
        page.on_enter()

        self.header.set_title(page.get_title())
        self.footer.set_back_visible(page.show_back_button())
        self.footer.set_next_visible(page.show_next_button())
        self.footer.set_next_text(page.get_next_button_text())
        self.footer.set_next_enabled(True)
        self.footer.set_back_enabled(True)

        self.current_page_key = page_key

    def invalidate_page(self, page_key: PageRoute):
        if page_key in self._page_instances:
            self._page_instances[page_key].destroy()
            del self._page_instances[page_key]

    def go_back(self):
        if not self.current_page_key:
            return

        page = self._page_instances.get(self.current_page_key)
        if not page or not page.can_go_back():
            return

        back_key = page.get_back_page_key()
        if back_key:
            if self._history:
                self._history.pop()
            self.show_page(back_key)

    def go_next(self):
        if not self.current_page_key:
            return

        page = self._page_instances.get(self.current_page_key)
        if not page or not page.can_go_next():
            return

        page.on_leave()
        next_key = page.get_next_page_key()

        if self.route_interceptor and next_key:
            override_key = self.route_interceptor(self.current_page_key, next_key)
            if override_key == PageRoute.HALT:
                return
            if override_key:
                next_key = override_key

        if next_key:
            self._history.append(self.current_page_key)
            self.show_page(next_key)

    def get_current_page(self) -> BasePage | None:
        return self._page_instances.get(self.current_page_key)

    def get_page_instance(self, page_key: PageRoute) -> BasePage | None:
        return self._page_instances.get(page_key)

    def push_history(self, page_key: PageRoute):
        self._history.append(page_key)
