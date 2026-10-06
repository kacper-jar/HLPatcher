import logging
import threading
import time
import tkinter
import customtkinter as ctk

import pytest

from patcher.app import App
from patcher.core import AppConfig, UpdateInfo
from patcher.ui import PageRoute

RELEASE_URL = "https://github.com/kacper-jar/HLPatcher/releases/tag/3.3.0"
HASH = "5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef"

HALF_LIFE = ["Half-Life/hl_osx", "Half-Life/valve/liblist.gam"]
PATCHED_HALF_LIFE = HALF_LIFE + ["Half-Life/libxash.dylib", "Half-Life/libmenu.dylib",
                                 "Half-Life/SDL2.framework/SDL2", "Half-Life/valve/dlls/hl_arm64.dylib"]
HALF_LIFE_2 = ["Half-Life 2/hl2_osx", "Half-Life 2/hl2/gameinfo.txt"]
PATCHED_HALF_LIFE_2 = HALF_LIFE_2 + ["Half-Life 2/hl2/bin/libclient.dylib", "Half-Life 2/hl2/bin/libserver.dylib"]
HL2DM = ["Half-Life 2 Deathmatch/hl2mp/gameinfo.txt"]


class FakePatcher:
    hold = False

    def __init__(self, context, config, component_callback=None, step_callback=None):
        self.context = context
        self.started = threading.Event()
        self.stopped = threading.Event()
        self.working_dir_when_stopped = None

    def get_total_steps(self, games):
        return 0

    def run(self, games):
        self.started.set()
        if self.hold:
            self.stopped.wait(5)
            time.sleep(0.2)
            self.working_dir_when_stopped = self.context.working_dir.exists()
            raise RuntimeError("Execution stopped by user")

    def stop(self):
        self.stopped.set()


