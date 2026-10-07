import contextlib
import dataclasses
import fnmatch
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import tkinter
import traceback
import zipfile
from collections.abc import Callable, Iterator
from datetime import datetime
from importlib import metadata
from pathlib import Path

import patcher
from patcher.core.command_executor import CommandExecutor
from patcher.core.models import AppConfig, Game, PatchContext, StepRecord
from patcher.core.session_log import SessionLog

logger = logging.getLogger(__name__)

PROBE_TIMEOUT = 60
TOOLS = ["git", "python3", "make", "cmake", "ninja", "meson", "perl", "curl", "patch"]
VENV_TOOLS = ["python3", "cmake", "ninja", "meson"]
ENVIRONMENT = ["PATH", "CC", "CXX", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "PKG_CONFIG_PATH", "SDKROOT",
               "MACOSX_DEPLOYMENT_TARGET", "DEVELOPER_DIR", "SHELL", "LANG", "LC_ALL"]
BUILD_LOGS = ["*.log", "CMakeConfigureLog.yaml"]
SKIPPED_FOLDERS = {".git", "venv"}
MAX_TREE_ENTRIES = 100_000
MAX_BINARIES = 500
MACH_O_MAGICS = {bytes.fromhex(magic) for magic in ("feedface", "feedfacf", "cefaedfe", "cffaedfe", "cafebabe")}
GIGABYTE = 1024 ** 3


