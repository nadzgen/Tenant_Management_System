"""
pages/login.py — Login screen
==============================
Displayed in the stacked widget before the user authenticates.
Emits ``login_success(username)`` on valid credentials.

TODO(DB): Replace the hardcoded credential check with an SQLite lookup:
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", ...)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QFrame, QGraphicsDropShadowEffect, QSizePolicy,
)

from icons import make_icon
from theme import T
from widgets.components import IconLabel
from database.repositories import validate_login


class LoginPage(QWidget):
    """Full-screen login page (replaces app background until authenticated)."""

    login_success = Signal(str)   # emits the username on success

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAutoFillBackground(False)

        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F0F4FF, stop:1 #EAF1FF);")

        self._build()

    # ── UI construction ─────────────────────────────────────────────────────

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Left illustration panel ─────────────────────────────────────────
        left = QFrame()
        left.setMinimumWidth(420)
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            f"stop:0 {T.PRIMARY}, stop:1 #1A4FCC);"
            "border-top-right-radius: 40px;"
        )
        lv = QVBoxLayout(left)
        lv.setContentsMargins(52, 60, 52, 60)
        lv.setSpacing(20)
        lv.setAlignment(Qt.AlignCenter)

        big_icon_wrap = QFrame()
        big_icon_wrap.setFixedSize(120, 120)
        big_icon_wrap.setStyleSheet(
            "background:rgba(255,255,255,0.18); border-radius:30px;"
        )
        bw = QVBoxLayout(big_icon_wrap)
        bw.setContentsMargins(0, 0, 0, 0)
        bw.addWidget(IconLabel("building", "white", 64), 0, Qt.AlignCenter)
        lv.addWidget(big_icon_wrap, 0, Qt.AlignCenter)
        lv.addSpacing(10)

        h1 = QLabel("Welcome to TMS")
        h1.setAlignment(Qt.AlignCenter)
        h1.setStyleSheet("color:white; font-size:28px; font-weight:800; background:transparent;")
        h1.setWordWrap(True)
        lv.addWidget(h1)

        h2 = QLabel(
            "Your all-in-one solution for managing\n"
            "tenants, rooms, and payments —\n"
            "simple, elegant, and effortless."
        )
        h2.setAlignment(Qt.AlignCenter)
        h2.setStyleSheet("color:rgba(255,255,255,0.75); font-size:13.5px; background:transparent;")
        h2.setWordWrap(True)
        lv.addWidget(h2)
        lv.addStretch(1)

        for icon, text in [
            ("users",  "Manage all your tenants in one place"),
            ("wallet", "Track rent payments at a glance"),
            ("chart",  "Insightful reports and analytics"),
        ]:
            row = QHBoxLayout(); row.setSpacing(14)
            dot = QFrame(); dot.setFixedSize(34, 34)
            dot.setStyleSheet("background:rgba(255,255,255,0.20); border-radius:9px;")
            dl = QVBoxLayout(dot); dl.setContentsMargins(0, 0, 0, 0)
            dl.addWidget(IconLabel(icon, "white", 18), 0, Qt.AlignCenter)
            row.addWidget(dot)
            lbl = QLabel(text)
            lbl.setStyleSheet("color:rgba(255,255,255,0.85); font-size:13px; background:transparent;")
            row.addWidget(lbl); row.addStretch(1)
            lv.addLayout(row)

        outer.addWidget(left, 1)

        # ── Right login card ────────────────────────────────────────────────
        right = QWidget()
        right.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        right.setFixedWidth(520)
        right.setStyleSheet("background:transparent;")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(56, 0, 56, 0)
        rv.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setStyleSheet(
            f"#LoginCard {{ background:{T.SURFACE}; border:1px solid {T.BORDER};"
            f" border-radius:20px; }}"
        )
        eff = QGraphicsDropShadowEffect(card)
        eff.setBlurRadius(40); eff.setOffset(0, 10)
        eff.setColor(QColor(15, 27, 45, 22))
        card.setGraphicsEffect(eff)

        cv = QVBoxLayout(card)
        cv.setContentsMargins(40, 44, 40, 44)
        cv.setSpacing(16)

        # App icon
        icon_wrap = QFrame(); icon_wrap.setFixedSize(64, 64)
        icon_wrap.setStyleSheet(f"background:{T.PRIMARY_SOFT}; border-radius:18px;")
        iw = QVBoxLayout(icon_wrap); iw.setContentsMargins(0, 0, 0, 0)
        iw.addWidget(IconLabel("building", T.PRIMARY, 36), 0, Qt.AlignCenter)
        cv.addWidget(icon_wrap, 0, Qt.AlignCenter)

        title = QLabel("Tenant Management System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{T.TEXT}; font-size:20px; font-weight:800;")
        title.setWordWrap(True)
        cv.addWidget(title)

        sub = QLabel("Manage your rental properties with ease")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:13px;")
        cv.addWidget(sub)
        cv.addSpacing(4)

        # ── Username field ──────────────────────────────────────────────────
        cv.addWidget(self._field_label("Username"))
        user_wrap = QFrame()
        user_wrap.setStyleSheet(self._wrap_style())
        ul = QHBoxLayout(user_wrap); ul.setContentsMargins(14, 0, 14, 0); ul.setSpacing(8)
        ul.addWidget(IconLabel("user", T.TEXT_SUBTLE, 18))
        # self.username_input = QLineEdit()
        self.username_input = QLineEdit("admin")  # Pre-fill for testing
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(48)
        self.username_input.setStyleSheet(self._input_style())
        ul.addWidget(self.username_input, 1)
        cv.addWidget(user_wrap)

        # ── Password field ──────────────────────────────────────────────────
        cv.addWidget(self._field_label("Password"))
        pw_wrap = QFrame()
        pw_wrap.setStyleSheet(self._wrap_style())
        pw_lay = QHBoxLayout(pw_wrap); pw_lay.setContentsMargins(14, 0, 10, 0); pw_lay.setSpacing(8)
        pw_lay.addWidget(IconLabel("lock", T.TEXT_SUBTLE, 18))
        # self.password_input = QLineEdit()
        self.password_input = QLineEdit("admin")  # Pre-fill for testing
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(48)
        self.password_input.setStyleSheet(self._input_style())
        pw_lay.addWidget(self.password_input, 1)
        self.show_pw_btn = QPushButton()
        self.show_pw_btn.setIcon(make_icon("eye", T.TEXT_SUBTLE, 18))
        self.show_pw_btn.setIconSize(QSize(18, 18))
        self.show_pw_btn.setFixedSize(36, 36)
        self.show_pw_btn.setCursor(Qt.PointingHandCursor)
        self.show_pw_btn.setStyleSheet(
            "QPushButton { border:none; background:transparent; border-radius:8px; }"
            "QPushButton:hover { background:#F0F4FF; }"
        )
        self.show_pw_btn.clicked.connect(self._toggle_password)
        pw_lay.addWidget(self.show_pw_btn)
        cv.addWidget(pw_wrap)

        # Remember me + forgot password
        opts = QHBoxLayout()
        self.remember_cb = QCheckBox("Remember me")
        self.remember_cb.setCursor(Qt.PointingHandCursor)
        self.remember_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {T.TEXT_MUTED};
                font-size: 13.5px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1.5px solid #94A3B8;
                border-radius: 3px;
                background: #FFFFFF;
            }}
            QCheckBox::indicator:hover {{
                border: 1.5px solid {T.PRIMARY};
            }}
            QCheckBox::indicator:checked {{
                background: #FFFFFF;
                border: 1.5px solid {T.PRIMARY};
                image: url(assets/check-black.svg);
            }}
        """)
        opts.addWidget(self.remember_cb)
        
        opts.addStretch(1)
        forgot = QLabel(
            f"<a href='#' style='color:{T.PRIMARY}; text-decoration:none;'>Forgot password?</a>"
        )
        forgot.setOpenExternalLinks(False)
        forgot.setStyleSheet("font-size:12.5px;")
        opts.addWidget(forgot)
        cv.addLayout(opts)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(
            f"color:{T.DANGER}; background:{T.DANGER_SOFT}; border-radius:8px;"
            f" padding:8px 14px; font-size:12.5px;"
        )
        self.error_lbl.hide()
        cv.addWidget(self.error_lbl)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background:{T.PRIMARY}; color:white; border:none;
                border-radius:13px; font-size:15px; font-weight:700;
            }}
            QPushButton:hover {{ background:{T.PRIMARY_DK}; }}
            QPushButton:pressed {{ background:{T.PRIMARY_DK}; }}
        """)
        self.login_btn.clicked.connect(self._handle_login)
        cv.addWidget(self.login_btn)

        # Enter key support
        self.username_input.returnPressed.connect(self._handle_login)
        self.password_input.returnPressed.connect(self._handle_login)

        rv.addWidget(card)
        outer.addWidget(right)

    # ── Style helpers ────────────────────────────────────────────────────────

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:600;")
        return lbl

    def _wrap_style(self) -> str:
        return (
            f"QFrame {{ background:{T.BG}; border:1.5px solid {T.BORDER}; border-radius:12px; }}"
            f"QFrame:focus-within {{ border:1.5px solid {T.PRIMARY}; }}"
        )

    def _input_style(self) -> str:
        return (
            f"QLineEdit {{ border:none; background:transparent;"
            f" color:{T.TEXT}; font-size:13.5px; }}"
        )

    # ── Interaction logic ────────────────────────────────────────────────────

    def _toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_pw_btn.setIcon(make_icon("eye_off", T.PRIMARY, 18))
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_pw_btn.setIcon(make_icon("eye", T.TEXT_SUBTLE, 18))

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username:
            self._show_error("Please enter your username.")
            return
        if not password:
            self._show_error("Please enter your password.")
            return

        # Verify user credentials using DB
        if validate_login(username, password):
            self.error_lbl.hide()
            self.login_success.emit(username)
        else:
            self._show_error("Invalid username or password.")

    def _show_error(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.show()

    def clear_fields(self):
        """Call this after logout to reset the form."""
        self.username_input.clear()
        self.password_input.clear()
        self.error_lbl.hide()
        self.username_input.setFocus()
