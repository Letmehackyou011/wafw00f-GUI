from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import json
import re
from urllib.request import urlopen


@dataclass
class UpdateInfo:
    gui_current: str
    gui_latest: str | None
    wafw00f_current: str | None
    wafw00f_latest: str | None
    notes: list[str]


def _parse_version_tuple(value: str) -> tuple[int, ...]:
    numbers = [int(x) for x in re.findall(r"\d+", value)]
    return tuple(numbers) if numbers else (0,)


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version_tuple(latest) > _parse_version_tuple(current)


def _fetch_json(url: str, timeout: int = 8) -> dict[str, object]:
    with urlopen(url, timeout=timeout) as response:
        data = response.read().decode("utf-8", errors="replace")
    return json.loads(data)


def _installed_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def check_updates(gui_current_version: str) -> UpdateInfo:
    notes: list[str] = []

    wafw00f_current = _installed_version("wafw00f")
    wafw00f_latest: str | None = None
    gui_latest: str | None = None

    try:
        pypi = _fetch_json("https://pypi.org/pypi/wafw00f/json")
        wafw00f_latest = str(pypi.get("info", {}).get("version", "")) or None
    except Exception as exc:
        notes.append(f"Could not check wafw00f updates: {exc}")

    try:
        release = _fetch_json("https://api.github.com/repos/Letmehackyou011/wafw00f-GUI/releases/latest")
        gui_latest = str(release.get("tag_name", "")).lstrip("v") or None
    except Exception as exc:
        notes.append(f"Could not check GUI updates: {exc}")

    return UpdateInfo(
        gui_current=gui_current_version,
        gui_latest=gui_latest,
        wafw00f_current=wafw00f_current,
        wafw00f_latest=wafw00f_latest,
        notes=notes,
    )


def format_update_message(info: UpdateInfo) -> str:
    lines = ["Update Check Results", ""]

    lines.append(f"GUI current version: {info.gui_current}")
    if info.gui_latest:
        lines.append(f"GUI latest version: {info.gui_latest}")
        if _is_newer(info.gui_latest, info.gui_current):
            lines.append("GUI update available: yes")
        else:
            lines.append("GUI update available: no")
    else:
        lines.append("GUI latest version: unavailable")

    lines.append("")
    lines.append(f"wafw00f current version: {info.wafw00f_current or 'not installed'}")
    lines.append(f"wafw00f latest version: {info.wafw00f_latest or 'unavailable'}")

    if info.wafw00f_current and info.wafw00f_latest:
        if _is_newer(info.wafw00f_latest, info.wafw00f_current):
            lines.append("wafw00f update available: yes")
        else:
            lines.append("wafw00f update available: no")

    if info.notes:
        lines.append("")
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in info.notes)

    return "\n".join(lines)
