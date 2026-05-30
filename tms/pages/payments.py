from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                                QDialog, QFormLayout, QComboBox, QDoubleSpinBox, QDateEdit,
                                QGridLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, QDate
from tms.pages._base import PageBase
from tms.widgets.cards import Card, StatCard
from tms.widgets.badges import make_badge
from tms import mock_data


class PaymentDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Payment" if data else "Record Payment")
        self.setMinimumWidth(420)
        form = QFormLayout(self); form.setSpacing(10)
        self.pid = QLineEdit(); self.tid = QLineEdit(); self.name = QLineEdit()
        self.amount = QDoubleSpinBox(); self.amount.setRange(0, 1_000_000); self.amount.setPrefix("₱ "); self.amount.setDecimals(0); self.amount.setSingleStep(500)
        self.due = QDateEdit(); self.due.setCalendarPopup(True); self.due.setDate(QDate.currentDate()); self.due.setDisplayFormat("yyyy-MM-dd")
        self.paid = QDateEdit(); self.paid.setCalendarPopup(True); self.paid.setDate(QDate.currentDate()); self.paid.setDisplayFormat("yyyy-MM-dd")
        self.paid.setSpecialValueText("—"); self.paid.setMinimumDate(QDate(2000,1,1))
        self.status = QComboBox(); self.status.addItems(["Paid", "Unpaid", "Overdue"])
        if data:
            self.pid.setText(data[0]); self.tid.setText(data[1]); self.name.setText(data[2])
            self.amount.setValue(float(data[3])); self.due.setDate(QDate.fromString(data[4], "yyyy-MM-dd"))
            if data[5]: self.paid.setDate(QDate.fromString(data[5], "yyyy-MM-dd"))
            self.status.setCurrentText(data[6])
        else:
            self.pid.setText(f"P-{len(mock_data.PAYMENTS)+1:03d}")
        for label, w in [("Payment ID", self.pid), ("Tenant ID", self.tid), ("Tenant Name", self.name),
                         ("Amount", self.amount), ("Due Date", self.due), ("Paid On", self.paid), ("Status", self.status)]:
            l = QLabel(label); l.setObjectName("formLabel"); form.addRow(l, w)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def values(self):
        paid = self.paid.date().toString("yyyy-MM-dd") if self.status.currentText() == "Paid" else ""
        return [self.pid.text().strip(), self.tid.text().strip(), self.name.text().strip(),
                int(self.amount.value()), self.due.date().toString("yyyy-MM-dd"),
                paid, self.status.currentText()]


class PaymentsPage(PageBase):
    def __init__(self):
        super().__init__()
        self.add_section_title("Payment Tracking", "Monitor rent payments across all tenants")

        self.stats_grid = QGridLayout(); self.stats_grid.setSpacing(14)
        self.body.addLayout(self.stats_grid)

        card = Card()
        bar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setObjectName("searchBox")
        self.search.setPlaceholderText("🔍   Search by tenant name or payment ID...")
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search, 1)
        self.filter_status = QComboBox(); self.filter_status.addItems(["All Statuses", "Paid", "Unpaid", "Overdue"])
        self.filter_status.currentIndexChanged.connect(lambda _: self._filter(self.search.text()))
        bar.addWidget(self.filter_status)
        add_btn = QPushButton(" +  Record Payment"); add_btn.setObjectName("primaryBtn"); add_btn.setCursor(Qt.PointingHandCursor)
        edit_btn = QPushButton(" ✎  Edit");           edit_btn.setObjectName("ghostBtn"); edit_btn.setCursor(Qt.PointingHandCursor)
        del_btn  = QPushButton(" 🗑  Delete");         del_btn.setObjectName("dangerBtn"); del_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add); edit_btn.clicked.connect(self._edit); del_btn.clicked.connect(self._delete)
        for b in (add_btn, edit_btn, del_btn): bar.addWidget(b)
        card.layout().addLayout(bar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Payment ID", "Tenant ID", "Tenant Name", "Amount", "Due Date", "Paid On", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(420)
        card.layout().addWidget(self.table)
        self.body.addWidget(card)
        self._reload()

    def _refresh_stats(self):
        while self.stats_grid.count():
            it = self.stats_grid.takeAt(0); w = it.widget()
            if w: w.deleteLater()
        total = sum(p[3] for p in mock_data.PAYMENTS if p[6] == "Paid")
        pending = sum(p[3] for p in mock_data.PAYMENTS if p[6] == "Unpaid")
        overdue = sum(p[3] for p in mock_data.PAYMENTS if p[6] == "Overdue")
        cards = [
            StatCard("Total Collected", f"₱ {total:,}",   "Paid payments", "💳", "#dcfce7", "#16a34a"),
            StatCard("Pending Amount",  f"₱ {pending:,}", "Not yet paid",  "📋", "#fef3c7", "#d97706"),
            StatCard("Overdue Amount",  f"₱ {overdue:,}", "Past due date", "📭", "#fee2e2", "#dc2626"),
        ]
        for i, c in enumerate(cards): self.stats_grid.addWidget(c, 0, i)

    def _reload(self):
        # TODO: SELECT * FROM payments
        self._refresh_stats()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row in mock_data.PAYMENTS:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row[0]))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setItem(r, 2, QTableWidgetItem(row[2]))
            self.table.setItem(r, 3, QTableWidgetItem(f"₱ {row[3]:,}"))
            self.table.setItem(r, 4, QTableWidgetItem(row[4]))
            self.table.setItem(r, 5, QTableWidgetItem(row[5] if row[5] else "—"))
            self.table.setCellWidget(r, 6, make_badge(row[6]))
        self.table.setSortingEnabled(True)
        self._filter(self.search.text())

    def _filter(self, text):
        text = text.lower().strip()
        status = self.filter_status.currentText()
        for r in range(self.table.rowCount()):
            cells = [self.table.item(r, c).text().lower() if self.table.item(r, c) else "" for c in range(6)]
            row_status = self.table.cellWidget(r, 6).text().split("  ")[-1] if self.table.cellWidget(r, 6) else ""
            text_ok = not text or any(text in s for s in cells)
            status_ok = status == "All Statuses" or status == row_status
            self.table.setRowHidden(r, not (text_ok and status_ok))

    def _sel_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return None
        return self.table.item(rows[0].row(), 0).text()

    def _add(self):
        dlg = PaymentDialog(self)
        if dlg.exec() == QDialog.Accepted:
            # TODO: INSERT INTO payments
            mock_data.PAYMENTS.append(dlg.values()); self._reload()

    def _edit(self):
        pid = self._sel_id()
        if not pid: QMessageBox.information(self, "Edit", "Please select a payment first."); return
        idx = next((i for i, p in enumerate(mock_data.PAYMENTS) if p[0] == pid), -1)
        if idx < 0: return
        dlg = PaymentDialog(self, mock_data.PAYMENTS[idx])
        if dlg.exec() == QDialog.Accepted:
            # TODO: UPDATE payments SET ...
            mock_data.PAYMENTS[idx] = dlg.values(); self._reload()

    def _delete(self):
        pid = self._sel_id()
        if not pid: QMessageBox.information(self, "Delete", "Please select a payment first."); return
        if QMessageBox.question(self, "Confirm Delete", f"Delete payment {pid}?") == QMessageBox.Yes:
            # TODO: DELETE FROM payments WHERE id = ?
            mock_data.PAYMENTS[:] = [p for p in mock_data.PAYMENTS if p[0] != pid]
            self._reload()
