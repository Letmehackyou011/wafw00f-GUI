from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
import logging
from queue import Queue
import re
from typing import Callable


@dataclass
class ScanConfig:
    target_url: str = ""
    find_all: bool = False
    verbose_level: int = 0
    no_redirect: bool = False
    no_colors: bool = False
    list_only: bool = False
    version_only: bool = False
    test_name: str = ""
    output_file: str = ""
    output_format: str = ""
    input_file: str = ""
    proxy: str = ""
    headers_file: str = ""
    request_timeout: int | None = None
    extra_args: str = ""
    execution_timeout_seconds: int = 180


@dataclass
class ScanResult:
    target_url: str
    command: list[str]
    started_at: str
    finished_at: str
    exit_code: int | None
    output: str
    stopped: bool = False
    error_message: str | None = None
    detected_wafs: list[str] = field(default_factory=list)
    request_count: int | None = None


LOGGER = logging.getLogger(__name__)


class Wafw00fRunner:
    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._stop_requested = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def run_async(
        self,
        config: ScanConfig,
        line_callback: Callable[[str], None],
        done_callback: Callable[[ScanResult], None],
    ) -> None:
        if self.is_running:
            raise RuntimeError("A scan is already running")

        self._stop_requested.clear()
        self._thread = threading.Thread(
            target=self._run_worker,
            args=(config, line_callback, done_callback),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_requested.set()
        if self._process and self.is_running:
            self._terminate_process()

    def _build_command(self, config: ScanConfig) -> list[str]:
        command = self._resolve_wafw00f_command()
        extra_parts: list[str] = []

        if config.find_all:
            command.append("-a")
        if config.no_redirect:
            command.append("-r")
        if config.no_colors:
            command.append("--no-colors")
        if config.list_only:
            command.append("-l")
        if config.version_only:
            command.append("-V")

        for _ in range(max(config.verbose_level, 0)):
            command.append("-v")

        if config.test_name.strip():
            command.extend(["-t", config.test_name.strip()])
        if config.output_file.strip():
            command.extend(["-o", config.output_file.strip()])
        if config.output_format.strip():
            command.extend(["-f", config.output_format.strip()])
        if config.input_file.strip():
            command.extend(["-i", config.input_file.strip()])
        if config.proxy.strip():
            command.extend(["-p", config.proxy.strip()])
        if config.headers_file.strip():
            command.extend(["-H", config.headers_file.strip()])
        if config.request_timeout is not None and config.request_timeout > 0:
            command.extend(["-T", str(config.request_timeout)])

        if config.extra_args.strip():
            try:
                parts = shlex.split(config.extra_args, posix=(os.name != "nt"))
            except ValueError as exc:
                raise ValueError(f"Invalid extra arguments: {exc}") from exc
            extra_parts.extend(parts)

        target = config.target_url.strip()
        contains_url_in_extra = any(re.match(r"https?://", token, flags=re.IGNORECASE) for token in extra_parts)
        target_optional = config.list_only or config.version_only or bool(config.input_file.strip())

        if not target and not contains_url_in_extra and not target_optional:
            raise ValueError("A target URL is required unless using --list, --version, or --input-file")

        if target:
            command.append(target)

        command.extend(extra_parts)

        return command

    def _terminate_process(self) -> None:
        if self._process is None:
            return
        if self._process.poll() is not None:
            return

        try:
            self._process.terminate()
            self._process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=3)
        except Exception:
            LOGGER.exception("Failed stopping scanner process")

    @staticmethod
    def _resolve_wafw00f_command() -> list[str]:
        is_frozen = getattr(sys, "frozen", False)
        if not is_frozen:
            return [sys.executable, "-m", "wafw00f.main"]

        local_cli = Path(sys.executable).with_name("wafw00f.exe")
        if local_cli.exists():
            return [str(local_cli)]

        discovered = shutil.which("wafw00f") or shutil.which("wafw00f.exe")
        if discovered:
            return [discovered]

        return ["wafw00f"]

    def _run_worker(
        self,
        config: ScanConfig,
        line_callback: Callable[[str], None],
        done_callback: Callable[[ScanResult], None],
    ) -> None:
        started_at = datetime.utcnow().isoformat() + "Z"
        try:
            command = self._build_command(config)
        except Exception as exc:
            result = ScanResult(
                target_url=config.target_url,
                command=[],
                started_at=started_at,
                finished_at=datetime.utcnow().isoformat() + "Z",
                exit_code=None,
                output=str(exc),
                error_message=str(exc),
            )
            done_callback(result)
            return

        lines: list[str] = []
        line_callback(f"[info] Command: {' '.join(command)}")
        LOGGER.info("Starting scan for %s", config.target_url)

        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except Exception as exc:
            result = ScanResult(
                target_url=config.target_url,
                command=command,
                started_at=started_at,
                finished_at=datetime.utcnow().isoformat() + "Z",
                exit_code=None,
                output=str(exc),
                error_message=str(exc),
            )
            done_callback(result)
            return

        try:
            assert self._process.stdout is not None
            for line in self._process.stdout:
                if self._stop_requested.is_set():
                    break
                clean_line = line.rstrip("\n")
                lines.append(clean_line)
                line_callback(clean_line)

            if self._stop_requested.is_set() and self.is_running:
                self._terminate_process()

            exit_code = self._process.wait(timeout=max(config.execution_timeout_seconds, 1))
            stopped = self._stop_requested.is_set()
            error_message = None
            if stopped:
                line_callback("[info] Scan stopped by user")
        except subprocess.TimeoutExpired:
            self._terminate_process()
            timeout_msg = f"Scan timed out after {max(config.execution_timeout_seconds, 1)} seconds"
            lines.append(f"[runner-error] {timeout_msg}")
            line_callback(lines[-1])
            exit_code = None
            stopped = False
            error_message = timeout_msg
        except Exception as exc:
            lines.append(f"[runner-error] {exc}")
            line_callback(lines[-1])
            exit_code = None
            stopped = self._stop_requested.is_set()
            error_message = str(exc)
        finally:
            if self._process and self._process.stdout:
                self._process.stdout.close()
            output = "\n".join(lines)
            wafs, request_count = self._extract_summary(output)
            result = ScanResult(
                target_url=config.target_url,
                command=command,
                started_at=started_at,
                finished_at=datetime.utcnow().isoformat() + "Z",
                exit_code=exit_code,
                output=output,
                stopped=stopped,
                error_message=error_message,
                detected_wafs=wafs,
                request_count=request_count,
            )
            LOGGER.info(
                "Finished scan for %s (exit=%s, stopped=%s)",
                config.target_url,
                result.exit_code,
                result.stopped,
            )
            self._process = None
            done_callback(result)

    @staticmethod
    def _extract_summary(output: str) -> tuple[list[str], int | None]:
        detected_wafs: list[str] = []
        request_count: int | None = None

        for line in output.splitlines():
            if " is behind " in line and " WAF" in line:
                parts = line.split(" is behind ", 1)
                if len(parts) == 2:
                    waf_info = parts[1].replace(" WAF.", "").strip()
                    if waf_info and waf_info not in detected_wafs:
                        detected_wafs.append(waf_info)

            if "Number of requests:" in line:
                raw = line.split("Number of requests:", 1)[1].strip()
                try:
                    request_count = int(raw)
                except ValueError:
                    request_count = None

        return detected_wafs, request_count


class UiEventBridge:
    def __init__(self) -> None:
        self.queue: Queue[tuple[str, object]] = Queue()

    def push_line(self, text: str) -> None:
        self.queue.put(("line", text))

    def push_done(self, result: ScanResult) -> None:
        self.queue.put(("done", result))
