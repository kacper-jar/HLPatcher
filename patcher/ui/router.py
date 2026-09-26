from collections.abc import Callable

from patcher.ui.base_page import BasePage
from patcher.ui.page_route import PageRoute
from patcher.ui.pages import (
    AllPatchedPage,
    DowngradePage,
    FailurePage,
    Hl2RequiredPage,
    LibraryPage,
    LimitationsPage,
    NoGamesPage,
    OptionsPage,
    ProgressPage,
    SelectionPage,
    SuccessPage,
    UpdateAvailablePage,
    WelcomePage,
)

PAGES: dict[PageRoute, type[BasePage]] = {
    PageRoute.WELCOME: WelcomePage,
    PageRoute.LIBRARY: LibraryPage,
    PageRoute.SELECTION: SelectionPage,
    PageRoute.OPTIONS: OptionsPage,
    PageRoute.LIMITATIONS: LimitationsPage,
    PageRoute.DOWNGRADE: DowngradePage,
    PageRoute.PROGRESS: ProgressPage,
    PageRoute.SUCCESS: SuccessPage,
    PageRoute.FAILURE: FailurePage,
    PageRoute.NO_GAMES: NoGamesPage,
    PageRoute.ALL_PATCHED: AllPatchedPage,
    PageRoute.UPDATE_AVAILABLE: UpdateAvailablePage,
    PageRoute.HL2_REQUIRED: Hl2RequiredPage,
}


class Router:
    def __init__(self, app, content_frame, header, footer):
        self.app = app
        self.content_frame = content_frame
        self.header = header
        self.footer = footer

        self._page_instances: dict[PageRoute, BasePage] = {}
        self._left_page: BasePage | None = None
        self.current_page_key: PageRoute | None = None

        self.route_interceptor: Callable[[PageRoute, PageRoute], PageRoute | None] | None = None

    def show_page(self, page_key: PageRoute):
        current = self.get_current_page()
        if current:
            if current is not self._left_page:
                current.on_leave()
            current.pack_forget()
        self._left_page = None

        if page_key not in self._page_instances:
            if page_key not in PAGES:
                raise ValueError(f"Page '{page_key}' not registered.")
            self._page_instances[page_key] = PAGES[page_key](self.content_frame, self.app)

        page = self._page_instances[page_key]
        self.header.set_title(page.get_title())
        self.footer.set_back_visible(page.show_back_button())
        self.footer.set_next_visible(page.show_next_button())
        self.footer.set_next_text(page.get_next_button_text())
        self.footer.set_next_enabled(True)
        self.footer.set_back_enabled(True)

        custom_footer = page.get_custom_footer_widget(self.footer.custom_container)
        self.footer.set_custom_content(custom_footer)

        page.pack(fill="both", expand=True)
        page.on_enter()

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
            self.show_page(back_key)

    def go_next(self):
        if not self.current_page_key:
            return

        page = self._page_instances.get(self.current_page_key)
        if not page or not page.can_go_next():
            return

        page.on_leave()
        self._left_page = page
        next_key = page.get_next_page_key()

        if self.route_interceptor and next_key:
            override_key = self.route_interceptor(self.current_page_key, next_key)
            if override_key == PageRoute.HALT:
                return
            if override_key:
                next_key = override_key

        if next_key:
            self.show_page(next_key)

    def get_current_page(self) -> BasePage | None:
        return self._page_instances.get(self.current_page_key)

    def get_page_instance(self, page_key: PageRoute) -> BasePage | None:
        return self._page_instances.get(page_key)
