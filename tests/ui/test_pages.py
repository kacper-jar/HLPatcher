import hashlib
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import customtkinter as ctk
import pytest

from patcher.core import (AppConfig, EngineType, Game, GuideConfig, GuideStepConfig, PatchContext, PatchMode,
                          PatchStatus, Planner, UpdateInfo)
from patcher.ui import BaseGuideWindow, PageRoute
from patcher.ui.pages import (AllPatchedPage, DowngradePage, FailurePage, Hl2RequiredPage, LibraryPage,
                              LimitationsPage, NoGamesPage, OptionsPage, ProgressPage, SelectionPage, SuccessPage,
                              UpdateAvailablePage, WelcomePage)

RELEASE_URL = "https://github.com/kacper-jar/HLPatcher/releases/tag/3.3.0"
PATCHED = PatchStatus.ALREADY_PATCHED
SOURCE = EngineType.SOURCE
GOLDSRC = EngineType.GOLDSRC


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def translate(key, **kwargs):
    return " ".join([key, *(f"{name}={value}" for name, value in kwargs.items())])


class FakeFooter:
    next_enabled = None
    back_enabled = None

    def set_next_enabled(self, enabled):
        self.next_enabled = enabled

    def set_back_enabled(self, enabled):
        self.back_enabled = enabled


class FakeRouter:
    def __init__(self):
        self.shown = []

    def show_page(self, route):
        self.shown.append(route)


class ScriptedPatcher:
    def __init__(self, context, config, component_callback=None, step_callback=None):
        self.component_callback = component_callback
        self.step_callback = step_callback
        self.release = threading.Event()
        self.error = None
        self.stopped = False
        self.games = None
        self.timeline = ["Half-Life 2, step 1 of 2"]
        self.executor = object()

    def get_total_steps(self, games):
        return sum(comp.needs_patch for game in games for comp in game.components)

    def run(self, games):
        self.games = games
        for comp in [comp for game in games for comp in game.components if comp.needs_patch]:
            self.component_callback(comp.name)
            self.step_callback(1, 2)
        self.release.wait(5)
        if self.stopped:
            raise RuntimeError("Execution stopped by user")
        if self.error:
            raise self.error

    def stop(self):
        self.stopped = True
        self.release.set()


def widgets(parent, kind):
    found = []
    for child in parent.winfo_children():
        if isinstance(child, kind):
            found.append(child)
        found += widgets(child, kind)
    return found


def texts(parent):
    return [text for label in widgets(parent, ctk.CTkLabel) if (text := label.cget("text"))]


def find(parent, kind, text):
    return next(widget for widget in widgets(parent, kind) if widget.cget("text") == text)


def run_until(root, condition, timeout=5.0):
    deadline = time.monotonic() + timeout

    def check():
        try:
            done = condition() or time.monotonic() > deadline
        except Exception:
            root.quit()
            raise
        if done:
            root.quit()
        else:
            root.after(20, check)

    root.after(20, check)
    root.mainloop()
    return condition()


def eventually(condition, timeout=5.0):
    deadline = time.monotonic() + timeout
    while not condition() and time.monotonic() < deadline:
        time.sleep(0.01)
    return condition()


@pytest.fixture
def guides():
    return {}


@pytest.fixture
def app(tmp_path, guides):
    return SimpleNamespace(i18n=SimpleNamespace(t=translate), config=AppConfig(),
                           context=PatchContext(working_dir=tmp_path / "work"), update_info=None, patching_error="",
                           failure_report=None, footer=FakeFooter(), router=FakeRouter(),
                           guide_registry=SimpleNamespace(get_guide=guides.get))


@pytest.fixture
def make_page(tk_root, app):
    return lambda page_class: page_class(ctk.CTkFrame(tk_root), app)


