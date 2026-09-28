from types import SimpleNamespace

import customtkinter as ctk
import pytest

from patcher.ui import BasePage, PageRoute, Router
from patcher.ui.router import PAGES

WELCOME, LIBRARY, SELECTION, OPTIONS, HL2_REQUIRED = (
    PageRoute.WELCOME, PageRoute.LIBRARY, PageRoute.SELECTION, PageRoute.OPTIONS, PageRoute.HL2_REQUIRED,
)


class FakePage(BasePage):
    route = None
    next_key = None
    back_key = None
    back_button = True
    next_button = True
    footer_widget = False

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.ready = True
        self.back_allowed = True
        app.events.append(("create", self.route))

    def get_title(self):
        return self.route.value

    def on_enter(self):
        self._app.events.append(("enter", self.route))

    def on_leave(self):
        self._app.events.append(("leave", self.route))

    def can_go_next(self):
        return self.ready

    def can_go_back(self):
        return self.back_allowed

    def get_next_page_key(self):
        return self.next_key

    def get_back_page_key(self):
        return self.back_key

    def show_back_button(self):
        return self.back_button

    def show_next_button(self):
        return self.next_button

    def get_custom_footer_widget(self, parent):
        return ctk.CTkFrame(parent) if self.footer_widget else None


def page_class(route, **attributes):
    return type(f"Fake{route.name.title()}Page", (FakePage,), {"route": route, **attributes})


class FakeHeader:
    title = None

    def set_title(self, title):
        self.title = title


class FakeFooter:
    def __init__(self, parent):
        self.custom_container = ctk.CTkFrame(parent)
        self.custom = None
        self.buttons = {}

    def set_back_visible(self, visible):
        self.buttons["back_visible"] = visible

    def set_next_visible(self, visible):
        self.buttons["next_visible"] = visible

    def set_next_text(self, text):
        self.buttons["next_text"] = text

    def set_back_enabled(self, enabled):
        self.buttons["back_enabled"] = enabled

    def set_next_enabled(self, enabled):
        self.buttons["next_enabled"] = enabled

    def set_custom_content(self, widget):
        self.custom = widget


@pytest.fixture
def app():
    return SimpleNamespace(events=[], i18n=SimpleNamespace(t=lambda key: key))


@pytest.fixture
def header():
    return FakeHeader()


@pytest.fixture
def footer(tk_root):
    return FakeFooter(tk_root)


@pytest.fixture
def router(tk_root, app, header, footer, mocker):
    mocker.patch.dict("patcher.ui.router.PAGES", {
        WELCOME: page_class(WELCOME, next_key=LIBRARY, back_button=False, footer_widget=True),
        LIBRARY: page_class(LIBRARY, next_key=SELECTION, back_key=WELCOME),
        SELECTION: page_class(SELECTION, next_key=OPTIONS, back_key=LIBRARY),
        OPTIONS: page_class(OPTIONS, back_key=SELECTION),
        HL2_REQUIRED: page_class(HL2_REQUIRED, back_key=SELECTION, next_button=False),
    }, clear=True)
    return Router(app, ctk.CTkFrame(tk_root), header, footer)


def test_every_screen_route_has_a_page():
    assert set(PAGES) == set(PageRoute) - {PageRoute.SCAN_AND_ROUTE, PageRoute.CHECK_DOWNGRADE, PageRoute.HALT}


@pytest.mark.parametrize(("route", "back_visible", "next_visible", "has_widget"), [
    (WELCOME, False, True, True),
    (LIBRARY, True, True, False),
    (HL2_REQUIRED, True, False, False),
], ids=["welcome", "library", "hl2-required"])
def test_shows_a_page_with_its_title_buttons_and_footer_widget(router, header, footer, route, back_visible,
                                                               next_visible, has_widget):
    router.show_page(route)

    page = router.get_current_page()
    assert (router.current_page_key, page.route, page.winfo_manager()) == (route, route, "pack")
    assert header.title == route.value
    assert footer.buttons == {"back_visible": back_visible, "next_visible": next_visible, "next_text": "btn_next",
                              "back_enabled": True, "next_enabled": True}
    assert (footer.custom is not None and footer.custom.master is footer.custom_container) is has_widget


