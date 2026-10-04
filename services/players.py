import json
import re
import subprocess
from pathlib import Path
from typing import Any


PLAYER_CONNECTED_PATTERN = re.compile(
    r"Player connected:\s*(?P<name>.+?),\s*xuid:\s*(?P<xuid>\d+)",
    re.IGNORECASE,
)
MAX_JOURNAL_LINES = 2000


class PlayerIdentityConflict(ValueError):
    """Raised when a gamertag is already linked to a different XUID."""


def parse_recent_players(log_output: str, limit: int = 50) -> list[dict[str, str]]:
    """Extract unique player identities, newest connection first."""
    latest_by_xuid: dict[str, dict[str, str]] = {}
    for line in reversed(log_output.splitlines()):
        match = PLAYER_CONNECTED_PATTERN.search(line)
        if not match:
            continue
        name = match.group("name").strip()
        xuid = match.group("xuid")
        if name and xuid not in latest_by_xuid:
            latest_by_xuid[xuid] = {"name": name, "xuid": xuid}
            if len(latest_by_xuid) >= limit:
                break
    return list(latest_by_xuid.values())


def read_recent_players(limit: int = 50) -> list[dict[str, str]]:
    """Read recent Minecraft service logs and extract connected player identities."""
    result = subprocess.run(
        [
            "sudo",
            "journalctl",
            "-u",
            "minecraft-bedrock",
            "--no-pager",
            "-n",
            str(MAX_JOURNAL_LINES),
            "-o",
            "cat",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return parse_recent_players(result.stdout, limit)


def load_allowlist(path: Path) -> list[dict[str, Any]]:
    """Read BDS allowlist entries and normalize legacy entries without XUIDs."""
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []

    if not isinstance(data, list):
        raise ValueError("allowlist.json deve conter uma lista de jogadores.")

    entries = []
    for entry in data:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("name"), str)
            or not entry["name"].strip()
            or (
                entry.get("xuid") is not None
                and not isinstance(entry.get("xuid"), str)
            )
        ):
            raise ValueError("allowlist.json contém uma entrada inválida.")
        normalized = dict(entry)
        normalized.setdefault("ignoresPlayerLimit", False)
        normalized.setdefault("xuid", None)
        entries.append(normalized)
    return entries


def add_allowlist_player(path: Path, name: str, xuid: str) -> str:
    """Add or update a player, returning added, updated, or existing."""
    entries = load_allowlist(path)
    for entry in entries:
        if entry["xuid"] == xuid:
            if entry["name"] == name:
                return "existing"
            entry["name"] = name
            result = "updated"
            break
        if entry["name"].casefold() == name.casefold():
            if entry["xuid"] is not None and entry["xuid"] != xuid:
                raise PlayerIdentityConflict(
                    "Esse gamertag já está associado a outro XUID."
                )
            entry["xuid"] = xuid
            result = "updated"
            break
    else:
        entries.append(
            {
                "ignoresPlayerLimit": False,
                "name": name,
                "xuid": xuid,
            }
        )
        result = "added"

    with path.open("w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2)
        file.write("\n")
    return result
