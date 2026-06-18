"""
pages/settings.py — Application Settings page
===============================================
Covers: profile, password, database, theme, backup, and preferences.
All sections include TODO(DB) comments marking where real logic will go.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QLineEdit, QPushButton, QComboBox, QListView, QFrame, QCheckBox, QSizePolicy,
    QFileDialog, QMessageBox
)

import csv
from database.repositories import get_tenants, get_payments, get_rooms, get_admin_profile, update_admin_profile

from theme import T
from icons import make_icon
from widgets.components import (
    Card, section_title, primary_button, ghost_button, IconLabel, Toast
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
    profile_updated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self._load_profile()

    def _load_profile(self):
        prof = get_admin_profile()
        self.set_user(prof.get("username", "admin"))
        self._email.setText(prof.get("email", ""))
        self._phone.setText(prof.get("contact", ""))

    def set_user(self, username: str):
        self._fullname.setText(username)
        self._av_name.setText(username)
        self._av.setText(username[0].upper() if username else "A")

    def _save_profile(self):
        name = self._fullname.text().strip()
        email = self._email.text().strip()
        phone = self._phone.text().strip()
        
        if not name:
            self._toast("Full Name (username) cannot be empty!")
            return
            
        update_admin_profile(name, email, phone)
        self.set_user(name)
        self.profile_updated.emit(name)
        # self._toast("Profile saved. You must use this new name to log in.")
        Toast("Profile saved. Use your new name to log in.", "blue").show_in(self)

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
        self._av = QLabel("A"); self._av.setFixedSize(70, 70); self._av.setAlignment(Qt.AlignCenter)
        self._av.setStyleSheet(f"background:{T.PRIMARY}; color:white; border-radius:18px; font-size:28px; font-weight:700;")
        av_row.addWidget(self._av)
        av_info = QVBoxLayout(); av_info.setSpacing(4)
        self._av_name = self._make_lbl("Admin User", f"color:{T.TEXT}; font-size:16px; font-weight:700;")
        av_info.addWidget(self._av_name)
        av_info.addWidget(self._make_lbl("Property Manager  ·  v1.0.0", f"color:{T.TEXT_MUTED}; font-size:12.5px;"))
        av_row.addLayout(av_info); av_row.addStretch(1)
        body.addLayout(av_row)
        body.addSpacing(8)

        body.addWidget(_lbl("Full Name"))
        self._fullname = _input("Your full name", "Administrator")
        body.addWidget(self._fullname)

        body.addWidget(_lbl("Email Address"))
        self._email = _input("example.com", "")
        body.addWidget(self._email)

        body.addWidget(_lbl("Phone Number"))
        self._phone = _input("e.g. 09171234567")
        body.addWidget(self._phone)

        save_profile = primary_button("Save Profile")
        save_profile.clicked.connect(self._save_profile)
        body.addWidget(save_profile)
        left.addWidget(card)

        # ── Appearance ─────────────────────────────────────────────────────────
        card3, body3 = _section_card("Appearance", "paint", T.WARNING, T.WARNING_SOFT)
        body3.addWidget(_lbl("Theme"))
        
        coming_soon_lbl = QLabel("Coming Soon")
        coming_soon_lbl.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:13px; font-style:italic;")
        body3.addWidget(coming_soon_lbl)
        
        right.addWidget(card3)

        # ── Backup & Export ──────────────────────────────────────────────────────
        card5, body5 = _section_card("Backup & Export", "download", T.DANGER, T.DANGER_SOFT)
        body5.addWidget(_lbl(
            "Export your data as CSV files for backups or reporting.", muted=True
        ))
        body5.addSpacing(6)
        exp_row = QHBoxLayout(); exp_row.setSpacing(12)
        btn_tenants = ghost_button("Export Tenants", "users")
        btn_tenants.clicked.connect(self._export_tenants)
        exp_row.addWidget(btn_tenants)
        
        btn_payments = ghost_button("Export Payments", "wallet")
        btn_payments.clicked.connect(self._export_payments)
        exp_row.addWidget(btn_payments)
        
        btn_rooms = ghost_button("Export Rooms", "door")
        btn_rooms.clicked.connect(self._export_rooms)
        exp_row.addWidget(btn_rooms)
        
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
        """Simple status message in a dialog."""
        QMessageBox.information(self, "Notice", msg)

    def _export_tenants(self):
        data = get_tenants()
        self._write_csv("Tenants", data)

    def _export_payments(self):
        data = get_payments()
        self._write_csv("Payments", data)

    def _export_rooms(self):
        data = get_rooms()
        self._write_csv("Rooms", data)

    def _write_csv(self, name: str, data: list[dict]):
        if not data:
            self._toast(f"No {name.lower()} data to export.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, f"Save {name} CSV", f"{name.lower()}_export.csv", "CSV Files (*.csv)"
        )
        
        if filepath:
            try:
                keys = data[0].keys()
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
                # self._toast(f"Successfully exported {name} to CSV.")
                Toast(f"{name} exported to CSV.", "green").show_in(self)
            except Exception as e:
                self._toast(f"Error exporting CSV: {e}")
