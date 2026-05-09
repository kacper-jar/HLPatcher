import urllib.error
from unittest.mock import Mock

from patcher.core.updater import Updater


def test_check_for_update_available(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")
    mock_response = Mock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"tag_name": "v3.1.0", "html_url": "https://github.com/fake/releases/tag/v3.1.0"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    updater = Updater()
    info = updater.check_for_update("3.0.0")

    assert info.update_available is True
    assert info.latest_version == "3.1.0"
    assert info.release_url == "https://github.com/fake/releases/tag/v3.1.0"


def test_check_for_update_not_available(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen")
    mock_response = Mock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"tag_name": "v3.0.0", "html_url": "https://github.com/fake/releases/tag/v3.0.0"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    updater = Updater()
    info = updater.check_for_update("3.0.0")

    assert info.update_available is False
    assert info.latest_version == "3.0.0"


def test_check_for_update_error(mocker):
    mock_urlopen = mocker.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network error"))

    updater = Updater()
    info = updater.check_for_update("3.0.0")

    assert info is None
