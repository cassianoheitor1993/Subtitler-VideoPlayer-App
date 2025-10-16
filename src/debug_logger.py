"""Centralized debug logger for tracking streaming behaviour and user actions."""

from __future__ import annotations

import json
import threading
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
EVENTS_FILE = LOG_DIR / "streaming_events.jsonl"
STATS_FILE = LOG_DIR / "streaming_stats.json"


@dataclass
class _SessionSummary:
    """Lightweight in-memory summary for the current application session."""

    session_id: str
    started_at: str
    events: int = 0
    video_loads: int = 0
    cast_starts: int = 0
    cast_stops: int = 0
    autoplay_starts: int = 0


class DebugLogger:
    """Append-only event logger with aggregated streaming statistics."""

    def __init__(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._session_id = str(uuid.uuid4())
        self._session_summary = _SessionSummary(
            session_id=self._session_id,
            started_at=self._timestamp(),
        )
        self._stats = self._load_stats()
        with self._lock:
            self._ensure_session_locked()
            self._write_stats_locked()

    # ------------------------------------------------------------------
    # Read APIs
    # ------------------------------------------------------------------
    def get_stats_snapshot(self) -> Dict[str, Any]:
        """Return a deep copy of the aggregated stats for external use."""
        with self._lock:
            return json.loads(json.dumps(self._stats))

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return up to ``limit`` recent events from the JSONL log."""
        limit = max(1, min(int(limit), 500))
        if not EVENTS_FILE.exists():
            return []

        events: List[Dict[str, Any]] = []
        try:
            with EVENTS_FILE.open("r", encoding="utf-8") as handle:
                for line in deque(handle, maxlen=limit):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[DebugLogger] Failed to read recent events: {exc}", flush=True)
            return []

        events.sort(key=lambda entry: entry.get("timestamp", ""))
        return events

    # ------------------------------------------------------------------
    # Public API helpers
    # ------------------------------------------------------------------
    def log_video_loaded(self, video_path: str, *, source: str, loop: bool) -> None:
        """Record that a video file was loaded into the player."""
        payload = {
            "video_path": str(video_path),
            "video_name": Path(video_path).name,
            "source": source,
            "loop": loop,
        }
        self._append_event("video_loaded", payload, self._update_stats_for_video_loaded)

    def log_cast_started(
        self,
        video_path: Optional[str],
        *,
        source: Optional[str],
        url: Optional[str],
        subtitle_path: Optional[str],
        autoplay: bool,
    ) -> None:
        """Record that a streaming session successfully started."""
        payload = {
            "video_path": str(video_path) if video_path else None,
            "video_name": Path(video_path).name if video_path else None,
            "source": source,
            "url": url,
            "subtitle_path": str(subtitle_path) if subtitle_path else None,
            "autoplay": autoplay,
        }
        self._append_event("cast_started", payload, self._update_stats_for_cast_started)

    def log_cast_stopped(
        self,
        video_path: Optional[str],
        *,
        source: Optional[str],
        reason: str,
    ) -> None:
        """Record that a streaming session was stopped."""
        payload = {
            "video_path": str(video_path) if video_path else None,
            "video_name": Path(video_path).name if video_path else None,
            "source": source,
            "reason": reason,
        }
        self._append_event("cast_stopped", payload, self._update_stats_for_cast_stopped)

    def log_cast_failed(
        self,
        video_path: Optional[str],
        *,
        source: Optional[str],
        error: str,
    ) -> None:
        """Record a casting failure for diagnostics."""
        payload = {
            "video_path": str(video_path) if video_path else None,
            "video_name": Path(video_path).name if video_path else None,
            "source": source,
            "error": error,
        }
        self._append_event("cast_failed", payload)

    def log_sample_autoplay_started(self, video_path: str) -> None:
        """Record that the bundled sample started autoplay."""
        payload = {
            "video_path": str(video_path),
            "video_name": Path(video_path).name,
        }
        self._append_event(
            "sample_autoplay_started",
            payload,
            self._update_stats_for_sample_autoplay,
        )

    def log_subtitle_linked(self, video_path: str, subtitle_path: str) -> None:
        """Record which subtitle file was paired with a video."""
        payload = {
            "video_path": str(video_path),
            "video_name": Path(video_path).name,
            "subtitle_path": str(subtitle_path),
            "subtitle_name": Path(subtitle_path).name,
        }
        self._append_event("subtitle_linked", payload)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _append_event(
        self,
        event: str,
        payload: Dict[str, Any],
        update_callback: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]] = None,
    ) -> None:
        """Append a structured event to disk and update aggregate metrics."""
        record = {
            "timestamp": self._timestamp(),
            "session_id": self._session_id,
            "event": event,
            "data": payload,
        }

        try:
            with self._lock:
                self._write_event_locked(record)
                self._refresh_stats_locked(record, update_callback)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[DebugLogger] Failed to persist event '{event}': {exc}", flush=True)

    def _write_event_locked(self, record: Dict[str, Any]) -> None:
        EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with EVENTS_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _refresh_stats_locked(
        self,
        record: Dict[str, Any],
        update_callback: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]],
    ) -> None:
        stats = self._stats
        totals = stats.setdefault("totals", {})
        totals["events"] = totals.get("events", 0) + 1

        session = stats.setdefault("sessions", {}).setdefault(
            self._session_id,
            {
                "session_id": self._session_id,
                "started_at": self._session_summary.started_at,
                "events": 0,
                "video_loads": 0,
                "cast_starts": 0,
                "cast_stops": 0,
                "autoplay_starts": 0,
            },
        )
        session["events"] = session.get("events", 0) + 1
        session["last_event_at"] = record["timestamp"]
        self._session_summary.events += 1

        if update_callback:
            update_callback(stats, record)

        stats["last_event"] = record
        stats["last_updated_at"] = record["timestamp"]
        self._write_stats_locked()

    def _update_stats_for_video_loaded(self, stats: Dict[str, Any], record: Dict[str, Any]) -> None:
        data = record["data"]
        source = data.get("source") or "unknown"
        video_path = data.get("video_path")

        totals = stats.setdefault("totals", {})
        totals["video_loads"] = totals.get("video_loads", 0) + 1

        sources = stats.setdefault("video_sources", {})
        sources[source] = sources.get(source, 0) + 1

        session = stats.setdefault("sessions", {}).setdefault(self._session_id, {})
        session["video_loads"] = session.get("video_loads", 0) + 1

        if video_path:
            video_stats = self._ensure_video_entry(stats, video_path)
            video_stats["loads"] = video_stats.get("loads", 0) + 1
            video_stats["last_loaded_at"] = record["timestamp"]
            video_stats["last_source"] = source
            video_stats["loop_enabled"] = bool(data.get("loop"))

    def _update_stats_for_cast_started(self, stats: Dict[str, Any], record: Dict[str, Any]) -> None:
        data = record["data"]
        source = data.get("source") or "unknown"
        video_path = data.get("video_path")
        autoplay = data.get("autoplay", False)

        totals = stats.setdefault("totals", {})
        totals["cast_starts"] = totals.get("cast_starts", 0) + 1
        if autoplay:
            totals["autoplay_casts"] = totals.get("autoplay_casts", 0) + 1

        session = stats.setdefault("sessions", {}).setdefault(self._session_id, {})
        session["cast_starts"] = session.get("cast_starts", 0) + 1

        if autoplay:
            session["autoplay_starts"] = session.get("autoplay_starts", 0) + 1

        sources = stats.setdefault("cast_sources", {})
        sources[source] = sources.get(source, 0) + 1

        if video_path:
            video_stats = self._ensure_video_entry(stats, video_path)
            video_stats["casts_started"] = video_stats.get("casts_started", 0) + 1
            video_stats["last_cast_started_at"] = record["timestamp"]
            video_stats["last_cast_url"] = data.get("url")
            video_stats["last_cast_source"] = source
            video_stats["subtitle_on_cast"] = bool(data.get("subtitle_path"))

    def _update_stats_for_cast_stopped(self, stats: Dict[str, Any], record: Dict[str, Any]) -> None:
        data = record["data"]
        video_path = data.get("video_path")

        totals = stats.setdefault("totals", {})
        totals["cast_stops"] = totals.get("cast_stops", 0) + 1

        session = stats.setdefault("sessions", {}).setdefault(self._session_id, {})
        session["cast_stops"] = session.get("cast_stops", 0) + 1

        if video_path:
            video_stats = self._ensure_video_entry(stats, video_path)
            video_stats["casts_stopped"] = video_stats.get("casts_stopped", 0) + 1
            video_stats["last_cast_stopped_at"] = record["timestamp"]
            video_stats["last_stop_reason"] = data.get("reason")

    def _update_stats_for_sample_autoplay(self, stats: Dict[str, Any], record: Dict[str, Any]) -> None:
        totals = stats.setdefault("totals", {})
        totals["sample_autoplay_starts"] = totals.get("sample_autoplay_starts", 0) + 1

        session = stats.setdefault("sessions", {}).setdefault(self._session_id, {})
        session["autoplay_starts"] = session.get("autoplay_starts", 0) + 1

    def _ensure_video_entry(self, stats: Dict[str, Any], video_path: str) -> Dict[str, Any]:
        videos = stats.setdefault("videos", {})
        entry = videos.get(video_path)
        if entry is None:
            entry = {
                "video_path": video_path,
                "video_name": Path(video_path).name,
                "loads": 0,
                "casts_started": 0,
                "casts_stopped": 0,
            }
            videos[video_path] = entry
        return entry

    def _ensure_session_locked(self) -> None:
        stats = self._stats
        sessions = stats.setdefault("sessions", {})
        if self._session_id not in sessions:
            sessions[self._session_id] = {
                "session_id": self._session_id,
                "started_at": self._session_summary.started_at,
                "events": 0,
                "video_loads": 0,
                "cast_starts": 0,
                "cast_stops": 0,
                "autoplay_starts": 0,
            }
            order = stats.setdefault("session_order", [])
            order.append(self._session_id)
            stats["last_session_started_at"] = self._session_summary.started_at

        stats.setdefault("totals", {})
        stats.setdefault("videos", {})
        stats.setdefault("video_sources", {})
        stats.setdefault("cast_sources", {})

    def _load_stats(self) -> Dict[str, Any]:
        if not STATS_FILE.exists():
            return {
                "totals": {},
                "videos": {},
                "video_sources": {},
                "cast_sources": {},
                "sessions": {},
                "session_order": [],
            }
        try:
            data = json.loads(STATS_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Stats file is not a JSON object")
            return data
        except Exception:  # pylint: disable=broad-except
            backup_path = STATS_FILE.with_suffix(".corrupt.json")
            STATS_FILE.replace(backup_path)
            print(
                f"[DebugLogger] Warning: corrupted stats file moved to {backup_path}",
                flush=True,
            )
            return {
                "totals": {},
                "videos": {},
                "video_sources": {},
                "cast_sources": {},
                "sessions": {},
                "session_order": [],
            }

    def _write_stats_locked(self) -> None:
        STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATS_FILE.write_text(
            json.dumps(self._stats, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()


debug_logger = DebugLogger()

__all__ = ["debug_logger", "DebugLogger"]
