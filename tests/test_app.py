from patcher.ui import PageRoute
import pytest

from patcher.app import App
from patcher.core import AppConfig, Component, EngineType, Game, PatchStatus


@pytest.fixture
def mock_app(mocker):
    mocker.patch("patcher.app.App.mainloop")
    mocker.patch("patcher.app.App._start_update_check")
    app = App(AppConfig())
    yield app
    app.update()
    app.destroy()


def test_app_initial_state(mock_app):
    assert mock_app.router.current_page_key == PageRoute.WELCOME
    assert len(mock_app.router._history) == 0


def test_app_navigation_next_back(mock_app, mocker):
    mocker.patch("patcher.ui.WelcomePage.can_go_next", return_value=True)
    mocker.patch("patcher.ui.WelcomePage.get_next_page_key", return_value=PageRoute.LIBRARY)

    mock_app.router.go_next()
    assert mock_app.router.current_page_key == PageRoute.LIBRARY
    assert mock_app.router._history == [PageRoute.WELCOME]

    mocker.patch("patcher.ui.LibraryPage.can_go_back", return_value=True)
    mocker.patch("patcher.ui.LibraryPage.get_back_page_key", return_value=PageRoute.WELCOME)

    mock_app.router.go_back()
    assert mock_app.router.current_page_key == PageRoute.WELCOME
    assert mock_app.router._history == []


def test_scan_and_route_no_games(mock_app, mocker):
    mocker.patch("patcher.app.GameDetector.scan", return_value=[])
    mock_app.router.show_page(PageRoute.LIBRARY)
    mock_app._scan_and_route()

    assert mock_app.router.current_page_key == PageRoute.NO_GAMES


def test_scan_and_route_all_patched(mock_app, mocker):
    game = Game("Test", None, EngineType.GOLDSRC)
    comp = Component("TestComp", "test", EngineType.GOLDSRC, PatchStatus.ALREADY_PATCHED, "")
    game.components.append(comp)

    mocker.patch("patcher.app.GameDetector.scan", return_value=[game])
    mock_app.router.show_page(PageRoute.LIBRARY)
    mock_app._scan_and_route()

    assert mock_app.router.current_page_key == PageRoute.ALL_PATCHED


def test_scan_and_route_needs_patch(mock_app, mocker):
    game = Game("Test", None, EngineType.GOLDSRC)
    comp = Component("TestComp", "test", EngineType.GOLDSRC, PatchStatus.NEEDS_PATCH, "")
    game.components.append(comp)

    mocker.patch("patcher.app.GameDetector.scan", return_value=[game])
    mock_app.router.show_page(PageRoute.LIBRARY)
    mock_app._scan_and_route()

    assert mock_app.router.current_page_key == PageRoute.SELECTION


def test_check_source_warning_with_source(mock_app):
    comp = Component("SourceComp", "test", EngineType.SOURCE, PatchStatus.NEEDS_PATCH, "")
    mock_app.context.selected_components = [comp]
    mock_app.router.show_page(PageRoute.OPTIONS)
    mock_app._check_source_warning()

    assert mock_app.router.current_page_key == PageRoute.WARNING


def test_check_source_warning_without_source(mock_app):
    comp = Component("GoldSrcComp", "test", EngineType.GOLDSRC, PatchStatus.NEEDS_PATCH, "")
    mock_app.context.selected_components = [comp]
    mock_app.router.show_page(PageRoute.OPTIONS)
    mock_app._check_source_warning()

    assert mock_app.router.current_page_key == PageRoute.PROGRESS
