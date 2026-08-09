#!/usr/bin/env python3
"""
Professional Log Widget
Clean, colored activity log
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QFrame, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from ..styles.professional_theme import COLORS


class ProfessionalLogWidget(QWidget):
    """Professional activity log with filtering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: list[tuple[str, str, str]] = []  # (timestamp, level, message)
        self._filter_text = ""
        self._setup_ui()

    def _setup_ui(self):
        """Setup log widget UI."""
        container = QFrame()
        container.setObjectName("card")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()

        # Search - also used as a per-tunnel filter (see set_filter())
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search or filter logs...")
        self.search_box.textChanged.connect(self._on_filter_changed)
        header_layout.addWidget(self.search_box)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("default")
        clear_btn.setMaximumWidth(70)
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Log area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMinimumHeight(120)
        layout.addWidget(self.log_text)

        # Footer
        footer_layout = QHBoxLayout()
        self.log_count_label = QLabel("0 entries")
        self.log_count_label.setObjectName("tertiary")
        self.log_count_label.setFont(QFont("Segoe UI", 9))
        footer_layout.addWidget(self.log_count_label)
        footer_layout.addStretch()

        layout.addLayout(footer_layout)

        self.log_count = 0

    def add_log(self, message: str, level: str = "info"):
        """Add a log entry."""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.entries.append((timestamp, level, message))

        self.log_count += 1
        self.log_count_label.setText(f"{self.log_count} entries")

        if self._matches_filter(message):
            self._append_entry(timestamp, level, message)

    def _matches_filter(self, message: str) -> bool:
        if not self._filter_text:
            return True
        return self._filter_text.lower() in message.lower()

    def _append_entry(self, timestamp: str, level: str, message: str):
        """Insert one formatted entry at the end of the visible log."""
        colors_map = {
            'info': COLORS['accent_secondary'],
            'success': COLORS['text_success'],
            'warning': COLORS['accent_warning'],
            'error': COLORS['text_error'],
        }
        color = colors_map.get(level, COLORS['text_primary'])

        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(COLORS['text_tertiary']))
        cursor.insertText(f"[{timestamp}] ", fmt)

        level_text = level.upper()[:4].ljust(4)
        fmt.setForeground(QColor(color))
        cursor.insertText(f"[{level_text}] ", fmt)

        fmt.setForeground(QColor(COLORS['text_primary']))
        cursor.insertText(f"{message}\n", fmt)

        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

    def _on_filter_changed(self, text: str):
        self._filter_text = text
        self._render()

    def _render(self):
        """Redraw the visible log from self.entries, applying the current filter."""
        self.log_text.clear()
        for timestamp, level, message in self.entries:
            if self._matches_filter(message):
                self._append_entry(timestamp, level, message)

    def set_filter(self, text: str):
        """Filter the log to lines containing `text` (empty string clears the filter).

        Updates the search box itself so the active filter is visible and the user can
        clear it manually to see every tunnel's output again.
        """
        self.search_box.setText(text)

    def clear_logs(self):
        """Clear all logs."""
        self.entries.clear()
        self.log_text.clear()
        self.log_count = 0
        self.log_count_label.setText("0 entries")


def log_level_from_message(message: str) -> str:
    """Determine log level from message content."""
    message_lower = message.lower()

    if any(word in message_lower for word in ['error', 'failed', 'failure', 'exception']):
        return 'error'
    elif any(word in message_lower for word in ['warning', 'warn']):
        return 'warning'
    elif any(word in message_lower for word in ['success', 'started', 'connected', 'complete']):
        return 'success'
    else:
        return 'info'
