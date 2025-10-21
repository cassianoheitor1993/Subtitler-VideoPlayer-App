"""
Stats Footer Widget
Displays ongoing player statuses within the main status bar.
"""

from __future__ import annotations

from typing import Dict

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QToolButton,
)


class StatusChip(QFrame):
    """Compact widget representing a single status entry."""

    action_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusChip")
        self.setStyleSheet(
            """
            QFrame#StatusChip {
                background-color: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
            }
            QFrame#StatusChip QLabel {
                color: #f0f0f0;
            }
            QFrame#StatusChip QPushButton,
            QFrame#StatusChip QToolButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QFrame#StatusChip QPushButton:hover,
            QFrame#StatusChip QToolButton:hover {
                background-color: #1177bb;
            }
            QFrame#StatusChip QToolButton {
                padding: 0px 6px;
                min-width: 18px;
            }
            """
        )

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label)

        self.action_button = QPushButton("Abrir")
        self.action_button.setVisible(False)
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.clicked.connect(self.action_clicked.emit)
        self.action_button.setFixedHeight(22)
        layout.addWidget(self.action_button)

        self.cancel_button = QToolButton()
        self.cancel_button.setText("✕")
        self.cancel_button.setVisible(False)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        self.cancel_button.setFixedHeight(22)
        layout.addWidget(self.cancel_button)

    def set_text(self, text: str) -> None:
        self.label.setText(text)

    def set_action(self, label: str | None) -> None:
        if label:
            self.action_button.setText(label)
            self.action_button.show()
        else:
            self.action_button.hide()

    def set_cancel_enabled(self, enabled: bool) -> None:
        self.cancel_button.setVisible(enabled)


class StatsFooter(QWidget):
    """Widget that renders player status entries inside the status bar."""

    action_requested = pyqtSignal(str)
    cancel_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._chips: Dict[str, StatusChip] = {}
        self._clear_timers: Dict[str, QTimer] = {}

        self._message_timer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self._on_message_timeout)

        layout = QHBoxLayout()
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(12)
        self.setLayout(layout)

        self._message_label = QLabel()
        self._message_label.setStyleSheet("color: #e0e0e0;")
        self._message_label.setVisible(False)
        layout.addWidget(self._message_label)

        self._chip_container = QWidget()
        self._chip_layout = QHBoxLayout()
        self._chip_layout.setContentsMargins(0, 0, 0, 0)
        self._chip_layout.setSpacing(8)
        self._chip_container.setLayout(self._chip_layout)
        layout.addWidget(self._chip_container)

        layout.addStretch()

        self._idle_label = QLabel("Ready")
        self._idle_label.setStyleSheet("color: #b0b0b0;")
        self._chip_layout.addWidget(self._idle_label)

    # ------------------------------------------------------------------
    # Basic status management
    # ------------------------------------------------------------------
    def set_idle(self, text: str = "Ready") -> None:
        """Set idle text when there are no active statuses."""
        self._idle_label.setText(text)
        if not self._chips:
            self._idle_label.show()

    def show_message(self, message: str, timeout_ms: int = 0) -> None:
        """Display a temporary message alongside the status chips."""
        self._message_label.setText(message)
        self._message_label.setVisible(bool(message))

        if timeout_ms > 0 and message:
            self._message_timer.start(timeout_ms)
        else:
            self._message_timer.stop()

    def set_status(
        self,
        key: str,
        text: str,
        *,
        button_text: str | None = None,
        cancelable: bool = False,
    ) -> None:
        """Add or update a status chip."""
        chip = self._chips.get(key)
        if chip is None:
            chip = StatusChip(self)
            chip.action_clicked.connect(lambda key=key: self.action_requested.emit(key))
            chip.cancel_clicked.connect(lambda key=key: self.cancel_requested.emit(key))
            self._chips[key] = chip
            self._chip_layout.addWidget(chip)
            self._idle_label.hide()

        chip.set_text(text)
        chip.set_action(button_text)
        chip.set_cancel_enabled(cancelable)

        # Reset any pending auto-clear timers if status changed back to active
        timer = self._clear_timers.pop(key, None)
        if timer:
            timer.stop()
            timer.deleteLater()

    def clear_status(self, key: str) -> None:
        """Remove a status chip."""
        chip = self._chips.pop(key, None)
        if chip:
            chip.hide()
            chip.deleteLater()

        timer = self._clear_timers.pop(key, None)
        if timer:
            timer.stop()
            timer.deleteLater()

        if not self._chips:
            self._idle_label.show()

    def clear_all(self) -> None:
        for key in list(self._chips.keys()):
            self.clear_status(key)

    def schedule_clear(self, key: str, delay_ms: int) -> None:
        """Schedule a status for automatic removal."""
        if key not in self._chips:
            return

        timer = self._clear_timers.get(key)
        if timer:
            timer.stop()
        else:
            timer = QTimer(self)
            timer.setSingleShot(True)
            self._clear_timers[key] = timer
            timer.timeout.connect(lambda key=key: self.clear_status(key))

        timer.start(delay_ms)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _on_message_timeout(self) -> None:
        self._message_label.clear()
        self._message_label.hide()