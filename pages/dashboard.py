"""
pages/dashboard.py — Dashboard overview page
=============================================
Shows KPI cards, revenue chart, payment donut, and insight mini-cards.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListView, QScrollArea,
    QGridLayout, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
)

from theme import T
from database.repositories import (
    get_dashboard_stats, get_payments,
    get_revenue_trend
)
from widgets.components import (
    Card, KPICard, MiniInsightCard, LineChart, DonutChart,
    section_title, IconLabel,
)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from database.repositories import get_dashboard_stats, get_revenue_trend
        self.stats = get_dashboard_stats()
        self.revenue_data, self.revenue_labels = get_revenue_trend("This Year")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 1, 20, 21)
        self._build()

    def refresh(self):
        from database.repositories import get_dashboard_stats, get_revenue_trend
        self.stats = get_dashboard_stats()
        # Keep the selected period
        current_period = getattr(self, "_current_period", "This Year")
        self.revenue_data, self.revenue_labels = get_revenue_trend(current_period)
        # Repaint or rebuild UI components if necessary. 
        # For a full implementation, you'd update the specific widgets instead of clearing.
        # This simple refresh just forces an update of the labels if they were decoupled.
        # Since _build recreates the layout, we'll clear and rebuild for simplicity here.
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: white; border-top-left-radius: 20px; border-bottom-left-radius: 20px; border-top-right-radius: 20px; border-bottom-right-radius: 20px; margin-right: 5px;}}")

        eff = QGraphicsDropShadowEffect(scroll)
        eff.setBlurRadius(28)
        eff.setOffset(0, 6)
        eff.setColor(QColor(15, 27, 45, 18))
        scroll.setGraphicsEffect(eff)
        
        self.main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(8, 16, 8, 25)
        root.setSpacing(16)

        # Load all stats from the database in one call
        current_month = QDate.currentDate().toString("yyyy-MM")
        stats = get_dashboard_stats(current_month)
        
        current_period = getattr(self, "_current_period", "This Year")
        revenue_monthly, revenue_labels = get_revenue_trend(current_period)
        payments = get_payments(current_month)

        paid_count    = stats["paid_count"]
        unpaid_count  = stats["unpaid_count"]
        overdue_count = stats["overdue_count"]
        vacant_units  = stats["vacant_units"]
        active_tenants = stats["active_tenants"]
        total_revenue  = stats["total_revenue"]
        avg_rent       = stats.get("average_rent", 0)
        proj_rev       = stats.get("projected_revenue", 0)

        # ── KPI row ─────────────────────────────────────────────────────────
        st1 = section_title("Overview", "Today's property snapshot")
        st1.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st1)
        
        kpi_container = QFrame()
        kpi_container.setObjectName("kpiContainer")
        kpi_container.setStyleSheet(f"#kpiContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        kpis = QHBoxLayout(kpi_container)
        kpis.setContentsMargins(10, 10, 10, 10)
        kpis.setSpacing(20)
        
        kpis.addWidget(KPICard("Monthly Revenue",  f"₱ {int(total_revenue):,}", "wallet",
                               T.PRIMARY, T.PRIMARY_SOFT, "", True, "Collected this month"))
        kpis.addWidget(KPICard("Available Units", str(vacant_units), "door",
                               T.WARNING, T.WARNING_SOFT, "0", True, "Vacant or partially occupied"))
        kpis.addWidget(KPICard("Active Tenants", str(active_tenants), "users",
                               T.PURPLE, T.PURPLE_SOFT, "1", True, "Currently housed"))
        root.addWidget(kpi_container)

        # ── Charts row ───────────────────────────────────────────────────────
        st2 = section_title("Analytics", "Revenue and payment breakdown")
        st2.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st2)
        
        charts_container = QFrame()
        charts_container.setObjectName("chartsContainer")
        charts_container.setStyleSheet(f"#chartsContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        charts = QHBoxLayout(charts_container)
        charts.setContentsMargins(10, 10, 10, 10)
        charts.setSpacing(20)

        # Revenue trend card
        trend = Card(padding=22)
        trend_head = QHBoxLayout()
        import datetime
        th = QLabel(f"Revenue Trend — {datetime.datetime.now().year}")
        th.setStyleSheet(f"color:{T.TEXT}; font-size:15px; font-weight:700;")
        trend_head.addWidget(th); trend_head.addStretch(1)
        from widgets.components import CleanComboBox
        period = CleanComboBox(["This Year", "Last 6 Months", "This Month"])
        period.setStyleSheet(f"""
            QPushButton {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER};
                border-radius: 8px;
                padding: 5px 24px 5px 10px;
                color: {T.TEXT_MUTED};
                font-size: 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {T.TEXT};
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
        period.setCurrentText(current_period)
        period.currentTextChanged.connect(self._on_period_changed)
        trend_head.addWidget(period)
        trend.body.addLayout(trend_head)
        self.revenue_chart = LineChart(revenue_monthly, revenue_labels)
        trend.body.addWidget(self.revenue_chart)
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
        root.addWidget(charts_container)

        # ── Insight mini-cards ───────────────────────────────────────────────
        total_p = (paid_count + unpaid_count + overdue_count) or 1
        collection_rate = f"{round(paid_count / total_p * 100)}%"

        st3 = section_title("Additional Insights")
        st3.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st3)
        
        insights_container = QFrame()
        insights_container.setObjectName("insightsContainer")
        insights_container.setStyleSheet(f"#insightsContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        insights = QGridLayout(insights_container)
        insights.setContentsMargins(10, 10, 10, 10)
        insights.setSpacing(20)
        
        mini_cards = [
            ("Collection Rate",               collection_rate, "chart",  T.SUCCESS, T.SUCCESS_SOFT),
            ("Average Rent per Unit",         f"₱ {avg_rent:,}", "wallet", T.PRIMARY, T.PRIMARY_SOFT),
            ("Projected Unpaid",              f"₱ {proj_rev:,}", "users", T.PURPLE,  T.PURPLE_SOFT),
        ]
        for i, args in enumerate(mini_cards):
            insights.addWidget(MiniInsightCard(*args), 0, i)
        root.addWidget(insights_container)

        # ── Recent activity ──────────────────────────────────────────────────

        st4 = section_title("Recent Payments", "Last 10 recorded payments")
        st4.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st4)
        
        recent_container = QFrame()
        recent_container.setObjectName("recentContainer")
        recent_container.setStyleSheet(f"#recentContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        recent_layout = QVBoxLayout(recent_container)
        recent_layout.setContentsMargins(10, 10, 10, 10)
        
        recent = Card(padding=20)
        from widgets.components import styled_table, set_table_item, set_badge_cell
        tbl = styled_table(["Payment ID", "Tenant", "Amount", "Due Date", "Status"])
        tbl.setFixedHeight(300)
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
        recent_layout.addWidget(recent)
        root.addWidget(recent_container)
        root.addStretch(1)

    def _on_period_changed(self, text: str):
        from database.repositories import get_revenue_trend
        self._current_period = text
        data, labels = get_revenue_trend(text)
        self.revenue_chart.update_data(data, labels)

