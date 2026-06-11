"""
widgets/components.py — Reusable UI building blocks
=====================================================
Every widget here is designed to be drop-in.  Import what you need; nothing
in this file has page-specific logic.
"""

from __future__ import annotations

import math
from typing import List

from PySide6.QtCore import Qt, QRectF, QPointF, QSize, Signal
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

        self.setStyleSheet("background:transparent; border:none;")

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
        "Full":        (T.SUCCESS, T.SUCCESS_SOFT),
        "Partially Occupied": (T.PURPLE, T.PURPLE_SOFT),
        "Vacant":      (T.PRIMARY, T.PRIMARY_SOFT)
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
        
        # Calculate midpoint radius of the donut ring
        # Outer radius = 0.5 * size
        # Inner radius (hole) = 0.55 * size / 2 = 0.275 * size
        # Midpoint = (0.5 + 0.275) / 2 = 0.3875
        label_radius = size * 0.3875
        font_size = max(8, min(12, int(size * 0.045)))
        p.setFont(QFont("Segoe UI", font_size, QFont.Bold))

        for _, value, color in self.segments:
            span = -int(360 * 16 * value / total)
            p.setBrush(QColor(color)); p.setPen(Qt.NoPen)
            p.drawPie(rect, start, span)
            
            if value > 0:
                pct = (value / total) * 100
                if pct >= 5:  # Hide labels for very small slices
                    mid_angle = (start + span / 2) / 16
                    rad = math.radians(mid_angle)
                    cx = rect.center().x() + label_radius * math.cos(rad)
                    cy = rect.center().y() - label_radius * math.sin(rad)
                    
                    p.setPen(QColor("white"))
                    p.drawText(QRectF(cx - 25, cy - 10, 50, 20), Qt.AlignCenter, f"{round(pct)}%")
            start += span

        hole = size * 0.55
        hrect = QRectF(rect.center().x() - hole / 2, rect.center().y() - hole / 2, hole, hole)
        p.setBrush(QColor(T.SURFACE)); p.setPen(Qt.NoPen)
        p.drawEllipse(hrect)


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def styled_table(columns: list[str]) -> QTableWidget:
    """Create a pre‑styled, read‑only table with uniform visual layout."""

    # Base table
    tbl = QTableWidget(0, len(columns))
    tbl.setHorizontalHeaderLabels(columns)

    # ==== Interaction ====
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.setSelectionMode(QTableWidget.SingleSelection)

    # ==== Row / column geometry ====
    tbl.setAlternatingRowColors(True)
    tbl.verticalHeader().setVisible(False)
    tbl.verticalHeader().setDefaultSectionSize(44)          # uniform row height
    tbl.setShowGrid(False)

    # Balance column widths evenly for a uniform appearance
    header = tbl.horizontalHeader()
    for i in range(tbl.columnCount()):
        header.setSectionResizeMode(i, QHeaderView.Stretch)
    header.setMinimumSectionSize(80)  # ensure columns aren't too narrow
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setHighlightSections(False)
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(False)



    # ==== Scrolling ====
    tbl.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
    tbl.setVerticalScrollMode(QTableWidget.ScrollPerPixel)

    # ==== Focus ====
    tbl.setFocusPolicy(Qt.NoFocus)
    tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    tbl.setStyleSheet(f"""
        QTableWidget {{
            background:{T.SURFACE};
            border:none;
            alternate-background-color:{T.BG};
            color:{T.TEXT};
            font-size:13px;
            outline: none;
            show-decoration-selected: 1;
        }}

        QTableWidget::item {{
            padding-left:16px;
            padding-right:16px;
            border-bottom:1px solid {T.BORDER};
        }}

        QTableWidget::item:selected, QTableWidget::item:selected:!active {{
            background:{T.PRIMARY_SOFT};
            color:{T.PRIMARY};
        }}

        QHeaderView::section {{
            background:{T.BG};
            color:{T.TEXT_MUTED};
            font-size:11px;
            font-weight:700;
            padding-left:16px;
            padding-right:16px;
            padding-top:12px;
            padding-bottom:12px;
            border:none;
            border-bottom:1px solid {T.BORDER};
        }}

        /* Modern Scrollbar Vertical */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {T.TEXT_SUBTLE};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {T.TEXT_MUTED};
        }}
        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{
            height: 0px;
            background: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}

        /* Modern Scrollbar Horizontal */
        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0px 0px 0px 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: {T.TEXT_SUBTLE};
            min-width: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {T.TEXT_MUTED};
        }}
        QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{
            width: 0px;
            background: none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """)

    return tbl


def set_table_item(tbl: QTableWidget, row: int, col: int, text: str):
    item = QTableWidgetItem(str(text))
    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    tbl.setItem(row, col, item)


