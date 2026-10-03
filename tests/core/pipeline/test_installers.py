import io
import tarfile
import zipfile

import pytest

from patcher.core.models import ArchiveInstallStepConfig, EngineType, Game, InstallStepConfig, SourceInstallStepConfig
from patcher.core.pipeline.installers import ArchiveInstallerStep, GenericInstaller, GoldSrcEngineInstaller, \
    SourceInstaller


def write_zip(path, files):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def write_tar(path, files):
    with tarfile.open(path, "w:gz") as archive:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def write_file(path, data=b""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


@pytest.fixture
def make_game(tmp_path, make_component):
    def factory(folder, subfolder, engine_type=EngineType.SOURCE):
        path = tmp_path / folder
        path.mkdir(exist_ok=True)
        return Game(folder, path, engine_type, [make_component(folder, subfolder, engine_type=engine_type)])

    return factory


def test_generic_installer_merges_the_build_output_into_the_game(step_context, make_game):
    game = make_game("Half-Life", "valve", EngineType.GOLDSRC)
    output = step_context.working_dir / "hlsdk-portable-hlfixed" / "output"
    write_file(output / "valve" / "dlls" / "hl_arm64.dylib", b"server")
    write_file(output / "valve" / "cl_dlls" / "client_arm64.dylib", b"client")
    write_file(game.path / "valve" / "liblist.gam", b"game info")

    config = InstallStepConfig("generic-installer", patch_dir_name="hlsdk-portable-hlfixed")
    GenericInstaller(step_context).execute(game, game.components[0], config)

    assert (game.path / "valve" / "dlls" / "hl_arm64.dylib").read_bytes() == b"server"
    assert (game.path / "valve" / "cl_dlls" / "client_arm64.dylib").read_bytes() == b"client"
    assert (game.path / "valve" / "liblist.gam").read_bytes() == b"game info"


def test_goldsrc_engine_installer_replaces_hl_osx_with_xash3d(step_context, make_game):
    game = make_game("Half-Life", "", EngineType.GOLDSRC)
    xash_dir = step_context.working_dir / "xash3d-fwgs"
    write_file(xash_dir / "output" / "xash3d", b"xash3d launcher")
    write_file(xash_dir / "output" / "libxash.dylib", b"engine")
    write_file(xash_dir / "3rdparty" / "SDL2.framework" / "Versions" / "A" / "SDL2", b"sdl")
    write_file(game.path / "hl_osx", b"valve launcher")

    GoldSrcEngineInstaller(step_context).execute(
        game, game.components[0], InstallStepConfig("goldsrc-engine-installer", patch_dir_name="xash3d-fwgs"))

    assert (game.path / "hl_osx").read_bytes() == b"xash3d launcher"
    assert not (game.path / "xash3d").exists()
    assert (game.path / "libxash.dylib").read_bytes() == b"engine"
    assert (game.path / "SDL2.framework" / "Versions" / "A" / "SDL2").read_bytes() == b"sdl"


def test_goldsrc_engine_installer_leaves_the_game_untouched_without_xash3d(step_context, make_game):
    game = make_game("Half-Life", "", EngineType.GOLDSRC)
    write_file(step_context.working_dir / "xash3d-fwgs" / "output" / "libxash.dylib", b"engine")
    write_file(game.path / "hl_osx", b"valve launcher")

    with pytest.raises(FileNotFoundError, match="xash3d launcher not found"):
        GoldSrcEngineInstaller(step_context).execute(
            game, game.components[0], InstallStepConfig("goldsrc-engine-installer", patch_dir_name="xash3d-fwgs"))

    assert [p.name for p in game.path.iterdir()] == ["hl_osx"]
    assert (game.path / "hl_osx").read_bytes() == b"valve launcher"


@pytest.fixture
def download_dir(step_context):
    path = step_context.working_dir / "dejavu-fonts"
    path.mkdir()
    return path


@pytest.fixture
def install_archive(step_context, make_game):
    game = make_game("Counter-Strike Source", "cstrike")

    def run(pattern="*.ttf"):
        config = ArchiveInstallStepConfig("archive-installer", patch_dir_name="dejavu-fonts",
                                          output_dir="platform/resource/linux_fonts", file_pattern=pattern)
        ArchiveInstallerStep(step_context).execute(game, game.components[0], config)
        return game.path / "platform" / "resource" / "linux_fonts"

    return run


def test_archive_installer_copies_matching_files_from_a_zip(download_dir, install_archive):
    write_zip(download_dir / "archive.tmp", {
        "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf": b"sans",
        "dejavu-fonts-ttf-2.37/ttf/DejaVuSerif.ttf": b"serif",
        "dejavu-fonts-ttf-2.37/LICENSE": b"license",
    })

    fonts = install_archive()

    assert sorted(p.name for p in fonts.iterdir()) == ["DejaVuSans.ttf", "DejaVuSerif.ttf"]
    assert (fonts / "DejaVuSans.ttf").read_bytes() == b"sans"


def test_archive_installer_copies_matching_files_from_a_tarball(download_dir, install_archive):
    write_tar(download_dir / "archive.tmp", {"liberation-fonts-ttf-2.1.5/LiberationSans-Regular.ttf": b"sans"})

    fonts = install_archive()

    assert (fonts / "LiberationSans-Regular.ttf").read_bytes() == b"sans"


def test_archive_installer_refuses_a_download_that_is_not_an_archive(download_dir, install_archive):
    (download_dir / "archive.tmp").write_bytes(b"<html>Rate limit exceeded</html>")

    with pytest.raises(ValueError, match="Unsupported archive format"):
        install_archive()


def test_archive_installer_fails_when_nothing_matches(download_dir, install_archive):
    write_zip(download_dir / "archive.tmp", {"dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf": b"sans"})

    with pytest.raises(ValueError, match=r"No files matching '\*\.otf'"):
        install_archive(pattern="*.otf")


def test_archive_installer_refuses_two_files_with_the_same_name(download_dir, install_archive):
    write_zip(download_dir / "archive.tmp", {
        "dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf": b"sans",
        "dejavu-fonts-ttf-2.37/ttf-hinted/DejaVuSans.ttf": b"hinted sans",
    })

    with pytest.raises(ValueError, match="more than one file named DejaVuSans.ttf"):
        install_archive()


def test_archive_installer_needs_the_downloaded_archive(download_dir, install_archive):
    with pytest.raises(FileNotFoundError, match="Archive not found"):
        install_archive()


@pytest.mark.parametrize("write_archive", [write_zip, write_tar], ids=["zip", "tar"])
def test_archive_installer_keeps_entries_with_parent_paths_inside_the_output_folder(download_dir, install_archive,
                                                                                   tmp_path, write_archive):
    write_archive(download_dir / "archive.tmp", {"../../escaped.ttf": b"outside"})

    fonts = install_archive()

    assert (fonts / "escaped.ttf").read_bytes() == b"outside"
    assert list(tmp_path.rglob("escaped.ttf")) == [fonts / "escaped.ttf"]


def test_archive_installer_skips_links_in_a_tarball(download_dir, install_archive):
    with tarfile.open(download_dir / "archive.tmp", "w:gz") as archive:
        link = tarfile.TarInfo("fonts/Linked.ttf")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/hosts"
        archive.addfile(link)
        font = tarfile.TarInfo("fonts/LiberationSans-Regular.ttf")
        font.size = 4
        archive.addfile(font, io.BytesIO(b"sans"))

    fonts = install_archive()

    assert [p.name for p in fonts.iterdir()] == ["LiberationSans-Regular.ttf"]


@pytest.fixture
def source_dir(step_context):
    return step_context.working_dir / "source-engine"


def install_source(step_context, game, steam_executable=""):
    config = SourceInstallStepConfig("source-installer", patch_dir_name="source-engine",
                                     steam_executable=steam_executable)
    SourceInstaller(step_context).execute(game, game.components[0], config)


def test_source_installer_copies_engine_mod_and_third_party_libraries(step_context, make_game, source_dir,
                                                                      mock_run_command):
    game = make_game("Half-Life 2", "hl2")
    write_file(source_dir / "output" / "bin" / "libtier0.dylib", b"tier0")
    write_file(source_dir / "output" / "hl2" / "bin" / "libclient.dylib", b"client")
    write_file(source_dir / "thirdparty" / "install" / "lib" / "libz.1.3.1.dylib", b"zlib")

    install_source(step_context, game)

    assert (game.path / "bin" / "libtier0.dylib").read_bytes() == b"tier0"
    assert (game.path / "hl2" / "bin" / "libclient.dylib").read_bytes() == b"client"
    assert (game.path / "bin" / "libz.1.3.1.dylib").read_bytes() == b"zlib"


def test_source_installer_installs_lost_coast_from_the_hl2_build(step_context, make_game, source_dir,
                                                                 mock_run_command):
    game = make_game("Half-Life 2", "lostcoast")
    write_file(source_dir / "output" / "hl2" / "bin" / "libclient.dylib", b"client")

    install_source(step_context, game)

    assert (game.path / "lostcoast" / "bin" / "libclient.dylib").read_bytes() == b"client"


def test_source_installer_replaces_the_hl2_launcher(step_context, make_game, source_dir, mock_run_command):
    game = make_game("Half-Life 2", "hl2")
    write_file(source_dir / "output" / "hl2_launcher", b"new launcher")
    write_file(game.path / "hl2_osx", b"old launcher")

    install_source(step_context, game)

    assert (game.path / "hl2_osx").read_bytes() == b"new launcher"
    assert (game.path / "hl2_osx").stat().st_mode & 0o777 == 0o755


def test_source_installer_relinks_engine_libraries(step_context, make_game, source_dir, mock_run_command):
    game = make_game("Half-Life 2", "hl2")
    write_file(source_dir / "output" / "bin" / "libtier0.dylib")
    write_file(source_dir / "output" / "bin" / "libvstdlib.dylib")
    build = source_dir / "build"

    install_source(step_context, game)

    bin_dir = str(game.path / "bin")
    assert (["install_name_tool", "-id", "@loader_path/libtier0.dylib", "libtier0.dylib"], bin_dir) \
           in mock_run_command.commands
    assert (["install_name_tool", "-id", "@loader_path/libvstdlib.dylib",
             "-change", f"{build}/tier0/libtier0.dylib", "@loader_path/libtier0.dylib", "libvstdlib.dylib"], bin_dir) \
           in mock_run_command.commands
    assert len(mock_run_command.commands) == 2


def test_source_installer_relinks_mod_libraries(step_context, make_game, source_dir, mock_run_command):
    game = make_game("Half-Life 2", "hl2")
    write_file(source_dir / "output" / "hl2" / "bin" / "libclient.dylib")
    write_file(source_dir / "output" / "hl2" / "bin" / "libserver.dylib")
    build = source_dir / "build"
    engine_changes = [
        "-change", f"{build}/vstdlib/libvstdlib.dylib", "@loader_path/../../bin/libvstdlib.dylib",
        "-change", f"{build}/tier0/libtier0.dylib", "@loader_path/../../bin/libtier0.dylib",
        "-change", f"{build}/stub_steam/libsteam_api.dylib", "@loader_path/../../bin/libsteam_api.dylib",
    ]

    install_source(step_context, game)

    commands = {cmd[-1]: (cmd, cwd) for cmd, cwd in mock_run_command.commands}
    mod_bin = str(game.path / "hl2" / "bin")
    assert commands["libserver.dylib"] == (
        ["install_name_tool", "-id", "@loader_path/libserver.dylib", *engine_changes, "libserver.dylib"], mod_bin)
    client_cmd, client_cwd = commands["libclient.dylib"]
    assert client_cmd[:3 + len(engine_changes)] == ["install_name_tool", "-id", "@loader_path/libclient.dylib",
                                                    *engine_changes]
    assert client_cwd == mod_bin


def test_source_installer_installs_the_steam_launcher(step_context, make_game, source_dir, mock_run_command):
    game = make_game("Day of Defeat Source", "dod")
    write_file(source_dir / "output" / "steam_launcher", b"launcher")
    write_file(game.path / "old_launcher", b"old")
    (game.path / "dod.exe").symlink_to("old_launcher")

    install_source(step_context, game, steam_executable="dod.exe")

    steam_exe = game.path / "dod.exe"
    assert not steam_exe.is_symlink()
    assert steam_exe.read_bytes() == b"launcher"
    assert steam_exe.stat().st_mode & 0o777 == 0o755
    assert (game.path / "old_launcher").read_bytes() == b"old"


def test_source_installer_needs_the_steam_launcher_when_configured(step_context, make_game, source_dir,
                                                                   mock_run_command):
    game = make_game("Day of Defeat Source", "dod")
    write_file(source_dir / "output" / "bin" / "libtier0.dylib")

    with pytest.raises(FileNotFoundError, match="Steam launcher not found"):
        install_source(step_context, game, steam_executable="dod.exe")

    assert not (game.path / "bin").exists()
