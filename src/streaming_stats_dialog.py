"""Dialog window for visualizing streaming analytics captured by the debug logger."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from debug_logger import debug_logger, EVENTS_FILE, LOG_DIR, STATS_FILE


class StreamingStatsDialog(QDialog):
    """Modal dialog exposing streaming usage analytics to the user."""

    MAX_EVENTS = 50
    MAX_VIDEOS = 15

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Streaming Analytics Dashboard")
        self.setModal(True)
        self.resize(900, 620)

        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        # Summary group -------------------------------------------------
        summary_group = QGroupBox("Aggregated Totals")
        summary_layout = QVBoxLayout()
        summary_group.setLayout(summary_layout)

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        summary_layout.addWidget(self.summary_label)

        main_layout.addWidget(summary_group)

        # Top videos table ----------------------------------------------
        videos_group = QGroupBox("Most Active Videos")
        videos_layout = QVBoxLayout()
        videos_group.setLayout(videos_layout)

        self.videos_table = QTableWidget(0, 6)
        self.videos_table.setHorizontalHeaderLabels(
            [
                "Video",
                "Loads",
                "Cast Starts",
                "Cast Stops",
                "Last Cast",
                "Last Stop Reason",
            ]
        )
        header = self.videos_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(160)
        self.videos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.videos_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.videos_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        videos_layout.addWidget(self.videos_table)

        main_layout.addWidget(videos_group)

        # Recent events table ------------------------------------------
        events_group = QGroupBox("Recent Events")
        events_layout = QVBoxLayout()
        events_group.setLayout(events_layout)

        self.events_table = QTableWidget(0, 5)
        self.events_table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "Event",
                "Video",
                "Source",
                "Details",
            ]
        )
        header = self.events_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(150)
        self.events_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.events_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.events_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        events_layout.addWidget(self.events_table)

        main_layout.addWidget(events_group)

        # Footer --------------------------------------------------------
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)

        self.path_label = QLabel(
            f"Logs directory: <code>{LOG_DIR}</code><br>"
            f"Stats file: <code>{STATS_FILE.name}</code> | Events file: <code>{EVENTS_FILE.name}</code>"
        )
        self.path_label.setTextFormat(Qt.TextFormat.RichText)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        footer_layout.addWidget(self.path_label)

        footer_layout.addStretch()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        footer_layout.addWidget(refresh_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)

        main_layout.addLayout(footer_layout)

    # ------------------------------------------------------------------
    # Public slots
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Reload analytics data from disk and update the UI."""
        stats = debug_logger.get_stats_snapshot()
        events = debug_logger.get_recent_events(limit=self.MAX_EVENTS)

        self._populate_summary(stats, events)
        self._populate_videos_table(stats)
        self._populate_events_table(events)

    # ------------------------------------------------------------------
    # Data population helpers
    # ------------------------------------------------------------------
    def _populate_summary(self, stats: Dict[str, Any], events: Iterable[Dict[str, Any]]) -> None:
        totals = stats.get("totals", {})
        sessions = stats.get("sessions", {})
        session_count = len(sessions)

        current_session = sessions.get(stats.get("session_order", [None])[-1]) if sessions else None
        last_event = stats.get("last_event")

        summary_parts = [
            f"<b>Total events:</b> {totals.get('events', 0):,}",
            f"<b>Video loads:</b> {totals.get('video_loads', 0):,}",
            f"<b>Cast starts:</b> {totals.get('cast_starts', 0):,}",
            f"<b>Cast stops:</b> {totals.get('cast_stops', 0):,}",
            f"<b>Autoplay casts:</b> {totals.get('autoplay_casts', 0):,}",
            f"<b>Sample autoplay:</b> {totals.get('sample_autoplay_starts', 0):,}",
            f"<b>Tracked sessions:</b> {session_count:,}",
        ]

        if current_session:
            started_at = _format_timestamp(current_session.get("started_at"))
            summary_parts.append(
                f"<b>Current session:</b> {current_session.get('session_id', '')[:8]}… "
                f"(since {started_at})"
            )

        if last_event:
            summary_parts.append(
                f"<b>Last event:</b> {last_event.get('event')} at "
                f"{_format_timestamp(last_event.get('timestamp'))}"
            )

        self.summary_label.setText("<br>".join(summary_parts))

    def _populate_videos_table(self, stats: Dict[str, Any]) -> None:
        videos = list(stats.get("videos", {}).values())
        videos.sort(
            key=lambda item: (
                item.get("casts_started", 0),
                item.get("loads", 0),
            ),
            reverse=True,
        )
        videos = videos[: self.MAX_VIDEOS]

        self.videos_table.setRowCount(len(videos))
        for row, video_stats in enumerate(videos):
            last_cast = _format_timestamp(video_stats.get("last_cast_started_at"))

            row_data = [
                video_stats.get("video_name") or video_stats.get("video_path", "—"),
                _format_int(video_stats.get("loads")),
                _format_int(video_stats.get("casts_started")),
                _format_int(video_stats.get("casts_stopped")),
                last_cast,
                video_stats.get("last_stop_reason", "—"),
            ]

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.videos_table.setItem(row, col, item)

        self.videos_table.resizeColumnsToContents()

    def _populate_events_table(self, events: Iterable[Dict[str, Any]]) -> None:
        events_list = list(events)
        events_list.sort(key=lambda entry: entry.get("timestamp", ""), reverse=True)

        self.events_table.setRowCount(len(events_list))
        for row, record in enumerate(events_list):
            data = record.get("data", {})
            video_name = data.get("video_name") or data.get("video_path") or "—"
            source = data.get("source") or data.get("reason") or "—"
            details = _summarise_event(record)

            row_data = [
                _format_timestamp(record.get("timestamp")),
                record.get("event", "—"),
                video_name,
                source,
                details,
            ]

            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.events_table.setItem(row, col, item)

        self.events_table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self.refresh()


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def _format_timestamp(ts: Optional[str]) -> str:
    if not ts:
        return "—"
    try:
        normalised = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalised)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:  # pylint: disable=broad-except
        return str(ts)


def _format_int(value: Optional[Any]) -> str:
    try:
        return f"{int(value):,}"
    except Exception:  # pylint: disable=broad-except
        return "0"


def _summarise_event(record: Dict[str, Any]) -> str:
    event_type = record.get("event")
    data = record.get("data", {})

    if event_type == "video_loaded":
        return "Source: {source}, Loop: {loop}".format(
            source=data.get("source", "—"),
            loop="yes" if data.get("loop") else "no",
        )
    if event_type == "cast_started":
        return "URL: {url} | Subtitle: {subtitle}".format(
            url=data.get("url", "—"),
            subtitle="yes" if data.get("subtitle_path") else "no",
        )
    if event_type == "cast_stopped":
        return f"Reason: {data.get('reason', '—')}"
    if event_type == "cast_failed":
        return f"Error: {data.get('error', '—')}"
    if event_type == "sample_autoplay_started":
        return "Sample autoplay triggered"
    if event_type == "subtitle_linked":
        return f"Subtitle: {data.get('subtitle_name', '—')}"

    extras = [f"{key}={value}" for key, value in sorted(data.items()) if key != "video_name"]
    return " | ".join(extras) if extras else "—"


__all__ = ["StreamingStatsDialog"]