def eventually(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return bool(condition())


def closed(app):
    try:
        app.winfo_exists()
    except tkinter.TclError:
        return True
    return False


def run_until(app, condition, timeout=5.0):
    deadline = time.monotonic() + timeout

    def check():
        if condition() or time.monotonic() > deadline:
            app.quit()
        else:
            app.after(10, check)

    if not closed(app):
        app.after(10, check)
        app.mainloop()
    return condition()


def install(library, *files):
    library.mkdir(parents=True, exist_ok=True)
    for file in files:
        (library / file).parent.mkdir(parents=True, exist_ok=True)
        (library / file).touch()


def open_library(app, library):
    app.router.show_page(PageRoute.LIBRARY)
    app.router.get_current_page()._path_var.set(str(library))
    app.router.go_next()


def button_texts(footer):
    return [widget.cget("text") for widget in footer.winfo_children() if isinstance(widget, ctk.CTkButton)]


@pytest.fixture(autouse=True)
def fake_patcher(mocker):
    return mocker.patch("patcher.ui.pages.progress_page.Patcher", FakePatcher)


@pytest.fixture
def update_check(mocker):
    return mocker.patch("patcher.app.Updater.check_for_update", return_value=None)


@pytest.fixture
def make_app(update_check, tmp_path):
    apps = []

    def factory(debug=False):
        app = App(AppConfig(debug=debug))
        app.context.working_dir = tmp_path / "working_dir"
        apps.append(app)
        return app

    yield factory
    for app in apps:
        try:
            app.update()
            app.destroy()
        except tkinter.TclError:
            pass


@pytest.fixture
def app(make_app):
    return make_app()


@pytest.fixture
def library(tmp_path):
    return tmp_path / "SteamLibrary"


def test_starts_on_the_welcome_page_with_the_shipped_data(app, pytestconfig):
    assert app.router.current_page_key == PageRoute.WELCOME
    assert app.title() == "HLPatcher"
    assert app.context.script_dir == pytestconfig.rootpath.resolve()
    assert app.guide_registry.get_guide("hl2") is not None
    assert {"en-US", "pl-PL"} <= set(app.i18n.available_langs)


@pytest.mark.parametrize(("info", "shown"), [
    (UpdateInfo("3.3.0", True, RELEASE_URL), PageRoute.UPDATE_AVAILABLE),
    (UpdateInfo("3.2.1", False, RELEASE_URL), PageRoute.LIBRARY),
    (None, PageRoute.LIBRARY),
], ids=["update-available", "up-to-date", "check-failed"])
def test_offers_an_available_update_before_the_library(make_app, update_check, mocker, info, shown):
    mocker.patch("patcher.__version__", "3.2.1")
    update_check.return_value = info
    app = make_app()
    assert eventually(lambda: update_check.called and app.update_info == info)

    app.router.go_next()

    assert update_check.call_args.args == ("3.2.1",)
    assert app.router.current_page_key == shown


@pytest.mark.parametrize(("files", "shown"), [
    ([], PageRoute.NO_GAMES),
    (PATCHED_HALF_LIFE, PageRoute.ALL_PATCHED),
    (HALF_LIFE + PATCHED_HALF_LIFE_2, PageRoute.SELECTION),
], ids=["no-games", "all-patched", "something-to-patch"])
def test_scans_the_chosen_library_and_shows_what_it_found(app, library, files, shown):
    install(library, *files)

    open_library(app, library)

    assert app.router.current_page_key == shown
    assert app.context.steam_library_path == library


def test_scanning_another_library_rebuilds_the_selection(app, tmp_path):
    first, second = tmp_path / "First", tmp_path / "Second"
    install(first, *HALF_LIFE)
    install(second, *HALF_LIFE_2)
    open_library(app, first)
    first_selection = app.router.get_current_page()

    app.router.go_back()
    open_library(app, second)

    assert app.router.current_page_key == PageRoute.SELECTION
    assert app.router.get_current_page() is not first_selection
    assert not first_selection.winfo_exists()
    assert [game.name for game in app.context.games] == ["Source (Half-Life 2)"]


@pytest.mark.parametrize(("files", "shown"), [
    (HL2DM, PageRoute.HL2_REQUIRED),
    (HALF_LIFE_2 + HL2DM, PageRoute.OPTIONS),
    (PATCHED_HALF_LIFE_2 + HL2DM, PageRoute.OPTIONS),
], ids=["half-life-2-missing", "half-life-2-selected-too", "half-life-2-patched"])
def test_asks_for_half_life_2_before_its_multiplayer_games(app, library, files, shown):
    install(library, *files)
    open_library(app, library)

    app.router.go_next()

    assert app.router.current_page_key == shown


@pytest.mark.parametrize(("requires", "shown"), [
    ({"hl2mp/bin/client.dylib": HASH}, PageRoute.DOWNGRADE),
    ({}, PageRoute.PROGRESS),
], ids=["needs-downgrade", "ready-to-patch"])
def test_checks_for_downgrades_before_patching(app, make_component, requires, shown):
    app.context.selected_components = [make_component("Half-Life 2: Deathmatch", "hl2mp",
                                                      downgrade_requires=requires)]
    app.router.show_page(PageRoute.LIMITATIONS)

    app.router.go_next()

    assert app.router.current_page_key == shown
    if shown == PageRoute.PROGRESS:
        assert run_until(app, lambda: app.router.current_page_key == PageRoute.SUCCESS)


def test_switching_language_retranslates_the_footer_and_rebuilds_the_page(app):
    welcome = app.router.get_current_page()

    app.i18n.set_language("pl-PL")

    assert app.router.get_current_page() is not welcome
    assert app.router.get_current_page().get_title().startswith("Witaj w HLPatcher")
    assert button_texts(app.footer) == ["Wyjdź", "Wstecz", "Dalej"]


@pytest.mark.parametrize("quit_app", [
    lambda app: app.tk.call(app.protocol("WM_DELETE_WINDOW")),
    lambda app: app.tk.call("::tk::mac::Quit"),
    lambda app: next(widget for widget in app.footer.winfo_children()
                     if isinstance(widget, ctk.CTkButton) and widget.cget("text") == app.i18n.t("btn_quit")).invoke(),
], ids=["window-close", "cmd-q", "quit-button"])
def test_quitting_removes_the_working_dir_and_closes(app, quit_app):
    (app.context.working_dir / "venv").mkdir(parents=True)

    quit_app(app)

    assert run_until(app, lambda: closed(app))
    assert not app.context.working_dir.exists()


def test_a_second_quit_request_is_ignored(app):
    app.tk.call("::tk::mac::Quit")

    app.tk.call("::tk::mac::Quit")

    assert closed(app)


def test_quitting_in_debug_mode_keeps_the_working_dir(make_app):
    app = make_app(debug=True)
    (app.context.working_dir / "venv").mkdir(parents=True)

    app.tk.call("::tk::mac::Quit")

    assert run_until(app, lambda: closed(app))
    assert app.context.working_dir.is_dir()


def test_quitting_while_patching_waits_for_the_patcher_to_stop(app, mocker):
    mocker.patch.object(FakePatcher, "hold", True)
    (app.context.working_dir / "venv").mkdir(parents=True)
    app.router.show_page(PageRoute.PROGRESS)
    page = app.router.get_current_page()
    assert eventually(page.patcher.started.is_set)

    app.tk.call("::tk::mac::Quit")

    assert run_until(app, lambda: closed(app))
    assert page.patcher.stopped.is_set()
    assert page.patcher.working_dir_when_stopped is True
    assert not page.is_patching()
    assert not app.context.working_dir.exists()


def test_an_error_in_the_interface_goes_to_the_log(app, caplog):
    def broken_button():
        raise ValueError("the page lost its game list")

    app.after(0, broken_button)
    with caplog.at_level(logging.ERROR):
        run_until(app, lambda: caplog.records)

    record, = caplog.records
    assert record.getMessage() == "Unhandled error in the interface"
    assert record.exc_info[1].args == ("the page lost its game list",)
