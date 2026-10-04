import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auth import User, UserRole
from controllers import minecraft as minecraft_controller
from services.players import (
    PlayerIdentityConflict,
    add_allowlist_player,
    load_allowlist,
    parse_recent_players,
    read_recent_players,
)


class ParseRecentPlayersTests(unittest.TestCase):
    def test_returns_unique_players_in_most_recent_join_order(self):
        logs = "\n".join(
            [
                "[INFO] Player connected: Alex, xuid: 1234567890123456",
                "[INFO] Player connected: Steve, xuid: 2535433945963160",
                "[INFO] Player connected: AlexNewName, xuid: 1234567890123456",
                "[INFO] Player disconnected: Steve",
                "[INFO] Player connected: invalid, xuid: not-a-number",
            ]
        )

        self.assertEqual(
            parse_recent_players(logs),
            [
                {"name": "AlexNewName", "xuid": "1234567890123456"},
                {"name": "Steve", "xuid": "2535433945963160"},
            ],
        )

    def test_returns_empty_list_when_no_player_connection_lines_exist(self):
        self.assertEqual(parse_recent_players("server started\nserver stopped"), [])

    def test_reads_only_the_bounded_minecraft_journal(self):
        process_result = type(
            "CompletedProcess",
            (),
            {
                "stdout": "[INFO] Player connected: Alex, xuid: 1234567890123456",
            },
        )()
        with patch("services.players.subprocess.run", return_value=process_result) as run:
            players = read_recent_players()

        self.assertEqual(players[0]["name"], "Alex")
        command = run.call_args.args[0]
        self.assertEqual(command[0:4], ["sudo", "journalctl", "-u", "minecraft-bedrock"])
        self.assertIn("2000", command)
        run.assert_called_once()


class LoadAllowlistTests(unittest.TestCase):
    def test_loads_xuid_and_legacy_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowlist.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Alex",
                            "xuid": "1234567890123456",
                            "ignoresPlayerLimit": False,
                        },
                        {"name": "LegacyPlayer", "ignoresPlayerLimit": False},
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                load_allowlist(path),
                [
                    {
                        "name": "Alex",
                        "xuid": "1234567890123456",
                        "ignoresPlayerLimit": False,
                    },
                    {
                        "name": "LegacyPlayer",
                        "xuid": None,
                        "ignoresPlayerLimit": False,
                    },
                ],
            )

    def test_rejects_invalid_json_instead_of_returning_empty_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowlist.json"
            path.write_text("{invalid", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_allowlist(path)

    def test_adds_player_with_bedrock_allowlist_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowlist.json"

            self.assertEqual(
                add_allowlist_player(path, "Alex", "1234567890123456"),
                "added",
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                [
                    {
                        "ignoresPlayerLimit": False,
                        "name": "Alex",
                        "xuid": "1234567890123456",
                    }
                ],
            )

    def test_fills_xuid_for_existing_legacy_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowlist.json"
            path.write_text(
                json.dumps([{"name": "Alex", "ignoresPlayerLimit": False}]),
                encoding="utf-8",
            )

            self.assertEqual(
                add_allowlist_player(path, "Alex", "1234567890123456"),
                "updated",
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))[0]["xuid"],
                "1234567890123456",
            )

    def test_rejects_gamertag_linked_to_different_xuid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowlist.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Alex",
                            "xuid": "1234567890123456",
                            "ignoresPlayerLimit": False,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaises(PlayerIdentityConflict):
                add_allowlist_player(path, "Alex", "2535433945963160")


class MinecraftPlayerEndpointTests(unittest.TestCase):
    def setUp(self):
        self.user = User(
            username="friend",
            role=UserRole.MODERATOR,
            description="Test user",
        )

    def test_recent_players_endpoint_returns_name_and_xuid(self):
        with patch.object(
            minecraft_controller,
            "read_recent_players",
            return_value=[{"name": "Alex", "xuid": "1234567890123456"}],
        ):
            response = minecraft_controller.get_recent_players(50, self.user)

        self.assertEqual(
            response,
            {
                "players": [{"name": "Alex", "xuid": "1234567890123456"}],
                "count": 1,
            },
        )

    def test_add_endpoint_persists_xuid_and_restarts_server(self):
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch.object(minecraft_controller, "MINECRAFT_DIR", Path(directory)),
                patch.object(minecraft_controller, "safe_systemctl") as systemctl,
            ):
                response = minecraft_controller.add_to_allowlist(
                    minecraft_controller.AllowlistPlayerModel(
                        gamertag="Alex",
                        xuid="1234567890123456",
                    ),
                    self.user,
                )
                saved_entries = json.loads(
                    (Path(directory) / "allowlist.json").read_text(encoding="utf-8")
                )

        self.assertEqual(saved_entries[0]["name"], "Alex")
        self.assertEqual(saved_entries[0]["xuid"], "1234567890123456")
        self.assertEqual(response["status"], "success")
        systemctl.assert_called_once_with("restart", "minecraft-bedrock")


if __name__ == "__main__":
    unittest.main()