NAVIGATION = [
    (WelcomePage, False, True, PageRoute.LIBRARY, None),
    (UpdateAvailablePage, True, True, PageRoute.LIBRARY, PageRoute.WELCOME),
    (LibraryPage, True, True, PageRoute.SCAN_AND_ROUTE, PageRoute.WELCOME),
    (NoGamesPage, True, False, None, PageRoute.LIBRARY),
    (AllPatchedPage, True, False, None, PageRoute.LIBRARY),
    (SelectionPage, True, True, PageRoute.OPTIONS, PageRoute.LIBRARY),
    (Hl2RequiredPage, True, False, None, PageRoute.SELECTION),
    (OptionsPage, True, True, PageRoute.LIMITATIONS, PageRoute.SELECTION),
    (LimitationsPage, True, True, PageRoute.CHECK_DOWNGRADE, PageRoute.OPTIONS),
    (DowngradePage, True, True, PageRoute.PROGRESS, PageRoute.LIMITATIONS),
    (ProgressPage, False, False, None, None),
    (SuccessPage, False, False, None, None),
    (FailurePage, False, False, None, None),
]


@pytest.mark.parametrize(("page_class", "back", "forward", "next_key", "back_key"), NAVIGATION,
                         ids=[row[0].__name__ for row in NAVIGATION])
def test_each_page_has_its_place_in_the_flow(make_page, page_class, back, forward, next_key, back_key):
    page = make_page(page_class)

    assert (page.show_back_button(), page.show_next_button(), page.get_next_page_key(),
            page.get_back_page_key()) == (back, forward, next_key, back_key)


@pytest.mark.parametrize(("info", "version_texts", "url"), [
    (UpdateInfo("3.3.0", True, RELEASE_URL), ["update_latest_version version=3.3.0"], RELEASE_URL),
    (None, [], "https://github.com/kacper-jar/HLPatcher/releases"),
], ids=["with-release", "without-release"])
def test_update_page_shows_the_new_version_and_opens_its_release(make_page, app, mocker, info, version_texts, url):
    app.update_info = info
    opened = mocker.patch("webbrowser.open")
    page = make_page(UpdateAvailablePage)

    find(page, ctk.CTkButton, "update_btn").invoke()

    assert [text for text in texts(page) if text.startswith("update_latest_version")] == version_texts
    opened.assert_called_once_with(url)


def path_entry(page):
    [entry] = widgets(page, ctk.CTkEntry)
    return entry


def type_path(page, path):
    path_entry(page).delete(0, "end")
    path_entry(page).insert(0, str(path))


@pytest.fixture
def library_page(make_page, mocker, tmp_path):
    mocker.patch("patcher.ui.pages.library_page.DEFAULT_STEAM_PATH", tmp_path / "no-steam")
    page = make_page(LibraryPage)
    page.on_enter()
    return page


@pytest.mark.parametrize("installed", [True, False], ids=["steam-installed", "no-steam"])
def test_library_suggests_the_default_steam_folder(make_page, mocker, tmp_path, installed):
    steam = tmp_path / "Steam" / "steamapps" / "common"
    if installed:
        steam.mkdir(parents=True)
    mocker.patch("patcher.ui.pages.library_page.DEFAULT_STEAM_PATH", steam)
    page = make_page(LibraryPage)

    page.on_enter()

    assert path_entry(page).get() == (str(steam) if installed else "")


def test_library_keeps_a_typed_folder_when_shown_again(library_page, tmp_path):
    type_path(library_page, tmp_path)

    library_page.on_enter()

    assert path_entry(library_page).get() == str(tmp_path)


def test_library_refuses_a_folder_that_does_not_exist(library_page, tmp_path):
    type_path(library_page, tmp_path / "SteamLibrary")
    assert library_page.can_go_next() is False
    assert "library_error_invalid" in texts(library_page)

    type_path(library_page, tmp_path)

    assert library_page.can_go_next() is True
    assert "library_error_invalid" not in texts(library_page)


@pytest.mark.parametrize(("typed", "chosen", "start", "result"), [
    ("{tmp}", "{tmp}/SteamLibrary", "{tmp}", "{tmp}/SteamLibrary"),
    ("{tmp}/missing", "{tmp}/SteamLibrary", "{home}", "{tmp}/SteamLibrary"),
    ("{tmp}", "", "{tmp}", "{tmp}"),
], ids=["from-typed-folder", "from-home", "cancelled"])
def test_library_browse_fills_in_the_chosen_folder(library_page, mocker, tmp_path, typed, chosen, start, result):
    fill = lambda text: text.format(tmp=tmp_path, home=Path.home())
    ask = mocker.patch("patcher.ui.pages.library_page.filedialog.askdirectory", return_value=fill(chosen))
    type_path(library_page, fill(typed))

    find(library_page, ctk.CTkButton, "...").invoke()

    assert ask.call_args.kwargs["initialdir"] == fill(start)
    assert path_entry(library_page).get() == fill(result)


