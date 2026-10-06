import contextlib
import dataclasses
import json
import logging
import shlex
import subprocess
import traceback
import zipfile
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path

import patcher
from patcher.core.command_executor import CommandExecutor
from patcher.core.models import AppConfig, PatchContext, StepRecord
from patcher.core.session_log import SessionLog

logger = logging.getLogger(__name__)


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

    def _report(self, error: BaseException) -> str:
        sections = [
            ("Error", lambda: "".join(traceback.format_exception(error)).rstrip()),
            ("Failed step", self._failed_step),
            ("Last command", lambda: self._last_command(error)),
            ("Session", self._session),
            ("Timeline", self._timeline_text),
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

    def _session_log(self) -> str:
        path = SessionLog.current()
        if not path or not path.exists():
            return "This session's log wasn't saved.\n"
        return path.read_text(encoding="utf-8", errors="replace")