def test_leaves_and_hides_the_previous_page(router, app):
    router.show_page(WELCOME)
    welcome = router.get_current_page()

    router.show_page(LIBRARY)

    assert app.events == [("create", WELCOME), ("enter", WELCOME), ("leave", WELCOME), ("create", LIBRARY),
                          ("enter", LIBRARY)]
    assert welcome.winfo_manager() == ""


def test_builds_each_page_once_and_reuses_it(router, app):
    router.show_page(WELCOME)
    welcome = router.get_current_page()
    router.show_page(LIBRARY)

    router.show_page(WELCOME)

    assert router.get_current_page() is welcome
    assert [event for event in app.events if event[0] == "create"] == [("create", WELCOME), ("create", LIBRARY)]


def test_next_leaves_the_page_once_and_shows_the_next_one(router, app):
    router.show_page(WELCOME)

    router.go_next()

    assert router.current_page_key == LIBRARY
    assert app.events == [("create", WELCOME), ("enter", WELCOME), ("leave", WELCOME), ("create", LIBRARY),
                          ("enter", LIBRARY)]


def test_next_waits_until_the_page_is_ready(router, app):
    router.show_page(WELCOME)
    router.get_current_page().ready = False

    router.go_next()

    assert router.current_page_key == WELCOME
    assert ("leave", WELCOME) not in app.events


def test_back_goes_to_the_back_route(router):
    router.show_page(LIBRARY)

    router.go_back()

    assert router.current_page_key == WELCOME


@pytest.mark.parametrize(("route", "allowed"), [(LIBRARY, False), (WELCOME, True)],
                         ids=["not-allowed", "no-back-route"])
def test_back_stays_put_when_it_has_nowhere_to_go(router, route, allowed):
    router.show_page(route)
    router.get_current_page().back_allowed = allowed

    router.go_back()

    assert router.current_page_key == route


@pytest.mark.parametrize(("decide", "shown"), [
    (lambda router: None, OPTIONS),
    (lambda router: HL2_REQUIRED, HL2_REQUIRED),
    (lambda router: router.show_page(HL2_REQUIRED) or PageRoute.HALT, HL2_REQUIRED),
], ids=["let-through", "redirect", "take-over"])
def test_the_interceptor_decides_where_next_leads_after_the_page_is_left(router, app, decide, shown):
    asked = []

    def interceptor(current, next_key):
        asked.append((current, next_key, app.events[-1]))
        return decide(router)

    router.route_interceptor = interceptor
    router.show_page(SELECTION)

    router.go_next()

    assert asked == [(SELECTION, OPTIONS, ("leave", SELECTION))]
    assert router.current_page_key == shown
    assert app.events.count(("leave", SELECTION)) == 1


def test_showing_a_page_turns_the_footer_buttons_back_on(router, footer):
    router.show_page(SELECTION)
    footer.set_next_enabled(False)
    footer.set_back_enabled(False)

    router.show_page(OPTIONS)

    assert (footer.buttons["back_enabled"], footer.buttons["next_enabled"]) == (True, True)


def test_rebuilds_an_invalidated_page(router, app):
    router.show_page(WELCOME)
    old = router.get_current_page()
    router.invalidate_page(OPTIONS)

    router.invalidate_page(WELCOME)
    router.show_page(WELCOME)

    assert not old.winfo_exists()
    assert router.get_current_page() is not old
    assert [event for event in app.events if event[0] == "create"] == [("create", WELCOME), ("create", WELCOME)]


def test_refuses_routes_without_a_page(router):
    with pytest.raises(ValueError, match="not registered"):
        router.show_page(PageRoute.SCAN_AND_ROUTE)


def test_navigation_does_nothing_before_the_first_page(router, app):
    router.go_next()
    router.go_back()

    assert (router.current_page_key, app.events) == (None, [])
