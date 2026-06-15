"""
widgets/navigation.py — Sidebar & top header bar
=================================================
Sidebar emits a ``navigate`` signal (int page index) when a menu item is
clicked.  TopHeader.set_context() updates the title and breadcrumb.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QToolButton,
    QButtonGroup, QLineEdit, QSizePolicy, QWidget, QGraphicsDropShadowEffect
)

from icons import make_icon
from theme import T, NAV_ITEMS
from widgets.components import IconLabel


# ---------------------------------------------------------------------------
# NavButton
# ---------------------------------------------------------------------------

class NavButton(QToolButton):
    """Single sidebar navigation item that is togglable."""

    def __init__(self, icon_name: str, label: str, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.setText("  " + label)
        self.setCheckable(True)
        self.setAutoExclusive(False)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(18, 18))
        self.setMinimumHeight(38)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._refresh(False)
        self.toggled.connect(self._refresh)

    def _refresh(self, checked: bool):
        color = "white"
        self.setIcon(make_icon(self.icon_name, color, 18))
        bg     = "rgba(255, 255, 255, 0.2)" if checked else "transparent"
        weight = "700" if checked else "650"
        txt    = "white"
        self.setStyleSheet(
            f"QToolButton {{ background:{bg}; color:{txt}; border:none;"
            f" border-radius:10px; padding:6px 10px; text-align:left;"
            f" font-size:12px; font-weight:{weight}; }}"
            f"QToolButton:hover {{ background:rgba(255, 255, 255, 0.1); color:white; }}"
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

class Sidebar(QFrame):
    """Left navigation rail.  Emits ``navigate(index)`` on item click."""

    navigate  = Signal(int)   # page index
    do_logout = Signal()      # logout requested

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(212)
        self.setObjectName("Sidebar")
        self.setStyleSheet(
            f"#Sidebar {{ background: qlineargradient(x1:1, y1:0, x2:0, y2:1, stop:0 #578DFA, stop:1 #0A2E8C); border-right:none; border-top-right-radius: 20px}}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 18)
        root.setSpacing(8)

        # ── Logo block ──────────────────────────────────────────────────────
        logo = QHBoxLayout(); logo.setSpacing(10)
        badge = QFrame(); badge.setFixedSize(41,41)
        badge.setStyleSheet(f"background:rgba(255,255,255,0.18); border-radius:10px;")
        bl = QVBoxLayout(badge); bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(IconLabel("building", "white", 33), 0, Qt.AlignCenter)
        logo.addWidget(badge)

        lt = QVBoxLayout(); lt.setSpacing(0)
        t1 = QLabel("TMS")
        t1.setStyleSheet(f"color:white; font-size:20px; font-weight:800; background:transparent;")
        lt.addWidget(t1)
        logo.addLayout(lt); logo.addStretch(1)
        root.addLayout(logo)

        # ── Separator ───────────────────────────────────────────────────────
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:rgba(255, 255, 255, 0.15); margin:6px 0;")
        root.addSpacing(3); root.addWidget(sep); root.addSpacing(5)

        # ── Navigation items ────────────────────────────────────────────────
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self.buttons: list[NavButton] = []

        for icon, label, idx in NAV_ITEMS:
            btn = NavButton(icon, label)
            root.addWidget(btn)
            self._group.addButton(btn, idx)
            self.buttons.append(btn)

        self._group.idClicked.connect(self.navigate.emit)
        self.buttons[0].setChecked(True)  # Dashboard default

        root.addStretch(1)

        # ── Logout button ───────────────────────────────────────────────────
        sep2 = QFrame(); sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background:rgba(255, 255, 255, 0.15); margin:4px 0;")
        root.addWidget(sep2)

        logout_btn = NavButton("logout", "Logout")
        logout_btn.setStyleSheet(
            f"QToolButton {{ background:transparent; color:white; border:none;"
            f" border-radius:10px; padding:6px 10px; text-align:left;"
            f" font-size:12px; font-weight:500; }}"
            f"QToolButton:hover {{ background:rgba(255, 255, 255, 0.1); color:white; }}"
        )
        logout_btn.setIcon(make_icon("logout", "white", 18))
        logout_btn.setCheckable(False)
        logout_btn.clicked.connect(self.do_logout.emit)
        root.addWidget(logout_btn)

        # ── Footer card ─────────────────────────────────────────────────────
        ver = QLabel("v1.0.0  ·  © 2026 TMS")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(f"color:rgba(255, 255, 255, 0.6); font-size:10px; padding-top:6px; background:transparent;")
        root.addWidget(ver)

    def set_active(self, index: int):
        for btn in self.buttons:
            btn.setChecked(False)
        btn = self._group.button(index)
        if btn:
            btn.setChecked(True)


# ---------------------------------------------------------------------------
# TopHeader
# ---------------------------------------------------------------------------

class TopHeader(QFrame):
    """Top bar: page title, search, notification bell, avatar."""
    
    onboard_requested = Signal()

    def __init__(self, title: str = "Dashboard",
                 user_initial: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(66)
        self.setStyleSheet(f"background: transparent; border: none; border-top-left-radius: 20px; border-bottom-left-radius: 20px;")


        row = QHBoxLayout(self)
        row.setContentsMargins(28, 8, 28, 8)
        row.setSpacing(20)

        # Title + breadcrumb
        title_col = QVBoxLayout(); title_col.setSpacing(0)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color:{T.TEXT}; font-size: 28px; font-weight:700;")
        title_col.addWidget(self.title_lbl)
        row.addLayout(title_col)
        row.addStretch(1)

        # Onboard (+) Button
        self.add_btn = QToolButton()
        self.add_btn.setIcon(make_icon("plus", "white", 20))
        self.add_btn.setIconSize(QSize(20, 20))
        self.add_btn.setFixedSize(42, 42)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setStyleSheet(
            f"QToolButton {{ background: {T.PRIMARY}; border-radius: 21px; }}"
            f"QToolButton:hover {{ background: {T.PRIMARY_DK}; }}"
        )
        self.add_btn.clicked.connect(self.onboard_requested.emit)
        row.addWidget(self.add_btn)
        row.addSpacing(10)

        # Avatar
        self.avatar = QLabel(user_initial.upper())
        self.avatar.setFixedSize(42, 42)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setCursor(Qt.PointingHandCursor)
        self.avatar.setStyleSheet(
            f"background: {T.PRIMARY};"
            f" color:white; border:none; border-radius:21px; font-weight:800; font-size:16px;"
        )
        row.addWidget(self.avatar)
        row.addSpacing(10)

    def set_context(self, title: str):
        self.title_lbl.setText(title)

    def set_user(self, initial: str):
        self.avatar.setText(initial.upper())
