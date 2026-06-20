"""
pages/reports.py — Reports & Analytics page
============================================
Full visual analytics dashboard with charts, KPIs, and insight cards.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListView,
    QScrollArea, QFrame, QGridLayout, QGraphicsDropShadowEffect,
)

from theme import T
from database.repositories import (
    get_dashboard_stats, get_revenue_trend,
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
        self._current_period = "This Year"
        self._build()

    def refresh(self):
        # We don't want to lose the current_period when refreshing
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

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(8, 16, 8, 25); root.setSpacing(16)

        # Load all stats from the database
        current_month   = QDate.currentDate().toString("yyyy-MM")
        stats           = get_dashboard_stats(current_month)
        revenue_monthly, revenue_labels = get_revenue_trend(self._current_period)

        paid_count    = stats["paid_count"]
        unpaid_count  = stats["unpaid_count"]
        overdue_count = stats["overdue_count"]
        
        fully_occupied     = stats["fully_occupied"]
        partially_occupied = stats["partially_occupied"]
        vacant_units       = stats["vacant_units"]
        
        occupied_rooms = stats["occupied_rooms"]
        total_rooms    = stats["total_rooms"] or 1
        total_revenue  = stats["total_revenue"]
        avg_rent       = stats.get("average_rent", 0)
        proj_rev       = stats.get("projected_revenue", 0)

        occupancy_rate = f"{round(occupied_rooms / total_rooms * 100)}%"

        # ── Overview KPIs ────────────────────────────────────────────────────
        st1 = section_title("Overview", "High-level performance at a glance")
        st1.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st1)
        
        kpi_container = QFrame()
        kpi_container.setObjectName("kpiContainer")
        kpi_container.setStyleSheet(f"#kpiContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        kpis = QHBoxLayout(kpi_container)
        kpis.setContentsMargins(10, 10, 10, 10)
        kpis.setSpacing(20)
        
        kpis.addWidget(KPICard("Monthly Revenue",  f"₱ {int(total_revenue):,}", "wallet",
                               T.PRIMARY, T.PRIMARY_SOFT, "", True,  "Collected this month"))
        kpis.addWidget(KPICard("Occupancy Rate",   occupancy_rate,  "home",
                               T.SUCCESS, T.SUCCESS_SOFT, "",  True,  "Across all units"))
        kpis.addWidget(KPICard("Occupied Rooms", str(occupied_rooms), "home",
                               T.SUCCESS, T.SUCCESS_SOFT, "", True, "Currently housed"))
        root.addWidget(kpi_container)

        # ── Revenue trend ────────────────────────────────────────────────────
        st2 = section_title("Revenue Trend", "Monthly income over the year")
        st2.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st2)
        
        trend_container = QFrame()
        trend_container.setObjectName("trendContainer")
        trend_container.setStyleSheet(f"#trendContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        trend_layout = QVBoxLayout(trend_container)
        trend_layout.setContentsMargins(10, 10, 10, 10)
        
        trend = Card(padding=22)
        head = QHBoxLayout()
        import datetime
        th = QLabel(f"Revenue Trend — {datetime.datetime.now().year}")
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
        period.setCurrentText(self._current_period)
        period.currentTextChanged.connect(self._on_period_changed)
        head.addWidget(period)
        trend.body.addLayout(head)
        self.revenue_chart = LineChart(revenue_monthly, revenue_labels)
        trend.body.addWidget(self.revenue_chart)
        trend_layout.addWidget(trend)
        root.addWidget(trend_container)

        # ── Charts row: donut + occupancy ────────────────────────────────────
        st3 = section_title("Breakdown", "Payment status and occupancy overview")
        st3.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st3)
        
        charts_container = QFrame()
        charts_container.setObjectName("chartsContainer")
        charts_container.setStyleSheet(f"#chartsContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        charts_row = QHBoxLayout(charts_container)
        charts_row.setContentsMargins(10, 10, 10, 10)
        charts_row.setSpacing(20)

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
            ("Fully Occupied",      fully_occupied,     T.SUCCESS),
            ("Partially Occupied",  partially_occupied, T.WARNING),
            ("Vacant",              vacant_units,       T.PRIMARY),
        ]), 1)
        olegend = QVBoxLayout(); olegend.setSpacing(14)
        for label, count, color in [
            ("Fully Occupied",      fully_occupied,     T.SUCCESS),
            ("Partially Occupied",  partially_occupied, T.WARNING),
            ("Vacant",              vacant_units,       T.PRIMARY),
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

        root.addWidget(charts_container)

        # ── Insight mini-cards ───────────────────────────────────────────────
        collection_rate = f"{round(paid_count / total_p * 100)}%"
        
        st4 = section_title("Key Metrics", "Performance indicators at a glance")
        st4.layout().setContentsMargins(12, 0, 12, 0)
        root.addWidget(st4)
        
        grid_container = QFrame()
        grid_container.setObjectName("gridContainer")
        grid_container.setStyleSheet(f"#gridContainer {{ background-color: {T.BG}; border-radius: {T.RADIUS}px; }}")
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setSpacing(20)
        
        mini = [
            ("Average Rent per Unit",         f"₱ {avg_rent:,}",        "wallet", T.PRIMARY, T.PRIMARY_SOFT),
            ("Collection Rate",               collection_rate,   "chart",  T.SUCCESS, T.SUCCESS_SOFT),
            ("Available Units",               str(vacant_units), "door",   T.WARNING, T.WARNING_SOFT),
            ("Projected Unpaid",              f"₱ {proj_rev:,}",        "users",  T.PURPLE,  T.PURPLE_SOFT),
        ]
        for i, args in enumerate(mini):
            grid.addWidget(MiniInsightCard(*args), 0, i)
        root.addWidget(grid_container)
        root.addStretch(1)

    def _on_period_changed(self, text: str):
        from database.repositories import get_revenue_trend
        self._current_period = text
        data, labels = get_revenue_trend(text)
        self.revenue_chart.update_data(data, labels)

