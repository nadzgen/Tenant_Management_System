from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


def add_shadow(widget, blur=24, y=6, alpha=18):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur); eff.setOffset(0, y); eff.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(eff)


class StatCard(QFrame):
    def __init__(self, label, value, hint, icon="📈", icon_bg="#eff6ff", icon_fg="#2563eb", trend=None):
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(130)
        add_shadow(self)

        outer = QVBoxLayout(self); outer.setContentsMargins(18, 16, 18, 16); outer.setSpacing(8)

        top = QHBoxLayout(); top.setSpacing(12)
        ic = QLabel(icon); ic.setObjectName("statIcon")
        ic.setStyleSheet(f"background:{icon_bg}; color:{icon_fg};")
        top.addWidget(ic)

        col = QVBoxLayout(); col.setSpacing(2)
        l = QLabel(label.upper()); l.setObjectName("statLabel")
        v = QLabel(value); v.setObjectName("statValue")
        col.addWidget(l); col.addWidget(v)
        top.addLayout(col); top.addStretch()

        if trend:
            tcolor = "#16a34a" if trend.startswith("↑") else "#dc2626"
            tbg = "#dcfce7" if trend.startswith("↑") else "#fee2e2"
            tl = QLabel(trend)
            tl.setStyleSheet(f"background:{tbg}; color:{tcolor}; padding:4px 10px; border-radius:10px; font-size:11px; font-weight:700;")
            top.addWidget(tl, alignment=Qt.AlignTop)
        outer.addLayout(top)

        h = QLabel(hint); h.setObjectName("statHint")
        outer.addWidget(h)


class Card(QFrame):
    """Generic white rounded card container."""
    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        add_shadow(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 18, 20, 18)
        self._layout.setSpacing(12)

    def layout(self):
        return self._layout