def set_badge_cell(tbl: QTableWidget, row: int, col: int, status: str):
    """Embed a StatusBadge widget inside a table cell."""

    badge = StatusBadge(status)
    badge.setAttribute(Qt.WA_TransparentForMouseEvents)

    wrap = QWidget()
    wrap.setAttribute(Qt.WA_TransparentForMouseEvents)
    wrap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    lay = QHBoxLayout(wrap)
    # Center the badge within the cell with balanced horizontal margins
    lay.setContentsMargins(16, 0, 16, 0)
    lay.setAlignment(Qt.AlignCenter)
    
    lay.addWidget(badge)

    tbl.setCellWidget(row, col, wrap)

    # Programmatically ensure the column header is also centered
    header_item = tbl.horizontalHeaderItem(col)
    if header_item:
        header_item.setTextAlignment(Qt.AlignCenter)


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


def dropdown_filter(options: list[str]) -> QComboBox:
    """Create a styled dropdown combo box for table filtering."""
    cb = QComboBox()
    cb.addItems(options)
    cb.setFixedHeight(42)
    cb.setStyleSheet(f"""
        QComboBox {{
            background:{T.SURFACE}; border:1px solid {T.BORDER};
            border-radius:10px; padding:0 14px;
            color:{T.TEXT}; font-size:13px; font-weight:500;
        }}
        QComboBox::drop-down {{ border:none; padding-right:10px; }}
        QComboBox:hover {{ border-color:{T.PRIMARY_SOFT}; }}
    """)
    cb.setCursor(Qt.PointingHandCursor)
    return cb

