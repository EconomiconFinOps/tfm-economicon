import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError


TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from collaboration import (  # noqa: E402
    CollaborationError,
    DiscordClient,
    Settings,
    TrelloClient,
    _request_json,
    require_write,
    snapshot_markdown,
    write_snapshot,
)


def settings(*, allow_writes=False, snapshot_dir=Path("snapshots")):
    return Settings(
        discord_bot_token="discord-secret",
        discord_guild_id="guild-1",
        discord_channel_id="channel-1",
        trello_api_key="trello-key",
        trello_api_token="trello-secret",
        trello_board_id="board-1",
        allow_writes=allow_writes,
        snapshot_dir=snapshot_dir,
        max_discord_pages=2,
    )


class Recorder:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def rate_limit_error(body, retry_after_header=None):
    headers = {}
    if retry_after_header is not None:
        headers["Retry-After"] = retry_after_header
    return HTTPError(
        url="https://discord.test/messages",
        code=429,
        msg="Too Many Requests",
        hdrs=headers,
        fp=io.BytesIO(json.dumps(body).encode("utf-8")),
    )


class CollaborationTests(unittest.TestCase):
    def test_writes_need_server_switch_and_command_confirmation(self):
        with self.assertRaises(CollaborationError):
            require_write(settings(allow_writes=False), confirmed=True)
        with self.assertRaises(CollaborationError):
            require_write(settings(allow_writes=True), confirmed=False)
        require_write(settings(allow_writes=True), confirmed=True)

    def test_discord_post_disables_mentions(self):
        recorder = Recorder([{"id": "message-1"}])
        client = DiscordClient(settings(allow_writes=True), recorder)

        result = client.post_message("Project update")

        self.assertEqual(result["id"], "message-1")
        method, url, kwargs = recorder.calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/channels/channel-1/messages"))
        self.assertEqual(kwargs["json_body"]["allowed_mentions"], {"parse": []})
        self.assertIn("EconomiconFinOps", kwargs["headers"]["User-Agent"])

    def test_trello_has_non_destructive_write_operations(self):
        recorder = Recorder(
            [{"id": "card-1"}, {"id": "comment-1"}, {"id": "card-1"}]
        )
        client = TrelloClient(settings(allow_writes=True), recorder)

        client.create_card("list-1", "Build fake API", "Azure fixture")
        client.comment("card-1", "Ready for review")
        client.move_card("card-1", "list-2")

        self.assertEqual([call[0] for call in recorder.calls], ["POST", "POST", "PUT"])
        self.assertFalse(any("DELETE" == call[0] for call in recorder.calls))

    def test_discord_pagination_uses_before_cursor_and_orders_messages(self):
        first_page = [
            {
                "id": str(index),
                "timestamp": (
                    f"2026-08-27T{index // 60:02d}:{index % 60:02d}:00Z"
                ),
            }
            for index in range(100, 0, -1)
        ]
        second_page = [{"id": "0", "timestamp": "2026-08-26T23:59:00Z"}]
        recorder = Recorder([first_page, second_page])

        messages = DiscordClient(settings(), recorder).list_messages()

        self.assertEqual(messages[0]["id"], "0")
        self.assertEqual(messages[-1]["id"], "100")
        self.assertNotIn("before=", recorder.calls[0][1])
        self.assertIn("before=1", recorder.calls[1][1])

    def test_http_429_retries_using_discord_json_delay(self):
        error = rate_limit_error({"message": "limited", "retry_after": 0.25})
        delays = []
        with patch(
            "collaboration.urlopen",
            side_effect=[error, FakeResponse({"ok": True})],
        ) as mocked_urlopen:
            result = _request_json(
                "GET",
                "https://discord.test/messages",
                max_retries=1,
                sleep=delays.append,
            )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(delays, [0.25])
        self.assertEqual(mocked_urlopen.call_count, 2)

    def test_http_429_uses_retry_after_header_as_fallback(self):
        error = rate_limit_error({"message": "limited"}, "0.4")
        delays = []
        with patch(
            "collaboration.urlopen",
            side_effect=[error, FakeResponse({"ok": True})],
        ):
            _request_json(
                "GET",
                "https://discord.test/messages",
                max_retries=1,
                sleep=delays.append,
            )

        self.assertEqual(delays, [0.4])

    def test_http_429_stops_after_bounded_retries(self):
        errors = [
            rate_limit_error({"retry_after": 0}),
            rate_limit_error({"retry_after": 0}),
        ]
        with patch("collaboration.urlopen", side_effect=errors):
            with self.assertRaisesRegex(CollaborationError, "HTTP 429"):
                _request_json(
                    "GET",
                    "https://discord.test/messages",
                    max_retries=1,
                    sleep=lambda _delay: None,
                )

    def test_snapshot_is_written_as_json_and_markdown(self):
        snapshot = {
            "synced_at": "2026-08-08T12:00:00+00:00",
            "discord": {
                "messages": [
                    {
                        "timestamp": "2026-08-08T11:00:00+00:00",
                        "author": {"username": "Lucia"},
                        "content": "Decision accepted",
                    }
                ]
            },
            "trello": {
                "lists": [{"id": "todo", "name": "To do"}],
                "cards": [
                    {
                        "idList": "todo",
                        "name": "Fake API",
                        "shortUrl": "https://t/card",
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as temporary:
            json_path, markdown_path = write_snapshot(snapshot, Path(temporary))
            self.assertEqual(
                json.loads(json_path.read_text(encoding="utf-8")), snapshot
            )
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("**Lucia:** Decision accepted", markdown)
            self.assertIn("**[To do]** Fake API", markdown)
            self.assertTrue((Path(temporary) / "latest.json").exists())
            self.assertTrue((Path(temporary) / "latest.md").exists())

    def test_settings_never_accept_missing_secrets(self):
        original = dict(os.environ)
        try:
            for name in (
                "DISCORD_BOT_TOKEN",
                "DISCORD_GUILD_ID",
                "DISCORD_CHANNEL_ID",
                "TRELLO_API_KEY",
                "TRELLO_API_TOKEN",
                "TRELLO_BOARD_ID",
            ):
                os.environ.pop(name, None)
            with self.assertRaises(CollaborationError):
                Settings.from_env()
        finally:
            os.environ.clear()
            os.environ.update(original)


if __name__ == "__main__":
    unittest.main()
