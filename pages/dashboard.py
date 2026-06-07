"""
pages/dashboard.py — Dashboard overview page
=============================================
Shows KPI cards, revenue chart, payment donut, and insight mini-cards.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QScrollArea,
    QGridLayout, QFrame, QSizePolicy,
)

from theme import T
from database.repositories import (
    get_dashboard_stats, get_payments,
    get_revenue_monthly, get_revenue_labels,
)
from widgets.components import (
    Card, KPICard, MiniInsightCard, LineChart, DonutChart,
    section_title, IconLabel,
)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28)
        root.setSpacing(22)

        # Load all stats from the database in one call
        current_month = QDate.currentDate().toString("yyyy-MM")
        stats = get_dashboard_stats(current_month)
        revenue_monthly = get_revenue_monthly()
        revenue_labels  = get_revenue_labels()
        payments        = get_payments(current_month)

        paid_count    = stats["paid_count"]
        unpaid_count  = stats["unpaid_count"]
        overdue_count = stats["overdue_count"]
        vacant_units  = stats["vacant_units"]
        active_tenants = stats["active_tenants"]
        total_revenue  = stats["total_revenue"]

        # ── KPI row ─────────────────────────────────────────────────────────
        root.addWidget(section_title("Overview", "Today's property snapshot"))
        kpis = QHBoxLayout(); kpis.setSpacing(20)
        kpis.addWidget(KPICard("Monthly Revenue",  f"₱ {int(total_revenue):,}", "wallet",
                               T.PRIMARY, T.PRIMARY_SOFT, "", True, "Collected this month"))
        kpis.addWidget(KPICard("Vacant Units", str(vacant_units), "door",
                               T.WARNING, T.WARNING_SOFT, "0", True, "Available for rent"))
        kpis.addWidget(KPICard("Active Tenants", str(active_tenants), "users",
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
        trend.body.addWidget(LineChart(revenue_monthly, revenue_labels))
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
        total_p = (paid_count + unpaid_count + overdue_count) or 1
        collection_rate = f"{round(paid_count / total_p * 100)}%"

        root.addWidget(section_title("Additional Insights"))
        insights = QGridLayout(); insights.setSpacing(20)
        mini_cards = [
            ("Collection Rate",               collection_rate, "chart",  T.SUCCESS, T.SUCCESS_SOFT),
            ("Vacant Units",                  str(vacant_units), "door", T.WARNING, T.WARNING_SOFT),
            ("Projected Revenue (Next Month)","₱ 30,000",       "users", T.PURPLE,  T.PURPLE_SOFT),
        ]
        for i, args in enumerate(mini_cards):
            insights.addWidget(MiniInsightCard(*args), 0, i)
        root.addLayout(insights)

        # ── Recent activity ──────────────────────────────────────────────────
        root.addWidget(section_title("Recent Payments", "Last 10 recorded payments"))
        recent = Card(padding=20)
        from widgets.components import styled_table, set_table_item, set_badge_cell
        tbl = styled_table(["Payment ID", "Tenant", "Amount", "Due Date", "Status"])
        tbl.setMaximumHeight(400)
        # Sort payments by most recent date (paid_on) descending, fallback to due date
        sorted_payments = sorted(payments, key=lambda p: p.get("paid_on", p.get("due", "")), reverse=True)
        for row_data in sorted_payments[:10]:
            r = tbl.rowCount(); tbl.insertRow(r)
            set_table_item(tbl, r, 0, row_data["id"])
            set_table_item(tbl, r, 1, row_data["tenant"])
            set_table_item(tbl, r, 2, f"₱ {int(row_data['amount']):,}")
            set_table_item(tbl, r, 3, row_data["due"])
            set_badge_cell(tbl, r, 4, row_data["status"])
        recent.body.addWidget(tbl)
        root.addWidget(recent)
        root.addStretch(1)

