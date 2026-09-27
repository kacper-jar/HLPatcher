import http.server
import subprocess
import threading
import time
import urllib.error
from pathlib import Path

import pytest

from patcher.core import EngineType, FetchStepConfig, Game, PatchMode
from patcher.core.pipeline.fetchers import GitFetcher, GoldSrcEngineFetcher, UrlFetcherStep

HLSDK_URL = "https://github.com/FWGS/hlsdk-portable"
XASH_URL = "https://github.com/FWGS/xash3d-fwgs"
SDL_URL = "https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.dmg"


def hlsdk_config(**fields):
    fields = {"url": HLSDK_URL, "patch_dir_name": "hlsdk-portable-hlfixed", "branch": "hlfixed",
              "stable_commit": "5bc5bec", **fields}
    return FetchStepConfig("git-fetcher", **fields)


def xash_config():
    return FetchStepConfig("goldsrc-engine-fetcher", url=XASH_URL, patch_dir_name="xash3d-fwgs",
                           stable_commit="8b5732b")


def url_config(url):
    return FetchStepConfig("url-fetcher", url=url, patch_dir_name="dejavu-fonts")


@pytest.fixture
def fetch(step_context, make_component):
    comp = make_component("Half-Life", "valve", engine_type=EngineType.GOLDSRC)
    game = Game("Half-Life", step_context.steam_library_path / "Half-Life", EngineType.GOLDSRC, [comp])
    return lambda step_class, config: step_class(step_context).execute(game, comp, config)


@pytest.fixture
def hlsdk_dir(step_context):
    return str(step_context.working_dir / "hlsdk-portable-hlfixed")


def test_git_fetcher_clones_the_branch_shallowly(fetch, hlsdk_dir, mock_run_command):
    fetch(GitFetcher, hlsdk_config())

    assert mock_run_command.commands == [
        (["git", "clone", "--recursive", "--shallow-submodules", "--depth", "1", "-b", "hlfixed", HLSDK_URL,
          hlsdk_dir], None),
    ]


def test_git_fetcher_clones_the_default_branch_when_none_is_set(fetch, hlsdk_dir, mock_run_command):
    fetch(GitFetcher, hlsdk_config(branch=""))

    assert mock_run_command.commands == [
        (["git", "clone", "--recursive", "--shallow-submodules", "--depth", "1", HLSDK_URL, hlsdk_dir], None),
    ]


@pytest.mark.parametrize("commit", ["5bc5bec", "5bc5bec3d2a1f0e9c8b7a6d5e4f3a2b1c0d9e8f7"], ids=["short", "full"])
def test_git_fetcher_checks_out_the_stable_commit_in_stable_mode(step_context, fetch, hlsdk_dir, mock_run_command,
                                                                 commit):
    step_context.patch_mode = PatchMode.STABLE

    fetch(GitFetcher, hlsdk_config(stable_commit=commit))

    assert mock_run_command.commands == [
        (["git", "clone", "--recursive", HLSDK_URL, hlsdk_dir], None),
        (["git", "checkout", commit], hlsdk_dir),
        (["git", "submodule", "update", "--init", "--recursive"], hlsdk_dir),
    ]


def test_git_fetcher_uses_the_stable_commit_when_forced(fetch, hlsdk_dir, mock_run_command):
    fetch(GitFetcher, hlsdk_config(force_stable=True))

    assert (["git", "checkout", "5bc5bec"], hlsdk_dir) in mock_run_command.commands


@pytest.mark.xfail(raises=AssertionError, strict=True,
                   reason="A commit is recognised only by its length, so a 12-character SHA is cloned as a branch")
def test_git_fetcher_checks_out_a_stable_commit_of_any_length(step_context, fetch, hlsdk_dir, mock_run_command):
    step_context.patch_mode = PatchMode.STABLE

    fetch(GitFetcher, hlsdk_config(stable_commit="5bc5bec3d2a1"))

    assert (["git", "checkout", "5bc5bec3d2a1"], hlsdk_dir) in mock_run_command.commands


def test_git_fetcher_skips_an_existing_checkout(step_context, fetch, mock_run_command):
    (step_context.working_dir / "hlsdk-portable-hlfixed").mkdir()

    fetch(GitFetcher, hlsdk_config())

    assert mock_run_command.commands == []
    step_context.log.assert_any_call("Directory hlsdk-portable-hlfixed already exists. Skipping fetch.")


@pytest.fixture
def sdl_disk_image(mocker, mock_run_command):
    def popen(cmd, *args, **kwargs):
        if cmd[:2] == ["hdiutil", "attach"]:
            framework = Path(cmd[cmd.index("-mountpoint") + 1]) / "SDL2.framework" / "Versions" / "A"
            framework.mkdir(parents=True)
            (framework / "SDL2").write_bytes(b"sdl")
        return mock_run_command(cmd, *args, **kwargs)

    mocker.patch("subprocess.Popen", side_effect=popen)
    return mock_run_command


