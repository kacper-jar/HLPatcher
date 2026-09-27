import http.server
import json
import threading

import pytest

from patcher.core import UpdateInfo, Updater

RELEASES_URL = "https://github.com/kacper-jar/HLPatcher/releases"


class GitHubHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.requests.append((self.path, self.headers.get("User-Agent")))
        status, body = self.server.reply
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def github():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), GitHubHandler)
    server.requests = []
    server.reply = (200, b"{}")
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def updater(github):
    updater = Updater()
    updater.api_url = updater.api_url.replace("https://api.github.com", f"http://127.0.0.1:{github.server_address[1]}")
    return updater


def release(tag):
    return {"tag_name": tag, "html_url": f"{RELEASES_URL}/tag/{tag}"}


def reply(github, data, status=200):
    github.reply = (status, data if isinstance(data, bytes) else json.dumps(data).encode())


def test_asks_github_for_the_latest_hlpatcher_release(github, updater):
    reply(github, release("3.3.0"))

    updater.check_for_update("3.2.1")

    assert Updater().api_url == "https://api.github.com/repos/kacper-jar/HLPatcher/releases/latest"
    assert github.requests == [("/repos/kacper-jar/HLPatcher/releases/latest", "HLPatcher-Updater")]


@pytest.mark.parametrize(("current", "tag", "available"), [
    ("3.2.0", "3.2.1", True),
    ("3.2.1", "3.2.1", False),
    ("3.3.0", "3.2.1", False),
    ("3.1.9", "3.1.10", True),
], ids=["newer", "same", "older", "numeric-order"])
def test_compares_the_latest_release_with_the_running_version(github, updater, current, tag, available):
    reply(github, release(tag))

    assert updater.check_for_update(current) == UpdateInfo(tag, available, f"{RELEASES_URL}/tag/{tag}")


def test_links_to_the_releases_page_when_the_release_has_no_link(github, updater):
    reply(github, {"tag_name": "3.3.0"})

    assert updater.check_for_update("3.2.1").release_url == RELEASES_URL


def test_skips_the_check_when_running_from_source(github, updater):
    assert updater.check_for_update("indev") is None
    assert github.requests == []


@pytest.mark.parametrize(("status", "data", "current"), [
    (403, {"message": "API rate limit exceeded"}, "3.2.1"),
    (404, {"message": "Not Found"}, "3.2.1"),
    (202, release("3.3.0"), "3.2.1"),
    (200, b"<html>Proxy error</html>", "3.2.1"),
    (200, {"html_url": f"{RELEASES_URL}/tag/3.3.0"}, "3.2.1"),
    (200, release("3.3.0"), "custom-build"),
], ids=["rate-limited", "no-releases", "not-200", "not-json", "no-tag", "running-version-not-a-version"])
def test_gives_up_quietly_without_a_usable_answer(github, updater, status, data, current):
    reply(github, data, status)

    assert updater.check_for_update(current) is None


def test_gives_up_quietly_when_github_cannot_be_reached(github, updater):
    github.shutdown()
    github.server_close()

    assert updater.check_for_update("3.2.1") is None


def test_waits_only_a_few_seconds_for_github(updater, mocker):
    urlopen = mocker.patch("urllib.request.urlopen", side_effect=TimeoutError("timed out"))

    assert updater.check_for_update("3.2.1") is None
    assert 0 < urlopen.call_args.kwargs["timeout"] <= 10