@pytest.fixture
def library_games(app, make_component, tmp_path):
    app.context.games = [
        Game("GoldSrc (Half-Life)", tmp_path / "Half-Life", GOLDSRC, [
            make_component("GoldSrc Engine", "", GOLDSRC, auto_select=True, estimated_patch_time=1,
                           estimated_free_space_required=350),
            make_component("Half-Life", "valve", GOLDSRC, depends_on=["goldsrc-engine"], estimated_patch_time=1,
                           estimated_free_space_required=60),
            make_component("Half-Life: Opposing Force", "gearbox", GOLDSRC, PATCHED, id="opposing-force"),
        ]),
        Game("Source (Half-Life 2)", tmp_path / "Half-Life 2", SOURCE, [
            make_component("Half-Life 2", "hl2", SOURCE, estimated_patch_time=3, estimated_free_space_required=25),
        ]),
        Game("Source (Portal)", tmp_path / "Portal", SOURCE, [make_component("Portal", "portal", SOURCE, PATCHED)]),
    ]
    return {comp.id: comp for game in app.context.games for comp in game.components}


@pytest.fixture
def selection_page(make_page, library_games):
    page = make_page(SelectionPage)
    page.on_enter()
    return page


def checkbox(page, text):
    return find(page, ctk.CTkCheckBox, text)


def test_selection_offers_every_component_that_needs_patching(selection_page):
    selection_page.on_enter()

    assert [(box.cget("text"), box.get(), box.cget("state")) for box in widgets(selection_page, ctk.CTkCheckBox)] == [
        ("GoldSrc (Half-Life)", 1, "normal"),
        ("  Half-Life", 1, "normal"),
        ("  Half-Life: Opposing Forceselection_already_patched", 0, "disabled"),
        ("Source (Half-Life 2)", 1, "normal"),
        ("  Half-Life 2", 1, "normal"),
        ("Source (Portal)", 0, "disabled"),
        ("  Portalselection_already_patched", 0, "disabled"),
    ]


def estimate_texts(app, *components):
    minutes, megabytes = Planner(app.context.games).estimate(list(components))
    return ["selection_hint", f"selection_time_est mins={minutes}", f"selection_space_est mb={megabytes}"]


def test_selection_shows_the_estimate_of_the_checked_components(selection_page, app, library_games):
    half_life, half_life_2 = library_games["half-life"], library_games["half-life-2"]
    before = texts(selection_page)

    checkbox(selection_page, "Source (Half-Life 2)").toggle()

    assert before == estimate_texts(app, half_life, half_life_2)
    assert texts(selection_page) == estimate_texts(app, half_life)


def test_selection_game_checkbox_follows_its_components(selection_page):
    game, half_life = checkbox(selection_page, "GoldSrc (Half-Life)"), checkbox(selection_page, "  Half-Life")
    opposing_force = checkbox(selection_page, "  Half-Life: Opposing Forceselection_already_patched")

    game.toggle()
    assert (game.get(), half_life.get(), opposing_force.get()) == (0, 0, 0)

    game.toggle()
    assert (game.get(), half_life.get(), opposing_force.get()) == (1, 1, 0)

    half_life.toggle()
    assert (game.get(), half_life.get(), opposing_force.get()) == (0, 0, 0)

    half_life.toggle()
    assert (game.get(), half_life.get(), opposing_force.get()) == (1, 1, 0)


def test_selection_saves_the_checked_components_and_needs_at_least_one(selection_page, app, library_games):
    checkbox(selection_page, "Source (Half-Life 2)").toggle()
    selection_page.on_leave()
    assert app.context.selected_components == [library_games["half-life"]]
    assert selection_page.can_go_next() is True

    checkbox(selection_page, "GoldSrc (Half-Life)").toggle()

    assert selection_page.can_go_next() is False