class FailureReport:
    def __init__(self, context: PatchContext, config: AppConfig, timeline: list[StepRecord], executor: CommandExecutor):
        self._context = context
        self._config = config
        self._timeline = timeline
        self._executor = executor

    def write(self, error: BaseException) -> Path | None:
        path = SessionLog.folder() / f"HLPatcher-failure-{datetime.now():%Y-%m-%d_%H-%M-%S}.zip"
        partial = path.with_name(f"{path.name}.partial")
        logger.info("Collecting logs for the failure report...")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(partial, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, text in self._files(error):
                    archive.writestr(name, text.replace(str(Path.home()), "~"))
            partial.rename(path)
            SessionLog.prune("HLPatcher-failure-*.zip")
        except Exception:
            logger.exception("Couldn't write the failure report")
            with contextlib.suppress(OSError):
                partial.unlink(missing_ok=True)
            return None
        logger.info(f"Saved the failure report to {path}")
        return path

    def _files(self, error: BaseException) -> Iterator[tuple[str, str]]:
        yield "report.txt", self._report(error)
        yield "session.log", self._session_log()
        yield "working-folder.txt", self._collect(self._working_folder)
        for clone in self._clones():
            yield f"git/{clone.name}.txt", self._collect(lambda: self._git(clone))
        yield from self._build_logs()

    def _report(self, error: BaseException) -> str:
        sections = [
            ("Error", lambda: "".join(traceback.format_exception(error)).rstrip()),
            ("Failed step", self._failed_step),
            ("Last command", lambda: self._last_command(error)),
            ("Session", self._session),
            ("Timeline", self._timeline_text),
            ("Game folders", self._game_folders),
            ("Machine", self._machine),
            ("Toolchain", self._toolchain),
            ("Environment", self._environment),
            ("Python", self._python),
        ]
        parts = [f"HLPatcher failure report, {datetime.now().astimezone():%Y-%m-%d %H:%M:%S %z}"]
        parts += [f"== {title}\n{self._collect(describe)}" for title, describe in sections]
        return "\n\n".join(parts) + "\n"

    def _collect(self, describe: Callable[[], str]) -> str:
        try:
            return describe()
        except Exception as e:
            logger.exception("Couldn't collect part of the failure report")
            return f"Couldn't collect this: {e!r}"

    def _failed_record(self) -> StepRecord | None:
        if self._timeline and self._timeline[-1].finished is None:
            return self._timeline[-1]
        return None

    def _failed_step(self) -> str:
        record = self._failed_record()
        if not record:
            return ("No patch step was running, so it failed while backing up, preparing the build environment "
                    "or cleaning up.")
        elapsed = (datetime.now() - record.started).total_seconds()
        return "\n".join([
            f"Game: {record.game.name}",
            f"Component: {record.component.name} ({record.component.id})",
            f"Step: {record.number} of {record.total}, {record.config.type}",
            f"Started: {record.started:%H:%M:%S}, failed after {elapsed:.1f}s",
            f"Config: {json.dumps(dataclasses.asdict(record.config), indent=2)}",
        ])

    def _last_command(self, error: BaseException) -> str:
        if not self._executor.last_command:
            return "No command was run."
        lines = [
            f"Command: {shlex.join(self._executor.last_command)}",
            f"Folder: {self._executor.last_cwd or 'the app folder'}",
        ]
        failed = self._called_process_error(error)
        if failed:
            lines.append(f"Exit code: {failed.returncode}")
        output = self._executor.recent_output.copy()
        lines.append("Last lines of its output:")
        lines += output
        return "\n".join(lines)

    @staticmethod
    def _called_process_error(error: BaseException | None) -> subprocess.CalledProcessError | None:
        while error:
            if isinstance(error, subprocess.CalledProcessError):
                return error
            error = error.__cause__ or error.__context__
        return None

    def _session(self) -> str:
        context = self._context
        lines = [
            f"HLPatcher version: {patcher.__version__ or 'unknown'}",
            f"Debug mode: {self._config.debug}",
            f"Launched from: {context.script_dir}",
            f"Steam library: {context.steam_library_path if context.steam_library_path != Path() else 'not chosen'}",
            f"Patch mode: {context.patch_mode.value}",
            f"Back up games: {context.create_backup}",
            f"Working folder: {context.working_dir}",
            "Selected components: " + (", ".join(f"{c.name} ({c.id})" for c in context.selected_components) or "none"),
            "Detected games:" if context.games else "Detected games: none",
        ]
        for game in context.games:
            lines.append(f"  {game.name} ({game.engine_type.value}) at {game.path}")
            lines += [f"    {c.name} ({c.id}): {c.status.value}" for c in game.components]
        return "\n".join(lines)

    def _timeline_text(self) -> str:
        if not self._timeline:
            return "No patch step started."
        lines = []
        for record in self._timeline:
            if record.finished:
                result = f"done in {(record.finished - record.started).total_seconds():.1f}s"
            else:
                result = "FAILED"
            lines.append(f"{record.started:%H:%M:%S}  {record.component.name}, step {record.number} of "
                         f"{record.total} ({record.config.type}): {result}")
        return "\n".join(lines)

    def _game_folders(self) -> str:
        record = self._failed_record()
        selected = self._context.selected_components
        if record:
            games = [record.game]
        else:
            games = [game for game in self._context.games if any(c in game.components for c in selected)]
        if not games:
            return "No game was being patched."
        return "\n\n".join(self._game_folder(game) for game in games)

    def _game_folder(self, game: Game) -> str:
        lines = [f"{game.name} at {game.path}"]
        if not game.path.is_dir():
            return f"{lines[0]}: the folder doesn't exist."
        backups = sorted((Path.home() / "Documents").glob(f"{game.name} backup (*"))
        lines.append("Backups: " + (", ".join(backup.name for backup in backups) or "none"))
        binaries = []
        for folder, _, files in os.walk(game.path):
            for name in sorted(files):
                path = Path(folder) / name
                if path.suffix in (".dylib", ".so") or os.access(path, os.X_OK):
                    if self._is_mach_o(path):
                        binaries.append(path)
        lines.append(f"Binaries ({len(binaries)}):")
        for path in binaries[:MAX_BINARIES]:
            info = path.stat()
            archs = self._run("lipo", "-archs", str(path))
            lines.append(f"  {path.relative_to(game.path)}  {info.st_size} bytes  "
                         f"{datetime.fromtimestamp(info.st_mtime):%Y-%m-%d %H:%M}  {archs}")
        return "\n".join(lines)

    @staticmethod
    def _is_mach_o(path: Path) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(4) in MACH_O_MAGICS
        except OSError:
            return False

    def _machine(self) -> str:
        memory = self._run("sysctl", "-n", "hw.memsize")
        lines = [
            f"macOS: {self._run('sw_vers', '-productVersion')} ({self._run('sw_vers', '-buildVersion')})",
            f"Model: {self._run('sysctl', '-n', 'hw.model')}",
            f"Chip: {self._run('sysctl', '-n', 'machdep.cpu.brand_string')}",
            f"Memory: {int(memory) / GIGABYTE:.0f} GB" if memory.isdigit() else f"Memory: {memory}",
            f"Running under Rosetta: {self._run('sysctl', '-n', 'sysctl.proc_translated') == '1'}",
            f"Rosetta installed: {self._run('arch', '-x86_64', '/usr/bin/true') == ''}",
        ]
        for label, path in [("System disk", Path("/")), ("Working folder disk", self._context.working_dir),
                            ("Steam library disk", self._context.steam_library_path)]:
            lines.append(f"{label}: {self._free_space(path)}")
        return "\n".join(lines)

    @staticmethod
    def _free_space(path: Path) -> str:
        existing = next((folder for folder in [path, *path.parents] if folder.exists()), Path("/"))
        usage = shutil.disk_usage(existing)
        return f"{usage.free / GIGABYTE:.1f} GB free of {usage.total / GIGABYTE:.1f} GB ({existing})"

    def _toolchain(self) -> str:
        xcode = Path("/Applications/Xcode.app")
        lines = [
            f"Developer folder: {self._run('xcode-select', '-p')}",
            f"Command Line Tools: {self._indent(self._run('pkgutil', '--pkg-info=com.apple.pkg.CLTools_Executables'))}",
            f"Xcode: {self._indent(self._run('xcodebuild', '-version')) if xcode.exists() else 'not installed'}",
            f"clang: {self._indent(self._run('clang', '--version'))}",
            f"SDK: {self._run('xcrun', '--show-sdk-path')} ({self._run('xcrun', '--show-sdk-version')})",
            "On PATH:",
        ]
        lines += [f"  {tool}: {self._tool(shutil.which(tool))}" for tool in TOOLS]
        venv_bin = self._context.working_dir / "venv" / "bin"
        lines.append(f"In the build venv ({venv_bin}):")
        lines += [f"  {tool}: {self._tool(venv_bin / tool if (venv_bin / tool).exists() else None)}"
                  for tool in VENV_TOOLS]
        return "\n".join(lines)

    def _tool(self, path: str | Path | None) -> str:
        if not path:
            return "not found"
        version = next((line for line in self._run(str(path), "--version").splitlines() if line.strip()), "")
        return f"{path}, {version}"

    @staticmethod
    def _environment() -> str:
        names = ENVIRONMENT + sorted(name for name in os.environ if name.startswith("DYLD_"))
        return "\n".join(f"{name}={os.environ.get(name, '(not set)')}" for name in names)

    def _python(self) -> str:
        venv = self._context.working_dir / "venv"
        venv_python = venv / "bin" / "python3"
        venv_config = venv / "pyvenv.cfg"
        lines = [
            f"App Python: {sys.version.splitlines()[0]} at {sys.executable}",
            f"Tk: {tkinter.TkVersion}",
            f"customtkinter: {metadata.version('customtkinter')}",
            "App packages:",
            "  " + self._indent(self._run(sys.executable, "-m", "pip", "freeze")),
            f"Build venv ({venv}):",
        ]
        if not venv_python.exists():
            lines.append("  not created")
            return "\n".join(lines)
        venv_settings = venv_config.read_text(errors="replace").strip() if venv_config.exists() else "no pyvenv.cfg"
        lines += [
            "  " + self._run(str(venv_python), "--version"),
            "  " + self._indent(venv_settings),
            "Build venv packages:",
            "  " + self._indent(self._run(str(venv_python), "-m", "pip", "freeze")),
        ]
        return "\n".join(lines)

    def _session_log(self) -> str:
        path = SessionLog.current()
        if not path or not path.exists():
            return "This session's log wasn't saved.\n"
        return path.read_text(encoding="utf-8", errors="replace")

    def _working_folder(self) -> str:
        root = self._context.working_dir
        if not root.is_dir():
            return f"The working folder {root} doesn't exist.\n"
        lines = [f"{root}"]
        for folder, folders, files in os.walk(root):
            folder = Path(folder)
            skipped = sorted(name for name in folders if name in SKIPPED_FOLDERS)
            folders[:] = sorted(name for name in folders if name not in SKIPPED_FOLDERS)
            for name in skipped + folders + sorted(files):
                if len(lines) > MAX_TREE_ENTRIES:
                    lines.append(f"... stopped after {MAX_TREE_ENTRIES} entries")
                    return "\n".join(lines) + "\n"
                lines.append(self._tree_line(root, folder / name, name in skipped))
        return "\n".join(lines) + "\n"

    @staticmethod
    def _tree_line(root: Path, path: Path, skipped: bool) -> str:
        try:
            info = path.lstat()
        except OSError as e:
            return f"{'?':>12}  {'?':16}  {path.relative_to(root)}  ({e.strerror})"
        kind = "/" if path.is_dir() and not path.is_symlink() else ""
        note = "  (contents not listed)" if skipped else ""
        return (f"{info.st_size:>12}  {datetime.fromtimestamp(info.st_mtime):%Y-%m-%d %H:%M}  "
                f"{path.relative_to(root)}{kind}{note}")

    def _clones(self) -> list[Path]:
        root = self._context.working_dir
        if not root.is_dir():
            return []
        return sorted(folder for folder in root.iterdir() if (folder / ".git").exists())

    def _git(self, clone: Path) -> str:
        def git(*args: str) -> str:
            return self._run("git", "-c", "core.quotepath=off", *args, cwd=clone)

        return "\n".join([
            f"Remote: {git('remote', 'get-url', 'origin')}",
            f"Commit: {git('rev-parse', 'HEAD')}",
            f"Branch: {git('rev-parse', '--abbrev-ref', 'HEAD')}",
            "== Status", git("status", "--short"),
            "== Submodules", git("submodule", "status", "--recursive"),
            "== Diff", git("diff"),
        ]) + "\n"

    def _build_logs(self) -> Iterator[tuple[str, str]]:
        root = self._context.working_dir
        if not root.is_dir():
            return
        for folder, folders, files in os.walk(root):
            folders[:] = sorted(name for name in folders if name not in SKIPPED_FOLDERS)
            for name in sorted(files):
                if any(fnmatch.fnmatch(name, pattern) for pattern in BUILD_LOGS):
                    path = Path(folder) / name
                    log = self._collect(lambda: path.read_bytes().decode(errors="replace"))
                    yield f"build-logs/{path.relative_to(root)}", log

    @staticmethod
    def _indent(text: str) -> str:
        return text.replace("\n", "\n  ")

    @staticmethod
    def _run(*cmd: str, cwd: Path | None = None) -> str:
        try:
            result = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                    errors="replace", timeout=PROBE_TIMEOUT)
        except (OSError, subprocess.TimeoutExpired) as e:
            return f"<{e}>"
        output = (result.stdout + result.stderr).rstrip()
        return output if result.returncode == 0 else f"{output} <exit code {result.returncode}>"