def filter_button(title="Filter") -> QPushButton:
    """Create a modern filter button intended to spawn a QMenu."""
    btn = QPushButton(f"  {title}")
    btn.setIcon(make_icon("filter", T.TEXT_MUTED, 16))
    btn.setFixedHeight(42)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {T.SURFACE};
            border: 1px solid {T.BORDER};
            border-radius: 10px;
            padding: 0 16px;
            color: {T.TEXT_MUTED};
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            border-color: {T.PRIMARY_SOFT};
            color: {T.TEXT};
        }}
        QPushButton::menu-indicator {{
            image: none;
        }}
    """)
    return btn


class MonthPicker(QWidget):
    """Modern SaaS-style month picker with a subtle, clean design."""
    month_changed = Signal(str)  # emits "YYYY-MM"

    MONTH_NAMES = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    def __init__(self, initial_month: str = "", parent=None):
        super().__init__(parent)
        if not initial_month:
            from datetime import date
            initial_month = date.today().strftime("%Y-%m")
        parts = initial_month.split("-")
        self._year = int(parts[0])
        self._month = int(parts[1])
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        wrap = QFrame()
        wrap.setFixedHeight(40)
        wrap.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER};
                border-radius: 8px;
            }}
        """)
        inner = QHBoxLayout(wrap)
        inner.setContentsMargins(4, 0, 4, 0)
        inner.setSpacing(0)

        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {T.BG};
            }}
        """

        # ── Left arrows ──
        self._prev_year = QPushButton()
        self._prev_year.setIcon(make_icon("chevrons-left", T.TEXT_MUTED, 16))
        self._prev_year.setFixedSize(20, 26)
        self._prev_year.setCursor(Qt.PointingHandCursor)
        self._prev_year.setToolTip("Previous year")
        self._prev_year.setStyleSheet(btn_style)
        self._prev_year.clicked.connect(self._go_prev_year)

        self._prev = QPushButton()
        self._prev.setIcon(make_icon("chevron-left", T.TEXT_MUTED, 16))
        self._prev.setFixedSize(20, 26)
        self._prev.setCursor(Qt.PointingHandCursor)
        self._prev.setToolTip("Previous month")
        self._prev.setStyleSheet(btn_style)
        self._prev.clicked.connect(self._go_prev)

        # ── Center Area (Icon + Text) ──
        center_lay = QHBoxLayout()
        center_lay.setContentsMargins(8, 0, 8, 0)
        center_lay.setSpacing(6)
        
        cal_icon = QLabel()
        cal_icon.setPixmap(make_icon("calendar", T.TEXT_MUTED, 14).pixmap(14, 14))
        cal_icon.setFixedSize(14, 14)
        cal_icon.setAlignment(Qt.AlignCenter)
        center_lay.addWidget(cal_icon)

        self._month_lbl = QLabel()
        self._month_lbl.setStyleSheet(f"""
            color: {T.TEXT_MUTED};
            font-size: 13px;
            font-weight: 500;
            border: none;
            background: transparent;
        """)
        center_lay.addWidget(self._month_lbl)
        
        # ── Right arrow ──
        self._next = QPushButton()
        self._next.setIcon(make_icon("chevron-right", T.TEXT_MUTED, 16))
        self._next.setFixedSize(20, 26)
        self._next.setCursor(Qt.PointingHandCursor)
        self._next.setToolTip("Next month")
        self._next.setStyleSheet(btn_style)
        self._next.clicked.connect(self._go_next)

        self._next_year = QPushButton()
        self._next_year.setIcon(make_icon("chevrons-right", T.TEXT_MUTED, 16))
        self._next_year.setFixedSize(20, 26)
        self._next_year.setCursor(Qt.PointingHandCursor)
        self._next_year.setToolTip("Next year")
        self._next_year.setStyleSheet(btn_style)
        self._next_year.clicked.connect(self._go_next_year)

        inner.addWidget(self._prev_year)
        inner.addWidget(self._prev)
        inner.addLayout(center_lay)
        inner.addWidget(self._next)
        inner.addWidget(self._next_year)

        lay.addWidget(wrap)
        self._update_label()

    def _update_label(self):
        self._month_lbl.setText(f"{self.MONTH_NAMES[self._month - 1]} {self._year}")

    def _go_prev(self):
        self._month -= 1
        if self._month < 1:
            self._month = 12
            self._year -= 1
        self._update_label()
        self.month_changed.emit(self.value())

    def _go_next(self):
        self._month += 1
        if self._month > 12:
            self._month = 1
            self._year += 1
        self._update_label()
        self.month_changed.emit(self.value())

    def _go_prev_year(self):
        self._year -= 1
        self._update_label()
        self.month_changed.emit(self.value())

    def _go_next_year(self):
        self._year += 1
        self._update_label()
        self.month_changed.emit(self.value())

    def value(self) -> str:
        return f"{self._year:04d}-{self._month:02d}"


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


# ---------------------------------------------------------------------------
# Pagination Control
# ---------------------------------------------------------------------------

class PaginationControl(QWidget):
    page_changed = Signal(int)
    items_per_page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.total_pages = 1
        self.items_per_page = 20

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        
        self.lbl_info = QLabel("Page 1 of 1")
        self.lbl_info.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:13px; font-weight:500;")
        
        btn_style = f"""
            QPushButton {{
                background: {T.SURFACE}; color: {T.TEXT}; border: 1.5px solid {T.BORDER};
                border-radius: 8px; padding: 0 16px; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {T.BG}; border-color: {T.PRIMARY}; color: {T.PRIMARY}; }}
            QPushButton:disabled {{ color: {T.TEXT_MUTED}; border-color: {T.DIVIDER}; background: {T.BG}; }}
        """

        self.btn_prev = QPushButton("‹  Prev")
        self.btn_prev.setFixedHeight(34)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet(btn_style)
        self.btn_prev.clicked.connect(self._on_prev)
        
        self.btn_next = QPushButton("Next  ›")
        self.btn_next.setFixedHeight(34)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet(btn_style)
        self.btn_next.clicked.connect(self._on_next)
        
        lay.addStretch(1)
        lay.addWidget(self.lbl_info)
        lay.addSpacing(8)
        lay.addWidget(self.btn_prev)
        lay.addWidget(self.btn_next)
        
        self._update_ui()

    def set_total_items(self, total_items: int):
        import math
        self.total_pages = max(1, math.ceil(total_items / self.items_per_page))
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        self._update_ui()

    def _on_prev(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._update_ui()
            self.page_changed.emit(self.current_page)

    def _on_next(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_ui()
            self.page_changed.emit(self.current_page)

    def _update_ui(self):
        self.lbl_info.setText(f"Page {self.current_page} of {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

def table_action_cell(on_edit, on_delete) -> QWidget:
    """Create a cell containing modern Edit and Delete icon buttons."""
    wrap = QWidget()
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(16, 0, 16, 0)
    lay.setSpacing(8)
    lay.setAlignment(Qt.AlignCenter)
    
    # Edit button
    edit_btn = QPushButton()
    edit_btn.setIcon(make_icon("edit", T.TEXT, 16))
    edit_btn.setFixedSize(30, 30)
    edit_btn.setCursor(Qt.PointingHandCursor)
    edit_btn.setToolTip("Edit")
    edit_btn.setStyleSheet(f"""
        QPushButton {{ background:transparent; border-radius:15px; border:none; }}
        QPushButton:hover {{ background:{T.PRIMARY_SOFT}; }}
    """)
    if on_edit: edit_btn.clicked.connect(on_edit)
    
    # Delete button
    del_btn = QPushButton()
    del_btn.setIcon(make_icon("trash", T.DANGER, 16))
    del_btn.setFixedSize(30, 30)
    del_btn.setCursor(Qt.PointingHandCursor)
    del_btn.setToolTip("Delete")
    del_btn.setStyleSheet(f"""
        QPushButton {{ background:transparent; border-radius:15px; border:none; }}
        QPushButton:hover {{ background:{T.DANGER_SOFT}; }}
    """)
    if on_delete: del_btn.clicked.connect(on_delete)
    
    lay.addWidget(edit_btn)
    lay.addWidget(del_btn)
    
    return wrap

def update_table_headers(tbl: QTableWidget, sort_col: int, sort_order: Qt.SortOrder):
    for i in range(tbl.columnCount()):
        item = tbl.horizontalHeaderItem(i)
        if not item or item.text() == "Action": continue
        if i == sort_col:
            icon_name = "sort-up" if sort_order == Qt.AscendingOrder else "sort-down"
            item.setIcon(make_icon(icon_name, "transparent", 18))
        else:
            item.setIcon(make_icon("sort-neutral", "transparent", 18))
