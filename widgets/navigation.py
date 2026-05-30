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
    QButtonGroup, QLineEdit, QSizePolicy, QWidget,
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
        self.setIconSize(QSize(20, 20))
        self.setMinimumHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._refresh(False)
        self.toggled.connect(self._refresh)

    def _refresh(self, checked: bool):
        color = T.PRIMARY if checked else T.TEXT_MUTED
        self.setIcon(make_icon(self.icon_name, color, 20))
        bg     = T.PRIMARY_SOFT if checked else "transparent"
        weight = "600" if checked else "500"
        txt    = T.PRIMARY if checked else "#3A4A63"
        self.setStyleSheet(
            f"QToolButton {{ background:{bg}; color:{txt}; border:none;"
            f" border-radius:10px; padding:8px 14px; text-align:left;"
            f" font-size:13.5px; font-weight:{weight}; }}"
            f"QToolButton:hover {{ background:{T.PRIMARY_SOFT}; color:{T.PRIMARY}; }}"
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
        self.setFixedWidth(252)
        self.setObjectName("Sidebar")
        self.setStyleSheet(
            f"#Sidebar {{ background:{T.SIDEBAR}; border-right:1px solid {T.BORDER}; }}"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 24, 18, 18)
        root.setSpacing(8)

        # ── Logo block ──────────────────────────────────────────────────────
        logo = QHBoxLayout(); logo.setSpacing(12)
        badge = QFrame(); badge.setFixedSize(48, 48)
        badge.setStyleSheet(f"background:{T.PRIMARY_SOFT}; border-radius:12px;")
        bl = QVBoxLayout(badge); bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(IconLabel("building", T.PRIMARY, 28), 0, Qt.AlignCenter)
        logo.addWidget(badge)

        lt = QVBoxLayout(); lt.setSpacing(0)
        t1 = QLabel("TMS")
        t1.setStyleSheet(f"color:{T.PRIMARY}; font-size:20px; font-weight:800;")
        t2 = QLabel("Tenant Management System")
        t2.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:10px; letter-spacing:0.3px;")
        lt.addWidget(t1); lt.addWidget(t2)
        logo.addLayout(lt); logo.addStretch(1)
        root.addLayout(logo)

        # ── Separator ───────────────────────────────────────────────────────
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{T.BORDER}; margin:6px 0;")
        root.addSpacing(10); root.addWidget(sep); root.addSpacing(6)

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
        sep2.setStyleSheet(f"background:{T.BORDER}; margin:4px 0;")
        root.addWidget(sep2)

        logout_btn = NavButton("logout", "Logout")
        logout_btn.setStyleSheet(
            f"QToolButton {{ background:transparent; color:{T.DANGER}; border:none;"
            f" border-radius:10px; padding:8px 14px; text-align:left;"
            f" font-size:13.5px; font-weight:500; }}"
            f"QToolButton:hover {{ background:{T.DANGER_SOFT}; color:{T.DANGER}; }}"
        )
        logout_btn.setIcon(make_icon("logout", T.DANGER, 20))
        logout_btn.setCheckable(False)
        logout_btn.clicked.connect(self.do_logout.emit)
        root.addWidget(logout_btn)

        # ── Footer card ─────────────────────────────────────────────────────
        root.addSpacing(6)
        footer = QFrame()
        footer.setStyleSheet(f"background:{T.PRIMARY_SOFT}; border-radius:14px;")
        fl = QVBoxLayout(footer); fl.setContentsMargins(16, 14, 16, 14); fl.setSpacing(4)
        h1 = QLabel("Manage your properties")
        h1.setStyleSheet(f"color:{T.TEXT}; font-size:12px; font-weight:700;")
        h1.setAlignment(Qt.AlignCenter)
        h2 = QLabel("with ease and clarity.")
        h2.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:11px;")
        h2.setAlignment(Qt.AlignCenter)
        fl.addWidget(h1); fl.addWidget(h2)
        root.addWidget(footer)

        ver = QLabel("v1.0.0  ·  © 2025 TMS")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(f"color:{T.TEXT_SUBTLE}; font-size:10px; padding-top:6px;")
        root.addWidget(ver)

    def set_active(self, index: int):
        for btn in self.buttons:
            btn.setChecked(False)
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)


# ---------------------------------------------------------------------------
# TopHeader
# ---------------------------------------------------------------------------

class TopHeader(QFrame):
    """Top bar: page title, breadcrumb, search, notification bell, avatar."""

    def __init__(self, title: str = "Dashboard", breadcrumb: str = "Dashboard",
                 user_initial: str = "A", parent=None):
        super().__init__(parent)
        self.setFixedHeight(82)
        self.setStyleSheet(f"background:{T.SURFACE}; border-bottom:1px solid {T.BORDER};")

        row = QHBoxLayout(self)
        row.setContentsMargins(28, 16, 28, 8)
        row.setSpacing(20)

        # Title + breadcrumb
        title_col = QVBoxLayout(); title_col.setSpacing(2)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color:{T.TEXT}; font-size:22px; font-weight:700;")
        self.crumb_lbl = QLabel()
        self.crumb_lbl.setStyleSheet("font-size:12px;")
        self._set_crumb(breadcrumb)
        title_col.addWidget(self.title_lbl)
        title_col.addWidget(self.crumb_lbl)
        row.addLayout(title_col)
        row.addStretch(1)

        # Search box
        search_wrap = QFrame()
        search_wrap.setFixedHeight(42)
        search_wrap.setMinimumWidth(320)
        search_wrap.setStyleSheet(
            f"background:{T.BG}; border:1px solid {T.BORDER}; border-radius:12px;"
        )
        sl = QHBoxLayout(search_wrap); sl.setContentsMargins(12, 0, 12, 0); sl.setSpacing(8)
        sl.addWidget(IconLabel("search", T.TEXT_SUBTLE, 17))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search anything…")
        self.search_input.setStyleSheet(
            f"QLineEdit {{ border:none; background:transparent;"
            f" color:{T.TEXT}; font-size:13px; }}"
        )
        sl.addWidget(self.search_input, 1)
        row.addWidget(search_wrap)

        # Bell
        bell = QToolButton()
        bell.setIcon(make_icon("bell", T.TEXT_MUTED, 20))
        bell.setIconSize(QSize(20, 20)); bell.setFixedSize(42, 42)
        bell.setCursor(Qt.PointingHandCursor)
        bell.setStyleSheet(
            f"QToolButton {{ background:{T.BG}; border:1px solid {T.BORDER};"
            f" border-radius:12px; }}"
            f"QToolButton:hover {{ background:{T.PRIMARY_SOFT}; }}"
        )
        row.addWidget(bell)

        # Avatar
        self.avatar = QLabel(user_initial.upper())
        self.avatar.setFixedSize(42, 42)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setCursor(Qt.PointingHandCursor)
        self.avatar.setStyleSheet(
            f"background:{T.PRIMARY}; color:white; border-radius:12px;"
            f" font-weight:700; font-size:15px;"
        )
        row.addWidget(self.avatar)

    def _set_crumb(self, breadcrumb: str):
        self.crumb_lbl.setText(
            f"<span style='color:{T.PRIMARY};'>Home</span>"
            f" <span style='color:{T.TEXT_SUBTLE};'>/</span>"
            f" <span style='color:{T.TEXT_MUTED};'>{breadcrumb}</span>"
        )

    def set_context(self, title: str, breadcrumb: str):
        self.title_lbl.setText(title)
        self._set_crumb(breadcrumb)

    def set_user(self, initial: str):
        self.avatar.setText(initial.upper())
