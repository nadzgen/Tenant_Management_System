"""
pages/reports.py — Reports & Analytics page
============================================
Full visual analytics dashboard with charts, KPIs, and insight cards.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListView,
    QScrollArea, QFrame, QGridLayout,
)

from theme import T
from database.repositories import (
    get_dashboard_stats, get_revenue_monthly, get_revenue_labels,
)
from widgets.components import (
    Card, KPICard, MiniInsightCard, LineChart, DonutChart,
    section_title,
)


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self._build()

    def refresh(self):
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self.main_layout.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28); root.setSpacing(22)

        # Load all stats from the database
        current_month   = QDate.currentDate().toString("yyyy-MM")
        stats           = get_dashboard_stats(current_month)
        revenue_monthly = get_revenue_monthly()
        revenue_labels  = get_revenue_labels()

        paid_count    = stats["paid_count"]
        unpaid_count  = stats["unpaid_count"]
        overdue_count = stats["overdue_count"]
        occupied_rooms = stats["occupied_rooms"]
        vacant_units   = stats["vacant_units"]
        total_rooms    = stats["total_rooms"] or 1
        total_revenue  = stats["total_revenue"]
        maint          = 0  # No maintenance status in current schema

        occupancy_rate = f"{round(occupied_rooms / total_rooms * 100)}%"

        # ── Overview KPIs ────────────────────────────────────────────────────
        root.addWidget(section_title("Overview", "High-level performance at a glance"))
        kpis = QHBoxLayout(); kpis.setSpacing(20)
        kpis.addWidget(KPICard("Monthly Revenue",  f"₱ {int(total_revenue):,}", "wallet",
                               T.PRIMARY, T.PRIMARY_SOFT, "", True,  "Collected this month"))
        kpis.addWidget(KPICard("Occupancy Rate",   occupancy_rate,  "home",
                               T.SUCCESS, T.SUCCESS_SOFT, "",  True,  "Across all units"))
        kpis.addWidget(KPICard("Occupied Rooms", str(occupied_rooms), "home",
                               T.SUCCESS, T.SUCCESS_SOFT, "", True, "Currently housed"))
        root.addLayout(kpis)

        # ── Revenue trend ────────────────────────────────────────────────────
        root.addWidget(section_title("Revenue Trend", "Monthly income over the year"))
        trend = Card(padding=22)
        head = QHBoxLayout()
        th = QLabel("Revenue Trend — 2025")
        th.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        head.addWidget(th); head.addStretch(1)
        from widgets.components import CleanComboBox
        period = CleanComboBox(["This Year", "Last 6 Months", "This Month"])
        period.setStyleSheet(f"""
            QPushButton {{
                background: {T.BG};
                border: 1px solid {T.BORDER};
                border-radius: 8px;
                padding: 5px 24px 5px 10px;
                color: {T.TEXT};
                font-size: 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                border-color: {T.PRIMARY_SOFT};
            }}
            QPushButton::menu-indicator {{
                image: url(assets/chevron-down.svg);
                subcontrol-origin: padding;
                subcontrol-position: right center;
                padding-right: 8px;
                width: 14px;
                height: 14px;
            }}
        """)
        head.addWidget(period)
        trend.body.addLayout(head)
        trend.body.addWidget(LineChart(revenue_monthly, revenue_labels))
        root.addWidget(trend)

        # ── Charts row: donut + occupancy ────────────────────────────────────
        root.addWidget(section_title("Breakdown", "Payment status and occupancy overview"))
        charts_row = QHBoxLayout(); charts_row.setSpacing(20)

        # Payment donut
        donut_card = Card(padding=22)
        dh = QLabel("Payment Status Breakdown")
        dh.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        donut_card.body.addWidget(dh)
        d_row = QHBoxLayout(); d_row.setSpacing(20)
        d_row.addWidget(DonutChart([
            ("Paid",    paid_count,    T.SUCCESS),
            ("Unpaid",  unpaid_count,  T.WARNING),
            ("Overdue", overdue_count, T.DANGER),
        ]), 1)
        legend = QVBoxLayout(); legend.setSpacing(14)
        total_p = (paid_count + unpaid_count + overdue_count) or 1
        for label, count, color in [
            ("Paid",    paid_count,    T.SUCCESS),
            ("Unpaid",  unpaid_count,  T.WARNING),
            ("Overdue", overdue_count, T.DANGER),
        ]:
            pct = round(count / total_p * 100)
            row = QHBoxLayout(); row.setSpacing(10)
            dot = QFrame(); dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{color}; border-radius:5px;")
            row.addWidget(dot)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:500;")
            row.addWidget(lbl); row.addStretch(1)
            val = QLabel(f"{pct}%  ({count})")
            val.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12.5px;")
            row.addWidget(val)
            legend.addLayout(row)
        legend.addStretch(1)
        d_row.addLayout(legend, 1)
        donut_card.body.addLayout(d_row)
        charts_row.addWidget(donut_card, 1)

        # Occupancy donut
        occ_card = Card(padding=22)
        oh = QLabel("Room Occupancy Breakdown")
        oh.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        occ_card.body.addWidget(oh)
        o_row = QHBoxLayout(); o_row.setSpacing(20)
        o_row.addWidget(DonutChart([
            ("Occupied",    occupied_rooms, T.SUCCESS),
            ("Vacant",      vacant_units,   T.PRIMARY),
            ("Maintenance", maint,          T.WARNING),
        ]), 1)
        olegend = QVBoxLayout(); olegend.setSpacing(14)
        for label, count, color in [
            ("Occupied",    occupied_rooms, T.SUCCESS),
            ("Vacant",      vacant_units,   T.PRIMARY),
            ("Maintenance", maint,          T.WARNING),
        ]:
            row = QHBoxLayout(); row.setSpacing(10)
            dot = QFrame(); dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{color}; border-radius:5px;")
            row.addWidget(dot)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:500;")
            row.addWidget(lbl); row.addStretch(1)
            val = QLabel(f"{round(count/total_rooms*100)}%  ({count})")
            val.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12.5px;")
            row.addWidget(val)
            olegend.addLayout(row)
        olegend.addStretch(1)
        o_row.addLayout(olegend, 1)
        occ_card.body.addLayout(o_row)
        charts_row.addWidget(occ_card, 1)

        root.addLayout(charts_row)

        # ── Insight mini-cards ───────────────────────────────────────────────
        collection_rate = f"{round(paid_count / total_p * 100)}%"
        root.addWidget(section_title("Key Metrics", "Performance indicators at a glance"))
        grid = QGridLayout(); grid.setSpacing(20)
        mini = [
            ("Average Rent per Unit",         "₱ 6,500",        "wallet", T.PRIMARY, T.PRIMARY_SOFT),
            ("Collection Rate",               collection_rate,   "chart",  T.SUCCESS, T.SUCCESS_SOFT),
            ("Vacant Units",                  str(vacant_units), "door",   T.WARNING, T.WARNING_SOFT),
            ("Projected Revenue (Next Month)","₱ 30,000",        "users",  T.PURPLE,  T.PURPLE_SOFT),
        ]
        for i, args in enumerate(mini):
            grid.addWidget(MiniInsightCard(*args), 0, i)
        root.addLayout(grid)
        root.addStretch(1)