def choose_stable_without_backup(page):
    find(page, ctk.CTkRadioButton, "options_mode_stable").invoke()
    find(page, ctk.CTkCheckBox, "options_backup_check").toggle()


@pytest.mark.parametrize(("choose", "expected"), [
    (lambda page: None, (PatchMode.LATEST, True)),
    (choose_stable_without_backup, (PatchMode.STABLE, False)),
], ids=["defaults", "stable-without-backup"])
def test_options_save_the_patch_mode_and_backup_choice(make_page, app, choose, expected):
    page = make_page(OptionsPage)
    choose(page)

    page.on_leave()

    assert (app.context.patch_mode, app.context.create_backup) == expected


@pytest.mark.parametrize(("requires", "next_text"), [
    ({"hl2mp/bin/client.dylib": sha256(b"client")}, "btn_next"),
    ({}, "btn_patch"),
], ids=["downgrade-next", "patch-next"])
def test_limitations_next_button_says_patch_when_no_downgrade_comes_next(make_page, app, make_component, requires,
                                                                         next_text):
    app.context.selected_components = [make_component("Half-Life 2: Deathmatch", "hl2mp", downgrade_requires=requires)]

    assert make_page(LimitationsPage).get_next_button_text() == next_text


@pytest.fixture
def downgrade_files(app, make_component, tmp_path):
    half_life_2 = Game("Source (Half-Life 2)", tmp_path / "Half-Life 2", SOURCE, [
        make_component("Half-Life 2", "hl2", SOURCE, downgrade_group="hl2",
                       downgrade_requires={"hl2/bin/client.dylib": sha256(b"hl2 client")}),
        make_component("Half-Life 2: Lost Coast", "lostcoast", SOURCE, id="lost-coast", downgrade_group="hl2",
                       downgrade_requires={"lostcoast/bin/client.dylib": sha256(b"lost coast client")}),
        make_component("Half-Life 2: Episodic", "episodic", SOURCE, id="episodic", downgrade_group="hl2",
                       downgrade_requires={"episodic/bin/client.dylib": sha256(b"episodic client")}),
    ])
    deathmatch = Game("Source (Half-Life 2 Deathmatch)", tmp_path / "Half-Life 2 Deathmatch", SOURCE, [
        make_component("Half-Life 2: Deathmatch", "hl2mp", SOURCE, id="half-life-2-deathmatch",
                       downgrade_requires={"hl2mp/bin/client.dylib": ""}),
    ])
    portal = Game("Source (Portal)", tmp_path / "Portal", SOURCE, [make_component("Portal", "portal", SOURCE)])
    app.context.games = [half_life_2, deathmatch, portal]
    app.context.selected_components = [*half_life_2.components[:2], *deathmatch.components, *portal.components]
    return {
        "hl2": (half_life_2.path / "hl2/bin/client.dylib", b"hl2 client"),
        "lost-coast": (half_life_2.path / "lostcoast/bin/client.dylib", b"lost coast client"),
        "deathmatch": (deathmatch.path / "hl2mp/bin/client.dylib", b"any client"),
    }


def downgrade(files, **contents):
    for name, (path, content) in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents.get(name, content))


@pytest.fixture
def open_downgrade_page(make_page, tk_root):
    def open_page():
        page = make_page(DowngradePage)
        status_bar = page.get_custom_footer_widget(ctk.CTkFrame(tk_root))
        page.on_enter()
        return page, status_bar

    return open_page


def status(status_bar):
    [label] = widgets(status_bar, ctk.CTkLabel)
    return label.cget("text")


def test_downgrade_shows_a_card_per_group_of_selected_components(open_downgrade_page, downgrade_files):
    page, _ = open_downgrade_page()
    page.on_enter()

    assert texts(page) == ["Half-Life 2downgrade_group_others count=1", "Half-Life 2: Deathmatch"]
    assert [button.cget("text") for button in widgets(page, ctk.CTkButton)] == ["downgrade_guide_btn"] * 2


def make_unreadable(files):
    downgrade(files)
    files["hl2"][0].chmod(0)


