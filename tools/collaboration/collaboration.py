#!/usr/bin/env python3
"""Bridge with read-only Discord and controlled Trello access."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


JsonTransport = Callable[..., Any]
Sleep = Callable[[float], None]
DEFAULT_RETRY_DELAY_SECONDS = 1.0
MIN_RETRY_DELAY_SECONDS = 0.05
MAX_RETRY_DELAY_SECONDS = 60.0


class CollaborationError(RuntimeError):
    """Expected configuration or remote API failure."""


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _retry_after_seconds(error: HTTPError, detail: str) -> float:
    candidates: list[Any] = []
    try:
        payload = json.loads(detail)
        if isinstance(payload, dict):
            candidates.append(payload.get("retry_after"))
    except json.JSONDecodeError:
        pass

    if error.headers is not None:
        candidates.append(error.headers.get("Retry-After"))

    for candidate in candidates:
        try:
            delay = float(candidate)
        except (TypeError, ValueError):
            continue
        if delay < 0:
            continue
        return min(MAX_RETRY_DELAY_SECONDS, max(MIN_RETRY_DELAY_SECONDS, delay))

    return DEFAULT_RETRY_DELAY_SECONDS


def _request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    form_body: dict[str, Any] | None = None,
    timeout: int = 30,
    max_retries: int = 4,
    sleep: Sleep = time.sleep,
) -> Any:
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")

    request_headers = {"Accept": "application/json", **(headers or {})}
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    elif form_body is not None:
        data = urlencode(
            {key: value for key, value in form_body.items() if value is not None}
        ).encode("utf-8")
        request_headers["Content-Type"] = "application/x-www-form-urlencoded"

    for attempt in range(max_retries + 1):
        request = Request(url, data=data, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code == 429 and attempt < max_retries:
                sleep(_retry_after_seconds(exc, detail))
                continue
            raise CollaborationError(
                f"Remote API returned HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise CollaborationError(
                f"Remote API is unavailable: {exc.reason}"
            ) from exc

        if not payload:
            return None
        return json.loads(payload.decode("utf-8"))

    raise AssertionError("unreachable retry loop")


@dataclass(frozen=True)
class Settings:
    discord_bot_token: str
    discord_guild_id: str
    discord_channel_id: str
    trello_api_key: str
    trello_api_token: str
    trello_board_id: str
    allow_trello_writes: bool
    snapshot_dir: Path
    max_discord_pages: int

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN", "").strip(),
            discord_guild_id=os.getenv("DISCORD_GUILD_ID", "").strip(),
            discord_channel_id=os.getenv("DISCORD_CHANNEL_ID", "").strip(),
            trello_api_key=os.getenv("TRELLO_API_KEY", "").strip(),
            trello_api_token=os.getenv("TRELLO_API_TOKEN", "").strip(),
            trello_board_id=os.getenv("TRELLO_BOARD_ID", "").strip(),
            allow_trello_writes=_env_bool(
                "TRELLO_ALLOW_WRITES",
                default=_env_bool("COLLAB_ALLOW_WRITES"),
            ),
            snapshot_dir=Path(
                os.getenv("COLLAB_SNAPSHOT_DIR", "./data/snapshots")
            ),
            max_discord_pages=int(os.getenv("COLLAB_MAX_DISCORD_PAGES", "10")),
        )
        missing = [
            name
            for name, value in {
                "DISCORD_BOT_TOKEN": settings.discord_bot_token,
                "DISCORD_GUILD_ID": settings.discord_guild_id,
                "DISCORD_CHANNEL_ID": settings.discord_channel_id,
                "TRELLO_API_KEY": settings.trello_api_key,
                "TRELLO_API_TOKEN": settings.trello_api_token,
                "TRELLO_BOARD_ID": settings.trello_board_id,
            }.items()
            if not value
        ]
        if missing:
            raise CollaborationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        if settings.max_discord_pages < 1:
            raise CollaborationError("COLLAB_MAX_DISCORD_PAGES must be at least 1")
        return settings


def require_write(settings: Settings, confirmed: bool) -> None:
    if not settings.allow_trello_writes:
        raise CollaborationError(
            "Trello writes are disabled. Set TRELLO_ALLOW_WRITES=true on the server."
        )
    if not confirmed:
        raise CollaborationError(
            "Write not confirmed. Re-run the command with --confirm-write."
        )


class DiscordClient:
    api_base = "https://discord.com/api/v10"

    def __init__(
        self, settings: Settings, transport: JsonTransport = _request_json
    ) -> None:
        self.settings = settings
        self.transport = transport

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bot {self.settings.discord_bot_token}",
            "User-Agent": (
                "Economicon-Collaboration/1.0 "
                "(+https://github.com/EconomiconFinOps/tfm-economicon)"
            ),
        }

    def get_channel(self) -> dict[str, Any]:
        return self.transport(
            "GET",
            f"{self.api_base}/channels/{self.settings.discord_channel_id}",
            headers=self._headers,
        )

    def list_messages(self) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        before: str | None = None
        for _ in range(self.settings.max_discord_pages):
            query: dict[str, Any] = {"limit": 100}
            if before:
                query["before"] = before
            page = self.transport(
                "GET",
                (
                    f"{self.api_base}/channels/"
                    f"{self.settings.discord_channel_id}/messages?{urlencode(query)}"
                ),
                headers=self._headers,
            )
            if not page:
                break
            messages.extend(page)
            if len(page) < 100:
                break
            before = page[-1]["id"]
        return sorted(messages, key=lambda message: message.get("timestamp", ""))

class TrelloClient:
    api_base = "https://api.trello.com/1"

    def __init__(
        self, settings: Settings, transport: JsonTransport = _request_json
    ) -> None:
        self.settings = settings
        self.transport = transport

    def _url(self, path: str, **params: Any) -> str:
        auth = {
            "key": self.settings.trello_api_key,
            "token": self.settings.trello_api_token,
        }
        return f"{self.api_base}{path}?{urlencode({**params, **auth})}"

    def get_board(self) -> dict[str, Any]:
        return self.transport(
            "GET",
            self._url(
                f"/boards/{self.settings.trello_board_id}",
                fields="name,url,dateLastActivity,closed",
            ),
        )

    def get_lists(self) -> list[dict[str, Any]]:
        return self.transport(
            "GET",
            self._url(
                f"/boards/{self.settings.trello_board_id}/lists",
                filter="open",
                fields="name,pos,closed",
            ),
        )

    def get_cards(self) -> list[dict[str, Any]]:
        return self.transport(
            "GET",
            self._url(
                f"/boards/{self.settings.trello_board_id}/cards",
                filter="open",
                fields=(
                    "name,desc,idList,idMembers,labels,due,dueComplete,"
                    "shortUrl,dateLastActivity"
                ),
            ),
        )

    def get_actions(self) -> list[dict[str, Any]]:
        return self.transport(
            "GET",
            self._url(
                f"/boards/{self.settings.trello_board_id}/actions",
                filter="commentCard,createCard,updateCard",
                limit=100,
                fields="type,date,data,idMemberCreator",
            ),
        )

    def create_card(
        self, list_id: str, name: str, description: str = ""
    ) -> dict[str, Any]:
        return self.transport(
            "POST",
            self._url("/cards"),
            form_body={"idList": list_id, "name": name, "desc": description},
        )

    def comment(self, card_id: str, text: str) -> dict[str, Any]:
        return self.transport(
            "POST",
            self._url(f"/cards/{card_id}/actions/comments"),
            form_body={"text": text},
        )

    def move_card(self, card_id: str, list_id: str) -> dict[str, Any]:
        return self.transport(
            "PUT",
            self._url(f"/cards/{card_id}"),
            form_body={"idList": list_id},
        )

    def update_card(
        self,
        card_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        due: str | None = None,
    ) -> dict[str, Any]:
        fields = {"name": name, "desc": description, "due": due}
        if all(value is None for value in fields.values()):
            raise CollaborationError("At least one card field must be supplied")
        return self.transport(
            "PUT",
            self._url(f"/cards/{card_id}"),
            form_body=fields,
        )


def build_snapshot(
    discord: DiscordClient, trello: TrelloClient
) -> dict[str, Any]:
    return {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "discord": {
            "guild_id": discord.settings.discord_guild_id,
            "channel": discord.get_channel(),
            "messages": discord.list_messages(),
        },
        "trello": {
            "board": trello.get_board(),
            "lists": trello.get_lists(),
            "cards": trello.get_cards(),
            "actions": trello.get_actions(),
        },
    }


def snapshot_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Economicon collaboration snapshot",
        "",
        f"Synced at: {snapshot['synced_at']}",
        "",
        "## Discord",
        "",
    ]
    for message in snapshot["discord"]["messages"]:
        author = message.get("author", {}).get("username", "unknown")
        timestamp = message.get("timestamp", "")
        content = (message.get("content") or "").replace("\r", " ").replace(
            "\n", " "
        )
        lines.append(f"- `{timestamp}` **{author}:** {content}")

    lines.extend(["", "## Trello", ""])
    lists_by_id = {
        item["id"]: item.get("name", item["id"])
        for item in snapshot["trello"]["lists"]
    }
    for card in snapshot["trello"]["cards"]:
        list_name = lists_by_id.get(card.get("idList"), "unknown")
        due = f" - due {card['due']}" if card.get("due") else ""
        lines.append(
            f"- **[{list_name}]** {card.get('name', 'Untitled')}"
            f"{due} ({card.get('shortUrl', '')})"
        )
    lines.append("")
    return "\n".join(lines)


def write_snapshot(
    snapshot: dict[str, Any], output_dir: Path
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"snapshot-{stamp}.json"
    markdown_path = output_dir / f"snapshot-{stamp}.md"
    json_payload = json.dumps(snapshot, ensure_ascii=False, indent=2)
    markdown_payload = snapshot_markdown(snapshot)
    json_path.write_text(json_payload, encoding="utf-8")
    markdown_path.write_text(markdown_payload, encoding="utf-8")
    (output_dir / "latest.json").write_text(json_payload, encoding="utf-8")
    (output_dir / "latest.md").write_text(markdown_payload, encoding="utf-8")
    return json_path, markdown_path


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check", help="Validate read access")
    subparsers.add_parser("sync", help="Create JSON and Markdown snapshots")

    trello_create = subparsers.add_parser("trello-create", help="Create a card")
    trello_create.add_argument("--list-id", required=True)
    trello_create.add_argument("--name", required=True)
    trello_create.add_argument("--description", default="")
    trello_create.add_argument("--confirm-write", action="store_true")

    trello_comment = subparsers.add_parser(
        "trello-comment", help="Comment on a card"
    )
    trello_comment.add_argument("--card-id", required=True)
    trello_comment.add_argument("--text", required=True)
    trello_comment.add_argument("--confirm-write", action="store_true")

    trello_move = subparsers.add_parser("trello-move", help="Move a card")
    trello_move.add_argument("--card-id", required=True)
    trello_move.add_argument("--list-id", required=True)
    trello_move.add_argument("--confirm-write", action="store_true")

    trello_update = subparsers.add_parser("trello-update", help="Update a card")
    trello_update.add_argument("--card-id", required=True)
    trello_update.add_argument("--name")
    trello_update.add_argument("--description")
    trello_update.add_argument("--due")
    trello_update.add_argument("--confirm-write", action="store_true")
    return root


def run(args: argparse.Namespace, settings: Settings) -> Any:
    discord = DiscordClient(settings)
    trello = TrelloClient(settings)

    if args.command == "check":
        return {"discord": discord.get_channel(), "trello": trello.get_board()}
    if args.command == "sync":
        paths = write_snapshot(
            build_snapshot(discord, trello), settings.snapshot_dir
        )
        return {"json": str(paths[0]), "markdown": str(paths[1])}

    require_write(settings, args.confirm_write)
    if args.command == "trello-create":
        return trello.create_card(args.list_id, args.name, args.description)
    if args.command == "trello-comment":
        return trello.comment(args.card_id, args.text)
    if args.command == "trello-move":
        return trello.move_card(args.card_id, args.list_id)
    if args.command == "trello-update":
        return trello.update_card(
            args.card_id,
            name=args.name,
            description=args.description,
            due=args.due,
        )
    raise CollaborationError(f"Unsupported command: {args.command}")


def main() -> int:
    try:
        args = parser().parse_args()
        result = run(args, Settings.from_env())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (CollaborationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
