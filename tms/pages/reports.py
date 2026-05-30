from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGridLayout, QFrame
from PySide6.QtCore import Qt
from tms.pages._base import PageBase
from tms.widgets.cards import Card, StatCard
from tms.pages.dashboard import RevenueChart, DonutChart


class ReportsPage(PageBase):
    def __init__(self):
        super().__init__()
        self.add_section_title("Overview", "High-level performance at a glance")
        grid = QGridLayout(); grid.setSpacing(14)
        cards = [
            StatCard("Monthly Revenue", "₱ 28,000", "Collected this month", "💳", "#dbeafe", "#2563eb", "↑ 12%"),
            StatCard("Occupancy Rate",  "71%",      "Across all units",     "🏠", "#dcfce7", "#16a34a", "↑ 5%"),
            StatCard("Active Tenants",  "7",        "Currently housed",     "👥", "#ede9fe", "#7c3aed", "↑ 1"),
            StatCard("Overdue Payments","2",        "Need attention",       "📭", "#fee2e2", "#dc2626", "↑ 1"),
        ]
        for i, c in enumerate(cards): grid.addWidget(c, 0, i)
        self.body.addLayout(grid)

        self.add_section_title("Revenue Trend", "Monthly income over the year")
        rc = Card(); rc.layout().addWidget(RevenueChart())
        self.body.addWidget(rc)

        self.add_section_title("Breakdown", "Payment status and occupancy overview")
        row = QHBoxLayout(); row.setSpacing(14)

        ps = Card()
        ps.layout().addWidget(QLabel("Payment Status Breakdown", styleSheet="font-size:15px; font-weight:700;"))
        inner = QHBoxLayout()
        inner.addWidget(DonutChart([("Paid", 60, "#16a34a"), ("Unpaid", 25, "#d97706"), ("Overdue", 15, "#dc2626")]))
        leg = QVBoxLayout(); leg.setSpacing(8)
        for color, name, pct, n in [("#16a34a","Paid","60%",3),("#d97706","Unpaid","25%",2),("#dc2626","Overdue","15%",1)]:
            r = QHBoxLayout()
            d = QLabel("●"); d.setStyleSheet(f"color:{color}; font-size:18px;")
            r.addWidget(d); r.addWidget(QLabel(name, styleSheet="font-weight:600;")); r.addStretch()
            r.addWidget(QLabel(f"{pct}  ({n})", styleSheet="color:#64748b;"))
            leg.addLayout(r)
        leg.addStretch(); inner.addLayout(leg, 1)
        ps.layout().addLayout(inner)
        row.addWidget(ps)

        rb = Card()
        rb.layout().addWidget(QLabel("Room Occupancy Breakdown", styleSheet="font-size:15px; font-weight:700;"))
        inner2 = QHBoxLayout()
        inner2.addWidget(DonutChart([("Occupied", 70, "#16a34a"), ("Vacant", 20, "#2563eb"), ("Maintenance", 10, "#d97706")]))
        leg2 = QVBoxLayout(); leg2.setSpacing(8)
        for color, name, pct, n in [("#16a34a","Occupied","70%",7),("#2563eb","Vacant","20%",2),("#d97706","Maintenance","10%",1)]:
            r = QHBoxLayout()
            d = QLabel("●"); d.setStyleSheet(f"color:{color}; font-size:18px;")
            r.addWidget(d); r.addWidget(QLabel(name, styleSheet="font-weight:600;")); r.addStretch()
            r.addWidget(QLabel(f"{pct}  ({n})", styleSheet="color:#64748b;"))
            leg2.addLayout(r)
        leg2.addStretch(); inner2.addLayout(leg2, 1)
        rb.layout().addLayout(inner2)
        row.addWidget(rb)
        self.body.addLayout(row)

        self.add_section_title("Key Metrics", "Performance indicators at a glance")
        grid2 = QGridLayout(); grid2.setSpacing(14)
        for i, (lbl, val, icon, ib, ic) in enumerate([
            ("Average Rent per Unit", "₱ 6,500", "💳", "#dbeafe", "#2563eb"),
            ("Collection Rate",       "85%",     "📊", "#dcfce7", "#16a34a"),
            ("Vacant Units",          "2",       "🚪", "#fef3c7", "#d97706"),
            ("Projected Revenue",     "₱ 30,000","👥", "#ede9fe", "#7c3aed"),
        ]):
            grid2.addWidget(StatCard(lbl, val, "", icon, ib, ic), 0, i)
        self.body.addLayout(grid2)
