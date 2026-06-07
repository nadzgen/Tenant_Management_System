"""
pages/settings.py — Application Settings page
===============================================
Covers: profile, password, database, theme, backup, and preferences.
All sections include TODO(DB) comments marking where real logic will go.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QLineEdit, QPushButton, QComboBox, QFrame, QCheckBox, QSizePolicy,
)

from theme import T
from icons import make_icon
from widgets.components import (
    Card, section_title, primary_button, ghost_button, IconLabel,
)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _lbl(text: str, muted: bool = False) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(f"color:{T.TEXT};")
    return l


def _input(placeholder: str, value: str = "", echo: bool = False) -> QLineEdit:
    le = QLineEdit(value)
    le.setPlaceholderText(placeholder)
    le.setFixedHeight(44)
    if echo:
        le.setEchoMode(QLineEdit.Password)
    le.setStyleSheet(
        f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
        f" border-radius:11px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
        f"QLineEdit:focus {{ border:1.5px solid {T.PRIMARY}; }}"
    )
    return le


def _divider() -> QFrame:
    f = QFrame(); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{T.BORDER}; margin:4px 0;")
    return f


def _section_card(title: str, icon: str, color: str, soft: str) -> tuple[Card, QVBoxLayout]:
    card = Card(padding=24)
    head = QHBoxLayout(); head.setSpacing(12)
    badge = QFrame(); badge.setFixedSize(38, 38)
    badge.setStyleSheet(f"background:{soft}; border-radius:10px;")
    bl = QVBoxLayout(badge); bl.setContentsMargins(0, 0, 0, 0)
    bl.addWidget(IconLabel(icon, color, 20), 0, Qt.AlignCenter)
    head.addWidget(badge)
    h = QLabel(title); h.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
    head.addWidget(h); head.addStretch(1)
    card.body.addLayout(head)
    card.body.addWidget(_divider())
    return card, card.body


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28); root.setSpacing(22)

        root.addWidget(section_title("Settings", "Manage your account, preferences, and data"))

        # ── Two-column layout ─────────────────────────────────────────────────
        cols = QHBoxLayout(); cols.setSpacing(22); cols.setAlignment(Qt.AlignTop)
        left  = QVBoxLayout(); left.setSpacing(22)
        right = QVBoxLayout(); right.setSpacing(22)

        # ── Profile ────────────────────────────────────────────────────────────
        card, body = _section_card("User Profile", "user", T.PRIMARY, T.PRIMARY_SOFT)

        # Avatar row
        av_row = QHBoxLayout(); av_row.setSpacing(18)
        av = QLabel("A"); av.setFixedSize(70, 70); av.setAlignment(Qt.AlignCenter)
        av.setStyleSheet(f"background:{T.PRIMARY}; color:white; border-radius:18px; font-size:28px; font-weight:700;")
        av_row.addWidget(av)
        av_info = QVBoxLayout(); av_info.setSpacing(4)
        av_info.addWidget(QLabel("Admin User") if False else self._make_lbl("Admin User", f"color:{T.TEXT}; font-size:16px; font-weight:700;"))
        av_info.addWidget(self._make_lbl("Property Manager  ·  v1.0.0", f"color:{T.TEXT_MUTED}; font-size:12.5px;"))
        av_row.addLayout(av_info); av_row.addStretch(1)
        change_av = ghost_button("Change Photo", "edit")
        change_av.setEnabled(False)  # placeholder
        av_row.addWidget(change_av)
        body.addLayout(av_row)
        body.addSpacing(8)

        body.addWidget(_lbl("Full Name"))
        self._fullname = _input("Your full name", "Administrator")
        body.addWidget(self._fullname)

        body.addWidget(_lbl("Email Address"))
        self._email = _input("your@email.com", "admin@tms.local")
        body.addWidget(self._email)

        body.addWidget(_lbl("Phone Number"))
        self._phone = _input("e.g. 09171234567")
        body.addWidget(self._phone)

        save_profile = primary_button("Save Profile")
        save_profile.clicked.connect(lambda: self._toast("Profile saved (placeholder)"))
        body.addWidget(save_profile)
        left.addWidget(card)

        # ── Change Password ────────────────────────────────────────────────────
        card2, body2 = _section_card("Change Password", "lock", T.PURPLE, T.PURPLE_SOFT)
        body2.addWidget(_lbl("Current Password"))
        self._cur_pw = _input("Enter current password", echo=True)
        body2.addWidget(self._cur_pw)
        body2.addWidget(_lbl("New Password"))
        self._new_pw = _input("Enter new password", echo=True)
        body2.addWidget(self._new_pw)
        body2.addWidget(_lbl("Confirm New Password"))
        self._conf_pw = _input("Re-enter new password", echo=True)
        body2.addWidget(self._conf_pw)
        body2.addWidget(_lbl("Password must be at least 8 characters.", muted=True))
        save_pw = primary_button("Update Password", "key")
        # TODO(DB): Hash new password and UPDATE users SET password=? WHERE id=?
        save_pw.clicked.connect(lambda: self._toast("Password updated (placeholder)"))
        body2.addWidget(save_pw)
        left.addWidget(card2)

        # ── Appearance ─────────────────────────────────────────────────────────
        card3, body3 = _section_card("Appearance", "paint", T.WARNING, T.WARNING_SOFT)
        body3.addWidget(_lbl("Theme"))
        theme_cb = QComboBox(); theme_cb.addItems(["Light (Default)", "Dark (Coming Soon)"])
        theme_cb.setFixedHeight(44)
        theme_cb.setStyleSheet(
            f"QComboBox {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
            f" border-radius:11px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        body3.addWidget(theme_cb)


        right.addWidget(card3)

        # ── Database ────────────────────────────────────────────────────────────
        card4, body4 = _section_card("Database Connection", "database", T.SUCCESS, T.SUCCESS_SOFT)
        body4.addWidget(_lbl("Database File Path"))
        self._db_path = _input("e.g. C:/TMS/data/tms.db", "tms.db (demo mode)")
        body4.addWidget(self._db_path)
        # TODO(DB): Connect to SQLite: sqlite3.connect(self._db_path.text())
        db_row = QHBoxLayout(); db_row.setSpacing(10)
        test_btn = ghost_button("Test Connection", "database")
        test_btn.clicked.connect(lambda: self._toast("Connection OK (placeholder)"))
        browse_btn = ghost_button("Browse…")
        db_row.addWidget(test_btn); db_row.addWidget(browse_btn); db_row.addStretch(1)
        body4.addLayout(db_row)

        # Connection status indicator
        status_row = QHBoxLayout(); status_row.setSpacing(8)
        dot = QFrame(); dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background:{T.WARNING}; border-radius:5px;")
        status_row.addWidget(dot)
        status_row.addWidget(_lbl("Demo mode — no database connected", muted=True))
        status_row.addStretch(1)
        body4.addLayout(status_row)
        right.addWidget(card4)

        # ── Backup & Export ──────────────────────────────────────────────────────
        card5, body5 = _section_card("Backup & Export", "download", T.DANGER, T.DANGER_SOFT)
        body5.addWidget(_lbl(
            "Export your data as CSV or backup the SQLite database file.", muted=True
        ))
        body5.addSpacing(6)
        exp_row = QHBoxLayout(); exp_row.setSpacing(12)
        for label, icon in [("Export Tenants CSV", "users"), ("Export Payments CSV", "wallet"), ("Backup DB", "database")]:
            b = ghost_button(label, icon)
            # TODO(DB): Implement CSV/DB export logic here
            b.clicked.connect(lambda checked=False, l=label: self._toast(f"{l} — placeholder"))
            exp_row.addWidget(b)
        exp_row.addStretch(1)
        body5.addLayout(exp_row)
        right.addWidget(card5)



        left.addStretch(1); right.addStretch(1)
        cols.addLayout(left, 1); cols.addLayout(right, 1)
        root.addLayout(cols)
        root.addStretch(1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_lbl(self, text: str, style: str) -> QLabel:
        l = QLabel(text); l.setStyleSheet(style); return l

    def _toast(self, msg: str):
        """Simple status message in a dialog (replace with toast widget later)."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Notice", msg)