def test_goldsrc_engine_fetcher_copies_sdl2_from_the_disk_image(step_context, fetch, sdl_disk_image):
    fetch(GoldSrcEngineFetcher, xash_config())

    framework = step_context.working_dir / "xash3d-fwgs" / "3rdparty" / "SDL2.framework"
    assert (framework / "Versions" / "A" / "SDL2").read_bytes() == b"sdl"

    dmg = str(step_context.working_dir / "SDL2-2.32.10.dmg")
    commands = [cmd for cmd, _ in sdl_disk_image.commands]
    attach = commands[2]
    mount_point = attach[attach.index("-mountpoint") + 1]
    assert commands[1:] == [
        ["curl", "-L", "-o", dmg, SDL_URL],
        ["hdiutil", "attach", dmg, "-nobrowse", "-readonly", "-mountpoint", mount_point],
        ["hdiutil", "detach", mount_point],
    ]
    assert Path(mount_point).name.startswith("HLPatcher-SDL2-")
    assert not Path(mount_point).exists()


def test_goldsrc_engine_fetcher_detaches_the_image_when_the_copy_fails(fetch, mock_run_command):
    with pytest.raises(FileNotFoundError):
        fetch(GoldSrcEngineFetcher, xash_config())

    attach, detach = mock_run_command.commands[2][0], mock_run_command.commands[3][0]
    assert detach == ["hdiutil", "detach", attach[attach.index("-mountpoint") + 1]]


def test_goldsrc_engine_fetcher_stops_when_the_image_does_not_mount(step_context, fetch, mocker):
    commands = []

    def popen(cmd, *args, **kwargs):
        commands.append(cmd)
        process = mocker.Mock(args=cmd)
        process.communicate.return_value = ("", "hdiutil: attach failed - image not recognized")
        process.poll.return_value = 1 if cmd[:2] == ["hdiutil", "attach"] else 0
        return process

    mocker.patch("subprocess.Popen", side_effect=popen)

    with pytest.raises(subprocess.CalledProcessError):
        fetch(GoldSrcEngineFetcher, xash_config())

    assert commands[-1][:2] == ["hdiutil", "attach"]
    assert not (step_context.working_dir / "xash3d-fwgs" / "3rdparty").exists()


def test_goldsrc_engine_fetcher_skips_an_existing_checkout(step_context, fetch, mock_run_command):
    (step_context.working_dir / "xash3d-fwgs").mkdir()

    fetch(GoldSrcEngineFetcher, xash_config())

    assert mock_run_command.commands == []


class DownloadHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in self.server.files:
            self.send_error(404)
            return
        chunks, delay = self.server.files[self.path]
        self.send_response(200)
        self.send_header("Content-Length", str(sum(map(len, chunks))))
        self.end_headers()
        for chunk in chunks:
            try:
                self.wfile.write(chunk)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return
            time.sleep(delay)

    def log_message(self, *args):
        pass


@pytest.fixture
def download_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), DownloadHandler)
    server.files = {}
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


def serve(server, path, chunks, delay=0.0):
    server.files[path] = (chunks, delay)
    return f"http://127.0.0.1:{server.server_address[1]}{path}"


def test_url_fetcher_downloads_the_archive_and_records_its_url(step_context, fetch, download_server):
    content = bytes(range(256)) * 800
    url = serve(download_server, "/dejavu-fonts-ttf-2.37.zip", [content[:100_000], content[100_000:]])

    fetch(UrlFetcherStep, url_config(url))

    download_dir = step_context.working_dir / "dejavu-fonts"
    assert (download_dir / "archive.tmp").read_bytes() == content
    assert (download_dir / "url.txt").read_text() == url


def test_url_fetcher_stops_mid_download(step_context, fetch, download_server):
    url = serve(download_server, "/slow.zip", [b"x" * 64 * 1024] * 40, delay=0.05)
    threading.Timer(0.2, step_context.executor.stop).start()
    started = time.monotonic()

    with pytest.raises(RuntimeError, match="Execution stopped by user"):
        fetch(UrlFetcherStep, url_config(url))

    assert time.monotonic() - started < 1.5


def test_url_fetcher_fails_on_http_errors(fetch, download_server):
    url = serve(download_server, "/dejavu-fonts-ttf-2.37.zip", [b"zip"])

    with pytest.raises(urllib.error.HTTPError, match="404"):
        fetch(UrlFetcherStep, url_config(url.replace("2.37", "9.99")))


def test_url_fetcher_passes_a_timeout_for_stalled_connections(fetch, mocker):
    urlopen = mocker.patch("urllib.request.urlopen", side_effect=TimeoutError("timed out"))

    with pytest.raises(TimeoutError):
        fetch(UrlFetcherStep, url_config("https://example.com/dejavu-fonts-ttf-2.37.zip"))

    assert 0 < urlopen.call_args.kwargs["timeout"] <= 60
