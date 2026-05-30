"""
pages/reports.py — Reports & Analytics page
============================================
Full visual analytics dashboard with charts, KPIs, and insight cards.
This is the most chart-heavy page in the application.

TODO(DB): Pull aggregated data from SQLite for all metrics shown here.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QScrollArea, QFrame, QGridLayout,
)

from theme import T
from data.mock_data import REVENUE_MONTHLY, REVENUE_LABELS, PAYMENTS, TENANTS, ROOMS
from widgets.components import (
    Card, KPICard, MiniInsightCard, LineChart, DonutChart,
    section_title,
)


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28); root.setSpacing(22)

        # ── Overview KPIs ────────────────────────────────────────────────────
        # TODO(DB): Aggregate these from real data
        root.addWidget(section_title("Overview", "High-level performance at a glance"))
        kpis = QHBoxLayout(); kpis.setSpacing(20)
        kpis.addWidget(KPICard("Monthly Revenue",  "₱ 28,000", "wallet",
                               T.PRIMARY, T.PRIMARY_SOFT, "12%", True,  "Collected this month"))
        kpis.addWidget(KPICard("Occupancy Rate",   "71%",      "home",
                               T.SUCCESS, T.SUCCESS_SOFT, "5%",  True,  "Across all units"))
        kpis.addWidget(KPICard("Active Tenants",   str(len(TENANTS)), "users",
                               T.PURPLE, T.PURPLE_SOFT,   "1",   True,  "Currently housed"))
        kpis.addWidget(KPICard("Overdue Payments", str(sum(1 for p in PAYMENTS if p["status"]=="Overdue")),
                               "wallet", T.DANGER, T.DANGER_SOFT, "1", False, "Need attention"))
        root.addLayout(kpis)

        # ── Revenue trend ────────────────────────────────────────────────────
        root.addWidget(section_title("Revenue Trend", "Monthly income over the year"))
        trend = Card(padding=22)
        head = QHBoxLayout()
        th = QLabel("Revenue Trend — 2025")
        th.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        head.addWidget(th); head.addStretch(1)
        period = QComboBox()
        period.addItems(["This Year", "Last 6 Months", "This Month"])
        period.setStyleSheet(
            f"QComboBox {{ background:{T.BG}; border:1px solid {T.BORDER};"
            f" border-radius:8px; padding:5px 10px; color:{T.TEXT}; font-size:12px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        head.addWidget(period)
        trend.body.addLayout(head)
        trend.body.addWidget(LineChart(REVENUE_MONTHLY, REVENUE_LABELS))
        root.addWidget(trend)

        # ── Charts row: donut + occupancy ────────────────────────────────────
        root.addWidget(section_title("Breakdown", "Payment status and occupancy overview"))
        charts_row = QHBoxLayout(); charts_row.setSpacing(20)

        paid_count    = sum(1 for p in PAYMENTS if p["status"] == "Paid")
        unpaid_count  = sum(1 for p in PAYMENTS if p["status"] == "Unpaid")
        overdue_count = sum(1 for p in PAYMENTS if p["status"] == "Overdue")

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
        for label, count, pct, color in [
            ("Paid",    paid_count,    60, T.SUCCESS),
            ("Unpaid",  unpaid_count,  25, T.WARNING),
            ("Overdue", overdue_count, 15, T.DANGER),
        ]:
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
        occupied = sum(1 for r in ROOMS if r["status"] == "Occupied")
        vacant   = sum(1 for r in ROOMS if r["status"] == "Vacant")
        maint    = sum(1 for r in ROOMS if r["status"] == "Maintenance")

        occ_card = Card(padding=22)
        oh = QLabel("Room Occupancy Breakdown")
        oh.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        occ_card.body.addWidget(oh)
        o_row = QHBoxLayout(); o_row.setSpacing(20)
        o_row.addWidget(DonutChart([
            ("Occupied",    occupied, T.SUCCESS),
            ("Vacant",      vacant,   T.PRIMARY),
            ("Maintenance", maint,    T.WARNING),
        ]), 1)
        olegend = QVBoxLayout(); olegend.setSpacing(14)
        total_rooms = len(ROOMS) or 1
        for label, count, color in [
            ("Occupied",    occupied, T.SUCCESS),
            ("Vacant",      vacant,   T.PRIMARY),
            ("Maintenance", maint,    T.WARNING),
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
        root.addWidget(section_title("Key Metrics", "Performance indicators at a glance"))
        grid = QGridLayout(); grid.setSpacing(20)
        mini = [
            ("Average Rent per Unit",         "₱ 6,500", "wallet", T.PRIMARY, T.PRIMARY_SOFT),
            ("Collection Rate",               "85%",     "chart",  T.SUCCESS, T.SUCCESS_SOFT),
            ("Vacant Units",                  str(vacant),"door",  T.WARNING, T.WARNING_SOFT),
            ("Projected Revenue (Next Month)","₱ 30,000","users",  T.PURPLE,  T.PURPLE_SOFT),
        ]
        for i, args in enumerate(mini):
            grid.addWidget(MiniInsightCard(*args), 0, i)
        root.addLayout(grid)
        root.addStretch(1)
