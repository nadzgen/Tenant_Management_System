"""Reusable page scaffold: scrollable content with consistent padding."""
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel


class PageBase(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(2 - 2)  # default
        inner = QWidget(); inner.setObjectName("pageContent")
        self.body = QVBoxLayout(inner)
        self.body.setContentsMargins(32, 24, 32, 32)
        self.body.setSpacing(18)
        self.setWidget(inner)

    def add_section_title(self, title, subtitle=None):
        t = QLabel(title); t.setObjectName("sectionTitle")
        self.body.addWidget(t)
        if subtitle:
            s = QLabel(subtitle); s.setObjectName("sectionSub")
            self.body.addWidget(s)
