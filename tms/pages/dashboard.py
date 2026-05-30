from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGridLayout,
                                QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QLinearGradient

from tms.pages._base import PageBase
from tms.widgets.cards import StatCard, Card, add_shadow
from tms.widgets.badges import make_badge
from tms import mock_data


class RevenueChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(220)
        self.values = [9, 10, 12, 17, 16, 19, 21, 22, 24, 28, 30, 27]
        self.labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 50, 20, 16, 30
        cw, ch = w - pad_l - pad_r, h - pad_t - pad_b
        if cw <= 0 or ch <= 0: return

        # gridlines + y labels
        p.setPen(QPen(QColor("#e2e8f0"), 1))
        steps = [0, 8, 17, 26, 35]
        for i, s in enumerate(steps):
            y = pad_t + ch - (s / 35.0) * ch
            p.drawLine(pad_l, int(y), pad_l + cw, int(y))
            p.setPen(QColor("#94a3b8"))
            p.drawText(4, int(y) + 4, f"₱{s}K")
            p.setPen(QPen(QColor("#e2e8f0"), 1))

        # build points
        n = len(self.values)
        max_v = 35.0
        pts = []
        for i, v in enumerate(self.values):
            x = pad_l + (i / (n - 1)) * cw
            y = pad_t + ch - (v / max_v) * ch
            pts.append((x, y))

        # area
        path = QPainterPath(); path.moveTo(pts[0][0], pad_t + ch)
        for x, y in pts: path.lineTo(x, y)
        path.lineTo(pts[-1][0], pad_t + ch); path.closeSubpath()
        grad = QLinearGradient(0, pad_t, 0, pad_t + ch)
        grad.setColorAt(0, QColor(37, 99, 235, 80))
        grad.setColorAt(1, QColor(37, 99, 235, 0))
        p.fillPath(path, QBrush(grad))

        # line
        p.setPen(QPen(QColor("#2563eb"), 2.5))
        for i in range(n - 1):
            p.drawLine(int(pts[i][0]), int(pts[i][1]), int(pts[i+1][0]), int(pts[i+1][1]))
        # dots
        p.setBrush(QColor("#2563eb")); p.setPen(QPen(QColor("white"), 2))
        for x, y in pts:
            p.drawEllipse(int(x)-4, int(y)-4, 8, 8)

        # x labels
        p.setPen(QColor("#94a3b8"))
        for i, lbl in enumerate(self.labels):
            x = pad_l + (i / (n - 1)) * cw
            p.drawText(int(x) - 12, pad_t + ch + 20, lbl)


class DonutChart(QWidget):
    def __init__(self, segments):
        """segments: [(label, value, color)]"""
        super().__init__()
        self.segments = segments
        self.setMinimumSize(220, 220)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        size = min(self.width(), self.height()) - 20
        x = (self.width() - size) // 2; y = (self.height() - size) // 2
        total = sum(v for _, v, _ in self.segments) or 1
        start = 90 * 16
        for label, val, color in self.segments:
            span = -int(360 * 16 * val / total)
            p.setPen(Qt.NoPen); p.setBrush(QColor(color))
            p.drawPie(x, y, size, size, start, span)
            start += span
        # inner hole
        hole = int(size * 0.58); hx = x + (size - hole)//2; hy = y + (size - hole)//2
        p.setBrush(QColor("white")); p.drawEllipse(hx, hy, hole, hole)