@pytest.mark.parametrize(("prepare", "expected_status", "enabled", "card_buttons"), [
    (lambda files: None, "downgrade_status_remaining count=3", False, ["downgrade_guide_btn"] * 2),
    (lambda files: downgrade(files, hl2=b"patched client"), "downgrade_status_remaining count=1", False,
     ["downgrade_guide_btn", "downgraded_success_btn"]),
    (make_unreadable, "downgrade_status_remaining count=1", False, ["downgrade_guide_btn", "downgraded_success_btn"]),
    (downgrade, "downgrade_status_all", True, ["downgraded_success_btn"] * 2),
], ids=["nothing-downgraded", "wrong-version", "unreadable", "all-downgraded"])
def test_downgrade_lets_you_continue_only_once_every_file_matches(open_downgrade_page, downgrade_files, tk_root, app,
                                                                  prepare, expected_status, enabled, card_buttons):
    prepare(downgrade_files)
    page, status_bar = open_downgrade_page()

    assert run_until(tk_root, lambda: status(status_bar) != "")

    assert (status(status_bar), app.footer.next_enabled) == (expected_status, enabled)
    assert [button.cget("text") for button in widgets(page, ctk.CTkButton)] == card_buttons


def test_downgrade_notices_the_files_as_soon_as_they_match(open_downgrade_page, downgrade_files, tk_root, app):
    _, status_bar = open_downgrade_page()
    assert run_until(tk_root, lambda: status(status_bar) != "")

    downgrade(downgrade_files)

    assert run_until(tk_root, lambda: app.footer.next_enabled is True, timeout=3)
    assert status(status_bar) == "downgrade_status_all"


def test_leaving_the_downgrade_page_stops_checking(open_downgrade_page, downgrade_files, tk_root, app):
    page, status_bar = open_downgrade_page()
    assert run_until(tk_root, lambda: status(status_bar) != "")
    page.on_leave()

    downgrade(downgrade_files)
    run_until(tk_root, lambda: False, timeout=1.3)

    assert app.footer.next_enabled is False


def test_downgrade_guide_button_opens_the_guide_of_its_group(open_downgrade_page, downgrade_files, guides, mocker):
    guides["hl2"] = GuideConfig("guide_hl2_title", [GuideStepConfig(
        "guide_hl2_step1_title", "guide_hl2_step1_desc", step_command="download_depot 220 221 5555555555555555555",
        step_button_text="guide_open_console", step_button_url="steam://open/console",
    )])
    copied = mocker.patch.object(BaseGuideWindow, "clipboard_append")
    mocker.patch.object(BaseGuideWindow, "clipboard_clear")
    opened = mocker.patch("webbrowser.open")
    page, _ = open_downgrade_page()
    hl2_button, deathmatch_button = widgets(page, ctk.CTkButton)

    deathmatch_button.invoke()
    assert widgets(page, BaseGuideWindow) == []
    hl2_button.invoke()
    [guide] = widgets(page, BaseGuideWindow)
    find(guide, ctk.CTkButton, "btn_copy").invoke()
    find(guide, ctk.CTkButton, "guide_open_console").invoke()

    assert guide.title() == "guide_hl2_title"
    assert texts(guide) == ["guide_hl2_title", "guide_hl2_step1_title", "guide_hl2_step1_desc"]
    copied.assert_called_once_with("download_depot 220 221 5555555555555555555")
    opened.assert_called_once_with("steam://open/console")


@pytest.fixture
def failure_report(mocker, tmp_path):
    report = mocker.patch("patcher.ui.pages.progress_page.FailureReport")
    report.return_value.write.return_value = tmp_path / "HLPatcher-failure-2026-10-06_14-03-11.zip"
    return report


@pytest.fixture
def progress_page(make_page, app, make_component, mocker, tmp_path, failure_report):
    mocker.patch("patcher.ui.pages.progress_page.Patcher", ScriptedPatcher)
    half_life_2 = Game("Source (Half-Life 2)", tmp_path / "Half-Life 2", SOURCE, [
        make_component("Half-Life 2", "hl2", SOURCE),
        make_component("Half-Life 2: Lost Coast", "lostcoast", SOURCE, id="lost-coast"),
        make_component("Half-Life 2: Episodic", "episodic", SOURCE, id="episodic"),
    ])
    app.context.games = [half_life_2]
    app.context.selected_components = half_life_2.components[:2]
    page = make_page(ProgressPage)
    page.on_enter()
    yield page
    page.stop_patching()
    eventually(lambda: not page.is_patching())


