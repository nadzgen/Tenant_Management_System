"""
widgets/components.py — Reusable UI building blocks
=====================================================
Every widget here is designed to be drop-in.  Import what you need; nothing
in this file has page-specific logic.
"""

from __future__ import annotations

import math
from typing import List

from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QPen, QBrush, QFont,
    QLinearGradient,
)
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QComboBox, QToolButton,
)

from icons import make_icon
from theme import T


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------

class Card(QFrame):
    """White rounded card with a subtle drop shadow."""

    def __init__(self, parent=None, radius: int = T.RADIUS, padding: int = 20):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(
            f"#Card {{ background:{T.SURFACE}; border:1px solid {T.BORDER};"
            f" border-radius:{radius}px; }}"
        )
        eff = QGraphicsDropShadowEffect(self)
        eff.setBlurRadius(28)
        eff.setOffset(0, 6)
        eff.setColor(QColor(15, 27, 45, 18))
        self.setGraphicsEffect(eff)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(padding, padding, padding, padding)
        lay.setSpacing(14)
        self.body = lay


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

class IconLabel(QLabel):
    """A QLabel that renders one SVG icon."""

    def __init__(self, name: str, color: str, size: int = 22, parent=None):
        super().__init__(parent)
        self.setPixmap(make_icon(name, color, size).pixmap(size, size))
        self.setFixedSize(size, size)