class DashboardPage(PageBase):
    def __init__(self):
        super().__init__()
        self.add_section_title("Overview", "Today's property snapshot")

        # Stat cards
        stats = QGridLayout(); stats.setSpacing(14)
        cards = [
            StatCard("Monthly Revenue", "₱ 28,000", "Collected this month", "💳", "#dbeafe", "#2563eb", "↑ 12%"),
            StatCard("Occupancy Rate",  "78%",      "Units currently occupied", "🏠", "#dcfce7", "#16a34a", "↑ 5%"),
            StatCard("Active Tenants",  "7",        "Currently housed", "👥", "#ede9fe", "#7c3aed", "↑ 1"),
            StatCard("Overdue Payments","2",        "Need attention", "📭", "#fee2e2", "#dc2626", "↑ 1"),
        ]
        for i, c in enumerate(cards):
            stats.addWidget(c, 0, i)
        self.body.addLayout(stats)

        self.add_section_title("Analytics", "Revenue and payment breakdown")
        analytics = QHBoxLayout(); analytics.setSpacing(14)

        # Revenue card
        rev = Card()
        rh = QHBoxLayout()
        rt = QLabel("Revenue Trend"); rt.setStyleSheet("font-size:15px; font-weight:700;")
        rh.addWidget(rt); rh.addStretch()
        year = QLabel("This Year"); year.setStyleSheet("background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:6px 12px; font-size:12px; color:#64748b;")
        rh.addWidget(year)
        rev.layout().addLayout(rh)
        rev.layout().addWidget(RevenueChart())
        analytics.addWidget(rev, 2)

        # Payment status card
        ps = Card()
        pt = QLabel("Payment Status"); pt.setStyleSheet("font-size:15px; font-weight:700;")
        ps.layout().addWidget(pt)
        inner = QHBoxLayout()
        donut = DonutChart([("Paid", 3, "#16a34a"), ("Unpaid", 2, "#d97706"), ("Overdue", 2, "#dc2626")])
        inner.addWidget(donut)
        legend = QVBoxLayout(); legend.setSpacing(10)
        for color, name, pct, count in [("#16a34a","Paid","43%",3),("#d97706","Unpaid","29%",2),("#dc2626","Overdue","28%",2)]:
            row = QHBoxLayout()
            dot = QLabel("●"); dot.setStyleSheet(f"color:{color}; font-size:18px;")
            nm = QLabel(name); nm.setStyleSheet("font-size:13px; font-weight:600;")
            row.addWidget(dot); row.addWidget(nm); row.addStretch()
            pc = QLabel(f"{pct}  ({count})"); pc.setStyleSheet("color:#64748b; font-size:12px;")
            row.addWidget(pc); legend.addLayout(row)
        legend.addStretch()
        tot = QLabel("Total payments: 7"); tot.setStyleSheet("color:#94a3b8; font-size:11px;")
        legend.addWidget(tot)
        inner.addLayout(legend, 1)
        ps.layout().addLayout(inner)
        analytics.addWidget(ps, 2)

        self.body.addLayout(analytics)

        # Additional insights
        self.add_section_title("Additional Insights")
        more = QGridLayout(); more.setSpacing(14)
        for i, (lbl, val, icon, ib, ic) in enumerate([
            ("Average Rent per Unit", "₱ 6,500", "💳", "#dbeafe", "#2563eb"),
            ("Collection Rate",       "85%",     "📊", "#dcfce7", "#16a34a"),
            ("Vacant Units",          "2",       "🚪", "#fef3c7", "#d97706"),
            ("Projected Revenue",     "₱ 30,000","👥", "#ede9fe", "#7c3aed"),
        ]):
            more.addWidget(StatCard(lbl, val, "", icon, ib, ic), 0, i)
        self.body.addLayout(more)

        # Recent payments
        self.add_section_title("Recent Payments", "Last 5 recorded payments")
        tbl_card = Card()
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Payment ID", "Tenant", "Amount", "Due Date", "Status"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row in mock_data.PAYMENTS[:5]:
            r = table.rowCount(); table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(row[0]))
            table.setItem(r, 1, QTableWidgetItem(row[2]))
            table.setItem(r, 2, QTableWidgetItem(f"₱ {row[3]:,}"))
            table.setItem(r, 3, QTableWidgetItem(row[4]))
            table.setCellWidget(r, 4, make_badge(row[6]))
        table.setMinimumHeight(280)
        tbl_card.layout().addWidget(table)
        view_all = QPushButton("View all payments"); view_all.setObjectName("linkBtn"); view_all.setCursor(Qt.PointingHandCursor)
        tbl_card.layout().addWidget(view_all, alignment=Qt.AlignCenter)
        self.body.addWidget(tbl_card)
