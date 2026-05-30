from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                                QPushButton, QComboBox, QCheckBox, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt
from tms.pages._base import PageBase
from tms.widgets.cards import Card


def _section_card(icon, icon_bg, icon_fg, title):
    c = Card()
    h = QHBoxLayout()
    ic = QLabel(icon)
    ic.setStyleSheet(f"background:{icon_bg}; color:{icon_fg}; border-radius:10px; min-width:36px; min-height:36px; font-size:18px;")
    ic.setAlignment(Qt.AlignCenter)
    h.addWidget(ic)
    t = QLabel(title); t.setStyleSheet("font-size:15px; font-weight:700;")
    h.addWidget(t); h.addStretch()
    c.layout().addLayout(h)
    return c


def _labeled(text, w):
    box = QVBoxLayout(); box.setSpacing(4)
    l = QLabel(text); l.setObjectName("formLabel")
    box.addWidget(l); box.addWidget(w)
    return box


class SettingsPage(PageBase):
    def __init__(self):
        super().__init__()
        self.body.addWidget(QLabel("Manage your account, preferences, and data", styleSheet="color:#64748b;"))

        grid = QGridLayout(); grid.setSpacing(16)

        # User Profile
        profile = _section_card("👤", "#dbeafe", "#2563eb", "User Profile")
        head = QHBoxLayout()
        avatar = QLabel("A"); avatar.setStyleSheet("background:#2563eb; color:white; border-radius:28px; min-width:56px; min-height:56px; font-size:24px; font-weight:700;")
        avatar.setAlignment(Qt.AlignCenter)
        head.addWidget(avatar)
        col = QVBoxLayout(); col.setSpacing(2)
        col.addWidget(QLabel("Admin User", styleSheet="font-weight:700; font-size:15px;"))
        col.addWidget(QLabel("Property Manager  •  v1.0.0", styleSheet="color:#64748b; font-size:12px;"))
        head.addLayout(col); head.addStretch()
        change = QPushButton(" ✎  Change Photo"); change.setObjectName("ghostBtn"); change.setCursor(Qt.PointingHandCursor)
        change.clicked.connect(lambda: QMessageBox.information(self, "Change Photo", "Photo upload coming soon."))
        head.addWidget(change)
        profile.layout().addLayout(head)
        self.full_name = QLineEdit("Administrator")
        self.email = QLineEdit("admin@tms.local")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("e.g. 09171234567")
        profile.layout().addLayout(_labeled("Full Name", self.full_name))
        profile.layout().addLayout(_labeled("Email Address", self.email))
        profile.layout().addLayout(_labeled("Phone Number", self.phone))
        save = QPushButton("Save Profile"); save.setObjectName("primaryBtn"); save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(lambda: QMessageBox.information(self, "Profile", "Profile saved."))
        profile.layout().addWidget(save)
        grid.addWidget(profile, 0, 0)

        # Appearance
        appear = _section_card("🎨", "#fef3c7", "#d97706", "Appearance")
        theme = QComboBox(); theme.addItems(["Light (Default)", "Dark", "System"])
        lang = QComboBox(); lang.addItems(["English (Default)", "Filipino", "Spanish"])
        appear.layout().addLayout(_labeled("Theme", theme))
        appear.layout().addLayout(_labeled("Language", lang))
        appear.layout().addStretch()
        grid.addWidget(appear, 0, 1)

        # Change Password
        pwd_card = _section_card("🔒", "#ede9fe", "#7c3aed", "Change Password")
        self.cur = QLineEdit(); self.cur.setEchoMode(QLineEdit.Password); self.cur.setPlaceholderText("Enter current password")
        self.new = QLineEdit(); self.new.setEchoMode(QLineEdit.Password); self.new.setPlaceholderText("Enter new password")
        self.conf = QLineEdit(); self.conf.setEchoMode(QLineEdit.Password); self.conf.setPlaceholderText("Re-enter new password")
        pwd_card.layout().addLayout(_labeled("Current Password", self.cur))
        pwd_card.layout().addLayout(_labeled("New Password", self.new))
        pwd_card.layout().addLayout(_labeled("Confirm New Password", self.conf))
        pwd_card.layout().addWidget(QLabel("Password must be at least 8 characters.", styleSheet="color:#64748b; font-size:11px;"))
        up = QPushButton("🔑  Update Password"); up.setObjectName("primaryBtn"); up.setCursor(Qt.PointingHandCursor)
        up.clicked.connect(self._update_password)
        pwd_card.layout().addWidget(up)
        grid.addWidget(pwd_card, 1, 0)

        # Database
        db_card = _section_card("💾", "#dcfce7", "#16a34a", "Database Connection")
        self.db_path = QLineEdit("tms.db (demo mode)")
        db_card.layout().addLayout(_labeled("Database File Path", self.db_path))
        row = QHBoxLayout()
        test = QPushButton(" 💾  Test Connection"); test.setObjectName("ghostBtn"); test.setCursor(Qt.PointingHandCursor)
        browse = QPushButton(" 📁  Browse..."); browse.setObjectName("ghostBtn"); browse.setCursor(Qt.PointingHandCursor)
        test.clicked.connect(lambda: QMessageBox.information(self, "Database", "Demo mode — connect SQLite later."))
        browse.clicked.connect(self._browse_db)
        row.addWidget(test); row.addWidget(browse); row.addStretch()
        db_card.layout().addLayout(row)
        db_card.layout().addWidget(QLabel("●  Demo mode — no database connected", styleSheet="color:#d97706; font-size:12px;"))
        grid.addWidget(db_card, 1, 1)

        # Backup & Export
        backup = _section_card("⬇️", "#fee2e2", "#dc2626", "Backup & Export")
        backup.layout().addWidget(QLabel("Export your data as CSV or backup the SQLite database file.",
                                          styleSheet="color:#64748b; font-size:12px;"))
        bb = QHBoxLayout()
        for lbl in [" 👥  Export Tenants CSV", " 💳  Export Payments CSV", " 💾  Backup DB"]:
            b = QPushButton(lbl); b.setObjectName("ghostBtn"); b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, t=lbl: QMessageBox.information(self, "Export", f"{t.strip()} — placeholder."))
            bb.addWidget(b)
        bb.addStretch()
        backup.layout().addLayout(bb)
        grid.addWidget(backup, 2, 0)

        # Preferences
        prefs = _section_card("⚙️", "#dbeafe", "#2563eb", "Preferences")
        prefs.layout().addWidget(QCheckBox("Send payment reminders"))
        chk = QCheckBox("Show overdue alerts on startup"); chk.setChecked(True)
        prefs.layout().addWidget(chk)
        prefs.layout().addWidget(QCheckBox("Auto-backup on exit"))
        prefs.layout().addStretch()
        grid.addWidget(prefs, 2, 1)

        self.body.addLayout(grid)

    def _update_password(self):
        if len(self.new.text()) < 8:
            QMessageBox.warning(self, "Password", "Password must be at least 8 characters."); return
        if self.new.text() != self.conf.text():
            QMessageBox.warning(self, "Password", "New password and confirmation do not match."); return
        # TODO: UPDATE users SET password = ? WHERE id = ?
        QMessageBox.information(self, "Password", "Password updated.")
        self.cur.clear(); self.new.clear(); self.conf.clear()

    def _browse_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select SQLite Database", "", "SQLite (*.db *.sqlite);;All files (*)")
        if path: self.db_path.setText(path)