class SoftIconBadge(QFrame):
    """Rounded tinted square holding an icon (used in KPI cards)."""

    def __init__(self, icon: str, color: str, soft: str, size: int = 46, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet(f"background:{soft}; border-radius:12px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(IconLabel(icon, color, 24), 0, Qt.AlignCenter)


class DeltaPill(QLabel):
    """Small pill showing a percentage change with direction arrow."""

    def __init__(self, text: str, positive: bool = True, parent=None):
        super().__init__(parent)
        color = T.SUCCESS if positive else T.DANGER
        soft  = T.SUCCESS_SOFT if positive else T.DANGER_SOFT
        arrow = "↑" if positive else "↓"
        self.setText(f"  {arrow} {text}  ")
        self.setStyleSheet(
            f"background:{soft}; color:{color}; border-radius:10px;"
            f" padding:2px 8px; font-weight:600; font-size:11px;"
        )


class StatusBadge(QLabel):
    """Coloured pill for table status columns."""

    SCHEME = {
        "Paid":        (T.SUCCESS, T.SUCCESS_SOFT),
        "Unpaid":      (T.WARNING, T.WARNING_SOFT),
        "Overdue":     (T.DANGER,  T.DANGER_SOFT),
        "Occupied":    (T.SUCCESS, T.SUCCESS_SOFT),
        "Vacant":      (T.PRIMARY, T.PRIMARY_SOFT),
        "Maintenance": (T.WARNING, T.WARNING_SOFT),
    }

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        color, soft = self.SCHEME.get(status, (T.TEXT_MUTED, T.DIVIDER))
        self.setText(f"  {status}  ")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"background:{soft}; color:{color}; border-radius:10px;"
            f" padding:3px 8px; font-weight:600; font-size:12px;"
        )


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

class KPICard(Card):
    def __init__(self, title: str, value: str, icon: str, color: str,
                 soft: str, delta: str, delta_positive: bool = True,
                 caption: str = "", parent=None):
        super().__init__(parent, padding=22)
        self.setMinimumHeight(140)
        self.setMinimumWidth(240)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        top = QHBoxLayout(); top.setSpacing(14)
        top.addWidget(SoftIconBadge(icon, color, soft, 52))

        mid = QVBoxLayout(); mid.setSpacing(6)
        t = QLabel(title.upper())
        t.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:11px; font-weight:700; letter-spacing:0.8px;")
        v = QLabel(value)
        v.setStyleSheet(f"color:{T.TEXT}; font-size:26px; font-weight:700;")
        mid.addWidget(t); mid.addWidget(v)
        top.addLayout(mid, 1)
        top.addWidget(DeltaPill(delta, delta_positive), 0, Qt.AlignTop)
        self.body.addLayout(top)

        if caption:
            cap = QLabel(caption)
            cap.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12px;")
            self.body.addWidget(cap)
        self.body.addStretch(1)


class MiniInsightCard(Card):
    def __init__(self, label: str, value: str, icon: str, color: str, soft: str, parent=None):
        super().__init__(parent, padding=16)
        row = QHBoxLayout(); row.setSpacing(12)
        row.addWidget(SoftIconBadge(icon, color, soft, 40))
        col = QVBoxLayout(); col.setSpacing(2)
        lbl = QLabel(label); lbl.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12px;")
        val = QLabel(value);  val.setStyleSheet(f"color:{T.TEXT}; font-size:16px; font-weight:700;")
        col.addWidget(lbl); col.addWidget(val)
        row.addLayout(col, 1)
        self.body.addLayout(row)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

class LineChart(QWidget):
    """Custom-painted smooth line/area chart — no external chart library."""

    def __init__(self, values: List[float], labels: List[str], parent=None):
        super().__init__(parent)
        self.values = values
        self.labels = labels
        self.setMinimumHeight(260)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 56, 18, 16, 36
        cw, ch = w - ml - mr, h - mt - mb
        if cw <= 0 or ch <= 0:
            return

        vmin = 0
        vmax = max(self.values) * 1.15 or 1

        # Grid lines & Y labels
        p.setFont(QFont("Segoe UI", 8))
        steps = 4
        for i in range(steps + 1):
            y = mt + ch * i / steps
            p.setPen(QPen(QColor(T.DIVIDER), 1))
            p.drawLine(ml, int(y), ml + cw, int(y))
            val = vmax - (vmax - vmin) * i / steps
            p.setPen(QColor(T.TEXT_MUTED))
            lbl = f"₱{int(val/1000)}K" if val >= 1000 else f"₱{int(val)}"
            p.drawText(QRectF(0, y - 8, ml - 6, 16), Qt.AlignRight | Qt.AlignVCenter, lbl)

        # X labels & point coords
        n = len(self.values)
        xs = [ml + cw * i / max(n - 1, 1) for i in range(n)]
        ys = [mt + ch * (1 - (v - vmin) / (vmax - vmin)) for v in self.values]
        p.setPen(QColor(T.TEXT_MUTED))
        for x, lbl in zip(xs, self.labels):
            p.drawText(QRectF(x - 20, mt + ch + 6, 40, 18), Qt.AlignHCenter | Qt.AlignTop, lbl)

        # Area fill
        path = QPainterPath(); path.moveTo(xs[0], mt + ch)
        for x, y in zip(xs, ys): path.lineTo(x, y)
        path.lineTo(xs[-1], mt + ch); path.closeSubpath()
        grad = QLinearGradient(0, mt, 0, mt + ch)
        grad.setColorAt(0, QColor(44, 107, 255, 70))
        grad.setColorAt(1, QColor(44, 107, 255, 0))
        p.fillPath(path, QBrush(grad))

        # Line
        p.setPen(QPen(QColor(T.PRIMARY), 2.4))
        for i in range(n - 1):
            p.drawLine(QPointF(xs[i], ys[i]), QPointF(xs[i + 1], ys[i + 1]))

        # Dots
        for x, y in zip(xs, ys):
            p.setBrush(QColor(T.SURFACE))
            p.setPen(QPen(QColor(T.PRIMARY), 2))
            p.drawEllipse(QPointF(x, y), 3.6, 3.6)


class DonutChart(QWidget):
    """Simple donut chart — segments: [(label, value, color)]."""

    def __init__(self, segments: List[tuple], parent=None):
        super().__init__(parent)
        self.segments = segments
        self.setMinimumSize(200, 200)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        size = min(w, h) - 20
        rect = QRectF((w - size) / 2, (h - size) / 2, size, size)
        total = sum(v for _, v, _ in self.segments) or 1
        start = 90 * 16
        for _, value, color in self.segments:
            span = -int(360 * 16 * value / total)
            p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
            p.drawPie(rect, start, span)
            mid_angle = (start + span / 2) / 16
            rad = math.radians(mid_angle)
            r = size * 0.34
            cx = rect.center().x() + r * math.cos(rad)
            cy = rect.center().y() - r * math.sin(rad)
            p.setPen(QColor("white"))
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            pct = round(value / total * 100)
            p.drawText(QRectF(cx - 25, cy - 10, 50, 20), Qt.AlignCenter, f"{pct}%")
            start += span

        hole = size * 0.55
        hrect = QRectF(rect.center().x() - hole / 2, rect.center().y() - hole / 2, hole, hole)
        p.setBrush(QColor(T.SURFACE)); p.setPen(Qt.NoPen)
        p.drawEllipse(hrect)


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def styled_table(columns: list[str]) -> QTableWidget:
    """Create a pre-styled, read-only table with the given column headers."""
    tbl = QTableWidget(0, len(columns))
    tbl.setHorizontalHeaderLabels(columns)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.setAlternatingRowColors(True)
    tbl.verticalHeader().setVisible(False)
    tbl.setShowGrid(False)
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    tbl.setStyleSheet(f"""
        QTableWidget {{
            background:{T.SURFACE}; border:none;
            alternate-background-color:{T.BG};
            gridline-color:{T.DIVIDER};
            color:{T.TEXT}; font-size:13px;
        }}
        QTableWidget::item {{ padding:10px 14px; border:none; }}
        QTableWidget::item:selected {{
            background:{T.PRIMARY_SOFT}; color:{T.PRIMARY};
        }}
        QHeaderView::section {{
            background:{T.BG}; color:{T.TEXT_MUTED};
            font-size:11px; font-weight:700;
            letter-spacing:0.6px; padding:10px 14px;
            border:none; border-bottom:2px solid {T.BORDER};
        }}
    """)
    tbl.setFocusPolicy(Qt.NoFocus)
    return tbl


def set_table_item(tbl: QTableWidget, row: int, col: int, text: str):
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    tbl.setItem(row, col, item)


def set_badge_cell(tbl: QTableWidget, row: int, col: int, status: str):
    """Embed a StatusBadge widget inside a table cell."""
    badge = StatusBadge(status)
    wrap = QWidget(); lay = QHBoxLayout(wrap)
    lay.setContentsMargins(8, 4, 8, 4)
    lay.addWidget(badge, 0, Qt.AlignLeft)
    tbl.setCellWidget(row, col, wrap)


# ---------------------------------------------------------------------------
# Search bar
# ---------------------------------------------------------------------------

def search_bar(placeholder: str = "Search…") -> QLineEdit:
    le = QLineEdit()
    le.setPlaceholderText(placeholder)
    le.setFixedHeight(42)
    le.setStyleSheet(f"""
        QLineEdit {{
            background:{T.SURFACE}; border:1px solid {T.BORDER};
            border-radius:10px; padding:0 14px 0 42px;
            color:{T.TEXT}; font-size:13.5px;
        }}
        QLineEdit:focus {{ border:1.5px solid {T.PRIMARY}; }}
    """)
    return le


# ---------------------------------------------------------------------------
# Section title
# ---------------------------------------------------------------------------

def section_title(text: str, subtitle: str = "") -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(2)
    t = QLabel(text); t.setStyleSheet(f"color:{T.PRIMARY}; font-size:15px; font-weight:700;")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12.5px;")
        lay.addWidget(s)
    return w


# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------

def primary_button(label: str, icon_name: str = "") -> QPushButton:
    btn = QPushButton()
    if icon_name:
        btn.setIcon(make_icon(icon_name, "white", 16))
        btn.setIconSize(QSize(16, 16))
    btn.setText(f"  {label}")
    btn.setFixedHeight(40)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{T.PRIMARY}; color:white; border:none;
            border-radius:10px; padding:0 18px;
            font-size:13px; font-weight:600;
        }}
        QPushButton:hover {{ background:{T.PRIMARY_DK}; }}
        QPushButton:pressed {{ background:{T.PRIMARY_DK}; }}
    """)
    return btn


def ghost_button(label: str, icon_name: str = "", color: str = T.TEXT) -> QPushButton:
    btn = QPushButton()
    if icon_name:
        btn.setIcon(make_icon(icon_name, color, 16))
        btn.setIconSize(QSize(16, 16))
    btn.setText(f"  {label}")
    btn.setFixedHeight(38)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:transparent; color:{color}; border:1.5px solid {T.BORDER};
            border-radius:10px; padding:0 16px;
            font-size:13px; font-weight:500;
        }}
        QPushButton:hover {{ background:{T.BG}; border-color:{color}; }}
    """)
    return btn


def danger_button(label: str, icon_name: str = "") -> QPushButton:
    btn = QPushButton()
    if icon_name:
        btn.setIcon(make_icon(icon_name, T.DANGER, 16))
        btn.setIconSize(QSize(16, 16))
    btn.setText(f"  {label}")
    btn.setFixedHeight(38)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{T.DANGER_SOFT}; color:{T.DANGER}; border:none;
            border-radius:10px; padding:0 16px;
            font-size:13px; font-weight:600;
        }}
        QPushButton:hover {{ background:{T.DANGER}; color:white; }}
    """)
    return btn
