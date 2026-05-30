from patcher.ui import PageRoute
from unittest.mock import Mock

import pytest
import customtkinter as ctk

from patcher.ui.pages import OptionsPage, WelcomePage


@pytest.fixture
def mock_app_context():
    app = Mock()
    app.context = Mock()
    app.context.patch_mode = None
    app.context.create_backup = False
    return app


def test_welcome_page(mock_app_context):
    master = ctk.CTkFrame(ctk.CTk())
    page = WelcomePage(master, mock_app_context)

    assert "Welcome" in page.get_title()
    assert page.get_next_page_key() == PageRoute.LIBRARY
    assert page.show_back_button() is False


def test_options_page(mock_app_context):
    master = ctk.CTkFrame(ctk.CTk())
    page = OptionsPage(master, mock_app_context)

    assert page.get_title() == "Patching Options"
    assert page.get_next_page_key() == PageRoute.CHECK_SOURCE_WARNING

    from patcher.core.models import PatchMode
    page._mode_var.set(PatchMode.LATEST.value)
    page._backup_var.set(True)

    page.on_leave()

    assert mock_app_context.context.patch_mode == PatchMode.LATEST
    assert mock_app_context.context.create_backup is True