def test_progress_shows_the_component_and_step_being_patched(progress_page, tk_root, app):
    lost_coast = "progress_patching_comp component=Half-Life 2: Lost Coast"
    assert run_until(tk_root, lambda: lost_coast in texts(progress_page))
    overall, step = widgets(progress_page, ctk.CTkProgressBar)

    assert [comp.id for comp in progress_page.patcher.games[0].components] == ["half-life-2", "lost-coast"]
    assert (overall.get(), step.get()) == (0.5, 0.5)
    assert "progress_step_format current=1 total=2" in texts(progress_page)
    assert (app.footer.next_enabled, app.footer.back_enabled) == (False, False)

    progress_page.patcher.release.set()

    assert run_until(tk_root, lambda: app.router.shown == [PageRoute.SUCCESS])
    assert (overall.get(), step.get()) == (1.0, 1.0)


def test_progress_reports_a_failure_with_a_saved_log_file(progress_page, tk_root, app, failure_report, tmp_path):
    error = RuntimeError("git clone failed")
    progress_page.patcher.error = error

    progress_page.patcher.release.set()

    assert run_until(tk_root, lambda: app.router.shown == [PageRoute.FAILURE])
    patcher = progress_page.patcher
    failure_report.assert_called_once_with(app.context, app.config, patcher.timeline, patcher.executor)
    failure_report.return_value.write.assert_called_once_with(error)
    assert app.patching_error == "git clone failed"
    assert app.failure_report == tmp_path / "HLPatcher-failure-2026-10-06_14-03-11.zip"
    assert "progress_collecting_logs" in texts(progress_page)


def test_stopping_the_patch_is_not_reported_as_a_failure(progress_page, tk_root, app, failure_report):
    assert run_until(tk_root, lambda: "progress_step_format current=1 total=2" in texts(progress_page))

    progress_page.stop_patching()

    assert run_until(tk_root, lambda: not progress_page.is_patching())
    run_until(tk_root, lambda: False, timeout=0.2)

    assert app.router.shown == []
    assert app.patching_error == ""
    assert "progress_stopping" in texts(progress_page)
    failure_report.assert_not_called()


@pytest.mark.parametrize(("error", "shown"), [("git clone failed", "git clone failed"), ("", "failure_unknown")],
                         ids=["known-error", "unknown-error"])
def test_failure_page_shows_what_went_wrong(make_page, app, error, shown):
    app.patching_error = error
    page = make_page(FailurePage)

    page.on_enter()

    assert shown in texts(page)


def test_failure_page_offers_the_saved_log_file_in_finder(make_page, app, mocker, tmp_path):
    reveal = mocker.patch("patcher.ui.pages.failure_page.subprocess.run")
    app.failure_report = tmp_path / "HLPatcher-failure-2026-10-06_14-03-11.zip"
    page = make_page(FailurePage)

    page.on_enter()
    report_button = find(page, ctk.CTkButton, "failure_report_btn")
    report_button.invoke()

    shown = [widget.cget("text") for widget in report_button.master.pack_slaves() if isinstance(widget, ctk.CTkButton)]
    assert shown == ["failure_report_btn", "failure_issue_btn"]
    assert "failure_help_report" in texts(page)
    reveal.assert_called_once_with(["open", "-R", str(app.failure_report)])


def test_failure_page_asks_for_the_terminal_output_when_no_log_file_was_saved(make_page, app, tmp_path):
    app.failure_report = tmp_path / "HLPatcher-failure-2026-10-06_14-03-11.zip"
    page = make_page(FailurePage)
    page.on_enter()

    app.failure_report = None
    page.on_enter()

    assert "failure_help" in texts(page)
    assert "failure_help_report" not in texts(page)
    assert find(page, ctk.CTkButton, "failure_report_btn").winfo_manager() == ""
