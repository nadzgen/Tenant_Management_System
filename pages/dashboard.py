"""
pages/dashboard.py — Dashboard overview page
=============================================
Shows KPI cards, revenue chart, payment donut, and insight mini-cards.

TODO(DB): Replace mock values with aggregated SQLite queries.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea,
    QGridLayout, QFrame, QSizePolicy,
)

from theme import T
from data.mock_data import REVENUE_MONTHLY, REVENUE_LABELS, PAYMENTS, TENANTS, ROOMS
from widgets.components import (
    Card, KPICard, MiniInsightCard, LineChart, DonutChart,
    section_title, IconLabel,
)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28)
        root.setSpacing(22)

        # ── KPI row ─────────────────────────────────────────────────────────
        # TODO(DB): SELECT SUM(amount) FROM payments WHERE status='Paid' AND month=current
        root.addWidget(section_title("Overview", "Today's property snapshot"))
        kpis = QHBoxLayout(); kpis.setSpacing(20)
        kpis.addWidget(KPICard("Monthly Revenue",  "₱ 28,000", "wallet",
                               T.PRIMARY, T.PRIMARY_SOFT, "12%", True, "Collected this month"))
        kpis.addWidget(KPICard("Vacant Units", str(sum(1 for r in ROOMS if r["status"] == "Vacant")), "door",
                               T.WARNING, T.WARNING_SOFT, "0", True, "Available for rent"))
        kpis.addWidget(KPICard("Active Tenants", str(len(TENANTS)), "users",
                               T.PURPLE, T.PURPLE_SOFT, "1", True, "Currently housed"))
        root.addLayout(kpis)

        # ── Charts row ───────────────────────────────────────────────────────
        root.addWidget(section_title("Analytics", "Revenue and payment breakdown"))
        charts = QHBoxLayout(); charts.setSpacing(20)

        # Revenue trend card
        trend = Card(padding=22)
        trend_head = QHBoxLayout()
        th = QLabel("Revenue Trend")
        th.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        trend_head.addWidget(th); trend_head.addStretch(1)
        period = QComboBox()
        period.addItems(["This Year", "Last 6 Months", "This Month"])
        period.setStyleSheet(
            f"QComboBox {{ background:{T.BG}; border:1px solid {T.BORDER};"
            f" border-radius:8px; padding:5px 10px; color:{T.TEXT}; font-size:12px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        trend_head.addWidget(period)
        trend.body.addLayout(trend_head)
        trend.body.addWidget(LineChart(REVENUE_MONTHLY, REVENUE_LABELS))
        charts.addWidget(trend, 3)
        trend.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # Donut card
        donut = Card(padding=22)
        dh = QLabel("Payment Status")
        dh.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        donut.body.addWidget(dh)

        paid_count    = sum(1 for p in PAYMENTS if p["status"] == "Paid")
        unpaid_count  = sum(1 for p in PAYMENTS if p["status"] == "Unpaid")
        overdue_count = sum(1 for p in PAYMENTS if p["status"] == "Overdue")

        d_row = QHBoxLayout(); d_row.setSpacing(16)
        d_row.addWidget(DonutChart([
            ("Paid",    paid_count,    T.SUCCESS),
            ("Unpaid",  unpaid_count,  T.WARNING),
            ("Overdue", overdue_count, T.DANGER),
        ]), 1)

        legend = QVBoxLayout(); legend.setSpacing(12)
        for label, count, color in [
            ("Paid",    paid_count,    T.SUCCESS),
            ("Unpaid",  unpaid_count,  T.WARNING),
            ("Overdue", overdue_count, T.DANGER),
        ]:
            row = QHBoxLayout(); row.setSpacing(10)
            dot = QFrame(); dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{color}; border-radius:5px;")
            row.addWidget(dot)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:500;")
            row.addWidget(lbl); row.addStretch(1)
            val = QLabel(f"{count} payments")
            val.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12.5px;")
            row.addWidget(val)
            legend.addLayout(row)
        legend.addStretch(1)
        d_row.addLayout(legend, 1)
        donut.body.addLayout(d_row)
        charts.addWidget(donut, 2)
        donut.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        root.addLayout(charts)

        # ── Insight mini-cards ───────────────────────────────────────────────
        root.addWidget(section_title("Additional Insights"))
        insights = QGridLayout(); insights.setSpacing(20)
        # TODO(DB): Calculate these from DB aggregates
        mini_cards = [
            ("Average Rent per Unit",        "₱ 6,500", "wallet", T.PRIMARY, T.PRIMARY_SOFT),
            ("Collection Rate",              "85%",     "chart",  T.SUCCESS, T.SUCCESS_SOFT),
            ("Vacant Units",                 str(sum(1 for r in ROOMS if r["status"] == "Vacant")),
             "door", T.WARNING, T.WARNING_SOFT),
            ("Projected Revenue (Next Month)","₱ 30,000","users", T.PURPLE, T.PURPLE_SOFT),
        ]
        for i, args in enumerate(mini_cards):
            insights.addWidget(MiniInsightCard(*args), 0, i)
        root.addLayout(insights)

        # ── Recent activity ──────────────────────────────────────────────────
        root.addWidget(section_title("Recent Payments", "Last 5 recorded payments"))
        recent = Card(padding=20)
        from widgets.components import styled_table, set_table_item, set_badge_cell
        tbl = styled_table(["Payment ID", "Tenant", "Amount", "Due Date", "Status"])
        tbl.setMaximumHeight(240)
        for row_data in PAYMENTS[-5:]:
            r = tbl.rowCount(); tbl.insertRow(r)
            set_table_item(tbl, r, 0, row_data["id"])
            set_table_item(tbl, r, 1, row_data["tenant"])
            set_table_item(tbl, r, 2, f"₱ {row_data['amount']:,}")
            set_table_item(tbl, r, 3, row_data["due"])
            set_badge_cell(tbl, r, 4, row_data["status"])
        recent.body.addWidget(tbl)
        root.addWidget(recent)
        root.addStretch(1)
