from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                QButtonGroup, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt


NAV_ITEMS = [
    ("🏠", "Dashboard"),
    ("👥", "Tenant Management"),
    ("🚪", "Room Management"),
    ("💳", "Payment Tracking"),
    ("📊", "Reports & Analytics"),
    ("⚙️", "Settings"),
]


class Sidebar(QFrame):
    def __init__(self, on_navigate, on_logout):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(250)
        self._on_navigate = on_navigate

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(14)

        # Brand
        brand = QHBoxLayout()
        brand.setSpacing(10)
        logo = QLabel("🏢")
        logo.setStyleSheet("font-size: 28px;")
        bcol = QVBoxLayout(); bcol.setSpacing(0)
        t = QLabel("TMS"); t.setObjectName("brandTitle")
        s = QLabel("Tenant Management System"); s.setObjectName("brandSub")
        bcol.addWidget(t); bcol.addWidget(s)
        brand.addWidget(logo); brand.addLayout(bcol); brand.addStretch()
        layout.addLayout(brand)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#e2e8f0;")
        layout.addWidget(sep)

        # Nav
        self.group = QButtonGroup(self); self.group.setExclusive(True)
        self.buttons = []
        for i, (icon, label) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, idx=i: self._on_navigate(idx))
            self.group.addButton(btn, i)
            layout.addWidget(btn)
            self.buttons.append(btn)
        self.buttons[0].setChecked(True)

        layout.addStretch(1)

        # Logout
        logout = QPushButton("  ➜   Logout")
        logout.setObjectName("logoutBtn")
        logout.setCursor(Qt.PointingHandCursor)
        logout.clicked.connect(on_logout)
        layout.addWidget(logout)

        # Tip card
        tip = QFrame(); tip.setObjectName("sidebarTip")
        tl = QVBoxLayout(tip); tl.setSpacing(2)
        tt = QLabel("Manage your properties"); tt.setObjectName("tipTitle")
        ts = QLabel("with ease and clarity."); ts.setObjectName("tipSub")
        tl.addWidget(tt); tl.addWidget(ts)
        layout.addWidget(tip)

        # Footer
        foot = QLabel("v1.0.0   •   © 2025 TMS")
        foot.setStyleSheet("color:#94a3b8; font-size:11px;")
        foot.setAlignment(Qt.AlignCenter)
        layout.addWidget(foot)

    def set_active(self, index: int):
        self.buttons[index].setChecked(True)
