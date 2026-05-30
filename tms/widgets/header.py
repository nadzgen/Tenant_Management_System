from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt


class Header(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("header")
        self.setFixedHeight(96)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 18, 32, 18)
        layout.setSpacing(16)

        left = QVBoxLayout(); left.setSpacing(2)
        self.title = QLabel("Dashboard"); self.title.setObjectName("pageTitle")
        self.crumb = QLabel("Home / Dashboard"); self.crumb.setObjectName("pageCrumb")
        left.addWidget(self.title); left.addWidget(self.crumb)
        layout.addLayout(left); layout.addStretch()

        self.search = QLineEdit()
        self.search.setObjectName("searchTop")
        self.search.setPlaceholderText("🔍   Search anything...")
        layout.addWidget(self.search)

        bell = QPushButton("🔔"); bell.setObjectName("bellBtn"); bell.setCursor(Qt.PointingHandCursor)
        layout.addWidget(bell)

        avatar = QLabel("A"); avatar.setObjectName("avatar")
        layout.addWidget(avatar)

    def set_title(self, title: str, subtitle: str):
        self.title.setText(title)
        self.crumb.setText(f"Home / {title}")
