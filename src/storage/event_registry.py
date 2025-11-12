import asyncio
import json
import shutil
import time
from pathlib import Path
from typing import Any, Optional

import redis.asyncio as redis

from src.settings import EVENT_TTL_SECONDS, REDIS_URL, TEMP_STORAGE_ROOT


EVENT_KEY_PREFIX = "actual_ids_mail_server"


def _sanitize_segment(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)


class EventRegistry:
    def __init__(self) -> None:
        self._redis = redis.from_url(REDIS_URL, decode_responses=True)
        self._base_dir = TEMP_STORAGE_ROOT
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, rule_name: str) -> str:
        return f"{EVENT_KEY_PREFIX}:{rule_name}"

    def _rule_dir(self, rule_name: str) -> Path:
        safe_rule = _sanitize_segment(rule_name)
        return self._base_dir / safe_rule

    async def start_event(
        self,
        rule_name: str,
        event_id: str,
        permanent_file: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        await self.cleanup_expired()
        rule_dir = self._rule_dir(rule_name)
        event_dir = rule_dir / _sanitize_segment(event_id)
        event_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "rule_name": rule_name,
            "event_id": event_id,
            "started_at": int(time.time()),
            "permanent_file": bool(permanent_file),
            "path": str(event_dir),
            "files": [],
        }
        if metadata:
            payload.update(metadata)

        await self._redis.set(self._key(rule_name), json.dumps(payload))
        await self._redis.expire(self._key(rule_name), EVENT_TTL_SECONDS)
        return payload

    async def get_event(self, rule_name: str) -> Optional[dict[str, Any]]:
        raw = await self._redis.get(self._key(rule_name))
        if not raw:
            return None
        return json.loads(raw)

    async def store_attachments(
        self,
        rule_name: str,
        event_id: str,
        attachments: list[tuple[str, bytes]],
    ) -> list[str]:
        if not attachments:
            return []
        meta = await self.get_event(rule_name)
        if not meta or meta.get("event_id") != event_id:
            return []

        event_dir = Path(meta["path"])

        def _write_files() -> list[str]:
            saved_paths: list[str] = []
            for filename, payload in attachments:
                safe_name = _sanitize_segment(filename) or "attachment"
                target = event_dir / safe_name
                with open(target, "wb") as fh:
                    fh.write(payload)
                saved_paths.append(str(target))
            return saved_paths

        saved = await asyncio.to_thread(_write_files)
        meta.setdefault("files", [])
        meta["files"].extend(saved)
        await self._redis.set(self._key(rule_name), json.dumps(meta))
        await self._redis.expire(self._key(rule_name), EVENT_TTL_SECONDS)
        return saved

    async def finish_event(
        self, rule_name: str, event_id: str, permanent_file: bool = False
    ) -> None:
        meta = await self.get_event(rule_name)
        if not meta or meta.get("event_id") != event_id:
            return
        if permanent_file:
            await self._redis.expire(self._key(rule_name), EVENT_TTL_SECONDS)
            return
        await self._cleanup_event(rule_name, meta)

    async def cleanup_expired(self) -> None:
        keys = await self._redis.keys(f"{EVENT_KEY_PREFIX}:*")
        now = int(time.time())
        for key in keys:
            raw = await self._redis.get(key)
            if not raw:
                continue
            meta = json.loads(raw)
            started = meta.get("started_at")
            if started is None:
                continue
            if now - int(started) >= EVENT_TTL_SECONDS:
                rule_name = meta.get("rule_name") or key.removeprefix(
                    f"{EVENT_KEY_PREFIX}:"
                )
                await self._cleanup_event(rule_name, meta)

    async def _cleanup_event(self, rule_name: str, meta: dict[str, Any]) -> None:
        await self._redis.delete(self._key(rule_name))
        path_str = meta.get("path")
        if not path_str:
            return
        event_dir = Path(path_str)

        def _remove() -> None:
            if event_dir.exists():
                shutil.rmtree(event_dir, ignore_errors=True)

        await asyncio.to_thread(_remove)


event_registry = EventRegistry()

__all__ = ["event_registry"]
