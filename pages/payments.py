"""
pages/payments.py — Payment Tracking page
==========================================
Displays all payments with colour-coded status badges.
Includes Add / Edit / Delete support and search/filter.

TODO(DB): Replace PAYMENTS list operations with SQLite queries.
"""

from __future__ import annotations

import copy
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QMessageBox, QAbstractItemView, QDateEdit, QFrame,
)

from theme import T
from database.repositories import get_payments
from widgets.components import (
    Card, section_title, styled_table, set_table_item, set_badge_cell,
    primary_button, ghost_button, danger_button, search_bar, KPICard,
    PaginationControl,
)


# ---------------------------------------------------------------------------
# Add / Edit dialog
# ---------------------------------------------------------------------------

class PaymentDialog(QDialog):
    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Payment" if record else "Record New Payment")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{T.SURFACE};")
        self.record = copy.deepcopy(record) if record else {}
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setSpacing(18); lay.setContentsMargins(28, 28, 28, 20)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color:{T.TEXT}; font-size:17px; font-weight:700;")
        lay.addWidget(title)

        form = QFormLayout(); form.setSpacing(14); form.setLabelAlignment(Qt.AlignLeft)
        lbl_style = f"color:{T.TEXT}; font-size:13px; font-weight:600;"

        def field(ph, val=""):
            le = QLineEdit(str(val)); le.setPlaceholderText(ph); le.setFixedHeight(42)
            le.setStyleSheet(
                f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
                f"QLineEdit:focus {{ border:1.5px solid {T.PRIMARY}; }}"
            )
            return le

        def date_edit(val=""):
            de = QDateEdit(); de.setCalendarPopup(True); de.setFixedHeight(42)
            de.setStyleSheet(
                f"QDateEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
            )
            if val:
                de.setDate(QDate.fromString(val, "yyyy-MM-dd"))
            else:
                de.setDate(QDate.currentDate())
            return de

        lbl = QLabel("Tenant ID"); lbl.setStyleSheet(lbl_style)
        self.tid_f = field("e.g. T-001", self.record.get("tenant_id",""))
        form.addRow(lbl, self.tid_f)

        lbl2 = QLabel("Tenant Name"); lbl2.setStyleSheet(lbl_style)
        self.tname_f = field("e.g. Maria Santos", self.record.get("tenant",""))
        form.addRow(lbl2, self.tname_f)

        lbl3 = QLabel("Amount (₱)"); lbl3.setStyleSheet(lbl_style)
        self.amount_f = field("e.g. 5000", self.record.get("amount",""))
        form.addRow(lbl3, self.amount_f)
        
        lbl_bm = QLabel("Month"); lbl_bm.setStyleSheet(lbl_style)
        self.month_f = QLineEdit(); self.month_f.setPlaceholderText("YYYY-MM"); self.month_f.setFixedHeight(42);
        self.month_f.setStyleSheet(
            f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER}; border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
        ); self.month_f.setReadOnly(True);
        form.addRow(lbl_bm, self.month_f)

        lbl4 = QLabel("Due Date"); lbl4.setStyleSheet(lbl_style)
        self.due_f = date_edit(self.record.get("due",""))
        form.addRow(lbl4, self.due_f)

        lbl5 = QLabel("Payment Date"); lbl5.setStyleSheet(lbl_style)
        self.paid_f = date_edit(self.record.get("paid_on",""))
        form.addRow(lbl5, self.paid_f)

        lbl6 = QLabel("Status"); lbl6.setStyleSheet(lbl_style)
        self.status_f = QComboBox()
        self.status_f.addItems(["Paid","Unpaid","Overdue"])
        idx = self.status_f.findText(self.record.get("status","Unpaid"))
        if idx >= 0: self.status_f.setCurrentIndex(idx)
        self.status_f.setFixedHeight(42)
        self.status_f.setStyleSheet(
            f"QComboBox {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        form.addRow(lbl6, self.status_f)

        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Save Payment")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            f"QPushButton {{ background:{T.PRIMARY}; color:white; border:none;"
            f" border-radius:10px; padding:8px 22px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{T.PRIMARY_DK}; }}"
        )
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(
            f"QPushButton {{ background:{T.BG}; color:{T.TEXT_MUTED}; border:1px solid {T.BORDER};"
            f" border-radius:10px; padding:8px 20px; font-size:13px; }}"
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_accept(self):
        self.record["tenant_id"]     = self.tid_f.text().strip()
        self.record["tenant"]        = self.tname_f.text().strip()
        self.record["amount"]        = self.amount_f.text().strip()
        self.record["due"]           = self.due_f.date().toString("yyyy-MM-dd")
        self.record["paid_on"]       = self.paid_f.date().toString("yyyy-MM-dd")
        self.record["status"]        = self.status_f.currentText()
        if not self.record["tenant"]:
            QMessageBox.warning(self, "Validation", "Tenant name is required.")
            return
        self.accept()


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

class PaymentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_month = QDate.currentDate().toString("yyyy-MM")
        self._data: list[dict] = get_payments(self.current_month)
        self._build()
        self._reload_table()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28); root.setSpacing(20)

        root.addWidget(section_title("Payment Tracking", "Monitor rent payments across all tenants"))

        # ── KPI summary ──────────────────────────────────────────────────────
        self.kpi_row = QHBoxLayout(); self.kpi_row.setSpacing(20)
        root.addLayout(self.kpi_row)
        self._update_kpis()

        # ── Filter row ───────────────────────────────────────────────────────
        card = Card(padding=20)
        filter_row = QHBoxLayout(); filter_row.setSpacing(12)
        
        self._month_filter = QLineEdit(self.current_month)
        self._month_filter.setPlaceholderText("YYYY-MM")
        self._month_filter.setFixedWidth(90)
        self._month_filter.setFixedHeight(42)
        self._month_filter.setStyleSheet(
            f"QLineEdit {{ background:{T.SURFACE}; border:1px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
        )
        self._month_filter.editingFinished.connect(self._change_month)
        filter_row.addWidget(self._month_filter)
        self._search = search_bar("Search by tenant name or payment ID…")
        self._search.textChanged.connect(self._filter_table)
        filter_row.addWidget(self._search, 1)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All Statuses","Paid","Unpaid","Overdue"])
        self._status_filter.setFixedHeight(42)
        self._status_filter.setStyleSheet(
            f"QComboBox {{ background:{T.SURFACE}; border:1px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; min-width:150px; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        self._status_filter.currentIndexChanged.connect(lambda _: self._apply_filters())
        filter_row.addWidget(self._status_filter)

        self._add_btn  = primary_button("Record Payment", "plus")
        self._edit_btn = ghost_button("Edit", "edit")
        self._del_btn  = danger_button("Delete", "trash")
        self._add_btn.clicked.connect(self._add_payment)
        self._edit_btn.clicked.connect(self._edit_payment)
        self._del_btn.clicked.connect(self._delete_payment)
        filter_row.addWidget(self._add_btn)
        filter_row.addWidget(self._edit_btn)
        filter_row.addWidget(self._del_btn)
        card.body.addLayout(filter_row)

        self._tbl = styled_table(
            ["Payment ID", "Tenant ID", "Tenant Name", "Amount", "Type", "Due Date", "Paid On", "Status"]
        )
        self._tbl.setMinimumHeight(380)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        card.body.addWidget(self._tbl)

        # Pagination and row count
        bottom_row = QHBoxLayout()
        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12px;")
        bottom_row.addWidget(self._count_lbl)
        bottom_row.addStretch(1)
        
        self._pagination = PaginationControl()
        self._pagination.page_changed.connect(lambda _: self._reload_table(self._filtered_data))
        self._pagination.items_per_page_changed.connect(lambda _: self._reload_table(self._filtered_data))
        bottom_row.addWidget(self._pagination)
        
        card.body.addLayout(bottom_row)

        root.addWidget(card)
        root.addStretch(1)

    # ── Table helpers ─────────────────────────────────────────────────────────

    def _update_kpis(self):
        # Clear existing
        while self.kpi_row.count():
            item = self.kpi_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        paid_amt    = sum(p["amount"] for p in self._data if p["status"] == "Paid")
        unpaid_amt  = sum(p["amount"] for p in self._data if p["status"] == "Unpaid")
        overdue_amt = sum(p["amount"] for p in self._data if p["status"] == "Overdue")
        self.kpi_row.addWidget(KPICard("Total Collected",  f"₱ {int(paid_amt):,}",    "wallet", T.SUCCESS, T.SUCCESS_SOFT, "", True,  "Paid this month"))
        self.kpi_row.addWidget(KPICard("Pending Amount",   f"₱ {int(unpaid_amt):,}",  "wallet", T.WARNING, T.WARNING_SOFT, "", False, "Not yet paid this month"))
        self.kpi_row.addWidget(KPICard("Overdue Amount",   f"₱ {int(overdue_amt):,}", "wallet", T.DANGER,  T.DANGER_SOFT,  "", False, "Total past due"))

    def _change_month(self):
        new_month = self._month_filter.text().strip()
        if len(new_month) == 7 and "-" in new_month:
            self.current_month = new_month
            self._data = get_payments(self.current_month)
            self._update_kpis()
            self._apply_filters()

    def _reload_table(self, rows: list[dict] | None = None):
        data = rows if rows is not None else self._data
        self._filtered_data = data
        self._pagination.set_total_items(len(data))
        
        start_idx = (self._pagination.current_page - 1) * self._pagination.items_per_page
        end_idx = start_idx + self._pagination.items_per_page
        page_data = data[start_idx:end_idx]

        self._tbl.setRowCount(0)
        for p in page_data:
            if "id" not in p:
                p["id"] = f"P-{len(self._data):03d}"
            r = self._tbl.rowCount(); self._tbl.insertRow(r)
            set_table_item(self._tbl, r, 0, p["id"])
            set_table_item(self._tbl, r, 1, p.get("tenant_id",""))
            set_table_item(self._tbl, r, 2, p["tenant"])
            set_table_item(self._tbl, r, 3, f"₱ {int(p['amount']):,}")
            set_table_item(self._tbl, r, 4, p.get("type","—"))
            set_table_item(self._tbl, r, 5, p["due"])
            set_table_item(self._tbl, r, 6, (p.get("paid_on") if p.get("paid_on") and p.get("paid_on") != "NULL" else "—"))
            set_badge_cell(self._tbl, r, 7, p["status"])
        self._count_lbl.setText(f"Showing {len(page_data)} of {len(data)} payment record(s)")

    def _apply_filters(self):
        q = self._search.text().lower()
        sf = self._status_filter.currentText()
        filtered = [
            p for p in self._data
            if (q in p["tenant"].lower() or q in p["id"].lower())
            and (sf == "All Statuses" or p["status"] == sf)
        ]
        self._pagination.current_page = 1
        self._reload_table(filtered)

    def _filter_table(self, _): self._apply_filters()

    def _selected_index(self) -> int | None:
        rows = self._tbl.selectionModel().selectedRows()
        if not rows: return None
        pid = self._tbl.item(rows[0].row(), 0).text()
        for i, p in enumerate(self._data):
            if p.get("id") == pid: return i
        return None

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_payment(self):
        dlg = PaymentDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            rec["id"] = f"P-{(len(self._data)+1):03d}"
            self._data.append(rec)
            # TODO(DB): INSERT INTO payments VALUES (...)
            self._apply_filters()

    def _edit_payment(self):
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select a Payment", "Please select a payment record first.")
            return
        dlg = PaymentDialog(record=self._data[idx], parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._data[idx] = dlg.record
            # TODO(DB): UPDATE payments SET ... WHERE id=?
            self._apply_filters()

    def _delete_payment(self):
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select a Payment", "Please select a payment to delete.")
            return
        pid = self._data[idx]["id"]
        ans = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete payment record '{pid}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            self._data.pop(idx)
            # TODO(DB): DELETE FROM payments WHERE id=?
            self._apply_filters()
