from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                                QPushButton, QFrame, QCheckBox, QMessageBox)
from PySide6.QtCore import Qt
from tms.widgets.cards import add_shadow


class LoginPage(QWidget):
    def __init__(self, on_login):
        super().__init__()
        self.on_login = on_login
        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Left hero
        left = QWidget(); left.setObjectName("loginLeft")
        ll = QVBoxLayout(left); ll.setContentsMargins(70, 70, 70, 70); ll.setSpacing(18)
        logo = QLabel("🏢"); logo.setStyleSheet("background:white; border-radius:20px; font-size:48px; padding:18px; min-width:80px; max-width:80px; min-height:80px; max-height:80px;")
        logo.setAlignment(Qt.AlignCenter)
        ll.addWidget(logo)
        ll.addSpacing(20)
        title = QLabel("Run your rentals\nwith confidence."); title.setObjectName("loginHeroTitle")
        sub = QLabel("Track tenants, rooms and payments in one calm,\nmodern workspace built for landlords.")
        sub.setObjectName("loginHeroSub")
        ll.addWidget(title); ll.addWidget(sub)
        ll.addSpacing(20)
        for icon, t, s in [
            ("👥", "Tenant directory", "Names, contacts and move-in dates at a glance."),
            ("🚪", "Room overview",   "See which rooms are occupied, vacant or in maintenance."),
            ("💳", "Payment tracking", "Know who has paid and what's still due this month."),
        ]:
            ll.addWidget(self._feature(icon, t, s))
        ll.addStretch()
        root.addWidget(left, 1)

        # Right form
        right = QWidget(); right.setObjectName("loginRight")
        rl = QVBoxLayout(right); rl.setContentsMargins(60, 60, 60, 60)
        rl.addStretch()

        card = QFrame(); card.setObjectName("loginCard"); card.setMaximumWidth(440)
        add_shadow(card, blur=40, y=8, alpha=30)
        cl = QVBoxLayout(card); cl.setContentsMargins(36, 36, 36, 36); cl.setSpacing(14)

        brand = QHBoxLayout(); brand.setSpacing(8); brand.addStretch()
        brand.addWidget(QLabel("🏢", styleSheet="font-size:28px; color:#2563eb;"))
        bt = QLabel("TMS"); bt.setStyleSheet("font-size:30px; font-weight:800; color:#2563eb;")
        brand.addWidget(bt); brand.addStretch()
        cl.addLayout(brand)

        h = QLabel("Tenant Management System"); h.setAlignment(Qt.AlignCenter)
        h.setStyleSheet("font-size:20px; font-weight:800;")
        sh = QLabel("Manage your rental properties with ease.")
        sh.setAlignment(Qt.AlignCenter); sh.setStyleSheet("color:#64748b; font-size:12px;")
        cl.addWidget(h); cl.addWidget(sh)
        cl.addSpacing(8)

        cl.addWidget(QLabel("Username", objectName="formLabel"))
        self.user = QLineEdit(); self.user.setPlaceholderText("👤   Enter your username")
        cl.addWidget(self.user)

        cl.addWidget(QLabel("Password", objectName="formLabel"))
        self.pwd = QLineEdit(); self.pwd.setPlaceholderText("🔒   Enter your password"); self.pwd.setEchoMode(QLineEdit.Password)
        cl.addWidget(self.pwd)

        opts = QHBoxLayout()
        opts.addWidget(QCheckBox("Remember me"))
        opts.addStretch()
        fb = QPushButton("Forgot password?"); fb.setObjectName("linkBtn"); fb.setCursor(Qt.PointingHandCursor)
        opts.addWidget(fb)
        cl.addLayout(opts)

        signin = QPushButton("Sign In"); signin.setObjectName("heroBtn"); signin.setCursor(Qt.PointingHandCursor)
        signin.clicked.connect(self._submit)
        cl.addWidget(signin)

        tip = QLabel("Tip: use any non-empty username and password to continue (demo).")
        tip.setObjectName("loginTip"); tip.setAlignment(Qt.AlignCenter); tip.setWordWrap(True)
        cl.addWidget(tip)

        rl.addWidget(card, alignment=Qt.AlignCenter)
        rl.addStretch()
        root.addWidget(right, 1)

        # Enter to submit
        self.pwd.returnPressed.connect(self._submit)
        self.user.returnPressed.connect(self._submit)

    def _feature(self, icon, title, sub):
        f = QFrame(); f.setObjectName("loginFeature")
        h = QHBoxLayout(f); h.setContentsMargins(16, 14, 16, 14); h.setSpacing(14)
        ic = QLabel(icon); ic.setStyleSheet("background:white; border-radius:12px; min-width:42px; min-height:42px; font-size:20px;"); ic.setAlignment(Qt.AlignCenter)
        h.addWidget(ic)
        c = QVBoxLayout(); c.setSpacing(2)
        t = QLabel(title); t.setStyleSheet("font-weight:700; font-size:14px;")
        s = QLabel(sub); s.setStyleSheet("color:#64748b; font-size:12px;")
        c.addWidget(t); c.addWidget(s); h.addLayout(c); h.addStretch()
        return f

    def _submit(self):
        if not self.user.text().strip() or not self.pwd.text().strip():
            QMessageBox.warning(self, "Sign In", "Please enter both username and password.")
            return
        # TODO: validate against SQLite users table
        self.on_login()
