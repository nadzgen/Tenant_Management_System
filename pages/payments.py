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
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QListView, QDialogButtonBox,
    QMessageBox, QAbstractItemView, QDateEdit, QFrame, QMenu, QCompleter
)

from theme import T
from database.repositories import get_payments
from widgets.components import (
    Card, section_title, styled_table, set_table_item, set_badge_cell,
    primary_button, ghost_button, danger_button, search_bar, KPICard,
    PaginationControl, table_action_cell, filter_button, MonthPicker, Toast
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
        lay = QVBoxLayout(self)
        lay.setSpacing(20)
        lay.setContentsMargins(32, 32, 32, 24)

        header = QVBoxLayout()
        header.setSpacing(4)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color:{T.TEXT}; font-size:18px; font-weight:700;")
        subtitle = QLabel("Record rent payments and deposits")
        subtitle.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:13px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        lay.addLayout(header)
        
        # Suggestion banner (hidden by default)
        self.suggestion_banner = QLabel()
        self.suggestion_banner.setStyleSheet(f"""
            background: {T.PRIMARY_SOFT}; 
            color: {T.PRIMARY_DK}; 
            padding: 10px 14px; 
            border-radius: 8px; 
            font-size: 13px; 
            font-weight: 500;
        """)
        self.suggestion_banner.hide()
        lay.addWidget(self.suggestion_banner)

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
            de.setStyleSheet(f"""
                QDateEdit {{
                    background: {T.BG};
                    border: 1.5px solid {T.BORDER};
                    border-radius: 10px;
                    padding: 0 14px;
                    color: {T.TEXT};
                    font-size: 13px;
                }}
                QDateEdit::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 32px;
                    border: none;
                }}
                QDateEdit::down-arrow {{
                    image: url(assets/chevron-down.svg);
                    width: 16px;
                    height: 16px;
                }}
            """)
            if val:
                de.setDate(QDate.fromString(val, "yyyy-MM-dd"))
            else:
                de.setDate(QDate.currentDate())
            return de

        lbl_tenant = QLabel("Select Tenant"); lbl_tenant.setStyleSheet(lbl_style)
        self.tenant_f = QComboBox(); self.tenant_f.setView(QListView())
        self.tenant_f.setFixedHeight(42)
        self.tenant_f.setEditable(True)
        self.tenant_f.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.tenant_f.setStyleSheet(
            f"QComboBox {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
            f"QComboBox:focus {{ border:1.5px solid {T.PRIMARY}; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        
        from database.repositories import get_tenants
        self._tenants = get_tenants()
        for t in self._tenants:
            self.tenant_f.addItem(f"{t['name']} (T-{t['id']:03d})", t['id'])
            
        if self.record.get("tenant_id"):
            tid_val = self.record["tenant_id"]
            if isinstance(tid_val, str) and tid_val.startswith("T-"):
                try: tid_val = int(tid_val[2:])
                except ValueError: pass
            idx = self.tenant_f.findData(tid_val)
            if idx >= 0: self.tenant_f.setCurrentIndex(idx)
        else:
            self.tenant_f.setCurrentIndex(-1)
            self.tenant_f.lineEdit().setPlaceholderText("Type to search tenant...")
        
        self.tenant_f.currentIndexChanged.connect(self._on_tenant_changed)
        form.addRow(lbl_tenant, self.tenant_f)

        lbl3 = QLabel("Amount (₱)"); lbl3.setStyleSheet(lbl_style)
        self.amount_f = field("e.g. 5000", self.record.get("amount",""))
        form.addRow(lbl3, self.amount_f)

        lbl4 = QLabel("Due Date"); lbl4.setStyleSheet(lbl_style)
        self.due_f = date_edit(self.record.get("due",""))
        form.addRow(lbl4, self.due_f)

        lbl5 = QLabel("Payment Date"); lbl5.setStyleSheet(lbl_style)
        self.paid_f = date_edit(self.record.get("paid_on",""))
        form.addRow(lbl5, self.paid_f)

        lbl_type = QLabel("Payment Type"); lbl_type.setStyleSheet(lbl_style)
        self.type_f = QComboBox(); self.type_f.setView(QListView())
        self.type_f.addItems(["Regular", "Deposit", "Summer"])
        idx_type = self.type_f.findText(self.record.get("type","Regular"))
        if idx_type >= 0: self.type_f.setCurrentIndex(idx_type)
        self.type_f.setFixedHeight(42)
        self.type_f.setStyleSheet(f"""
            QComboBox {{
                background: {T.BG};
                border: 1.5px solid {T.BORDER};
                border-radius: 10px;
                padding: 0 14px;
                color: {T.TEXT};
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url(assets/chevron-down.svg);
                width: 16px;
                height: 16px;
            }}
        """)
        form.addRow(lbl_type, self.type_f)

        lbl6 = QLabel("Status"); lbl6.setStyleSheet(lbl_style)
        self.status_f = QComboBox(); self.status_f.setView(QListView())
        self.status_f.addItems(["Paid","Unpaid","Overdue"])
        idx = self.status_f.findText(self.record.get("status","Unpaid"))
        if idx >= 0: self.status_f.setCurrentIndex(idx)
        self.status_f.setFixedHeight(42)
        self.status_f.setStyleSheet(f"""
            QComboBox {{
                background: {T.BG};
                border: 1.5px solid {T.BORDER};
                border-radius: 10px;
                padding: 0 14px;
                color: {T.TEXT};
                font-size: 13px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url(assets/chevron-down.svg);
                width: 16px;
                height: 16px;
            }}
        """)
        form.addRow(lbl6, self.status_f)

        lay.addLayout(form)
        lay.addSpacing(10)

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

    def _on_tenant_changed(self):
        tid = self.tenant_f.currentData()
        if not tid: return
        from database.repositories import get_unpaid_payments_for_tenant
        unpaid = get_unpaid_payments_for_tenant(tid)
        if unpaid:
            rec = unpaid[0] # Suggest the oldest unpaid
            self.suggestion_banner.setText(f"💡 Found an Unpaid record for {rec['due'][:7]}. Auto-filled details.")
            self.suggestion_banner.show()
            self.amount_f.setText(str(rec["amount"]))
            self.due_f.setDate(QDate.fromString(rec["due"], "yyyy-MM-dd"))
            self.status_f.setCurrentText("Paid")
            self.paid_f.setDate(QDate.currentDate())
        else:
            self.suggestion_banner.hide()

    def _on_accept(self):
        tid = self.tenant_f.currentData()
        self.record["tenant_id"]     = str(tid) if tid is not None else ""
        self.record["tenant"]        = self.tenant_f.currentText().split(" (T-")[0] if self.tenant_f.currentText() else ""
        self.record["amount"]        = self.amount_f.text().strip()
        self.record["due"]           = self.due_f.date().toString("yyyy-MM-dd")
        self.record["paid_on"]       = self.paid_f.date().toString("yyyy-MM-dd")
        self.record["type"]          = self.type_f.currentText()
        self.record["status"]        = self.status_f.currentText()
        if not self.record["tenant_id"]:
            QMessageBox.warning(self, "Validation", "Please select a tenant.")
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
        
        self._month_picker = MonthPicker(self.current_month)
        self._month_picker.month_changed.connect(self._change_month)
        filter_row.addWidget(self._month_picker)
        self._search = search_bar("Search by tenant or payment ID…")
        self._search.textChanged.connect(lambda _: self._apply_filters())
        filter_row.addWidget(self._search, 1)

        self._filter_btn = filter_button("Filter")
        menu = QMenu(self._filter_btn)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {T.SURFACE}; border: 1px solid {T.BORDER}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px 8px 24px; border-radius: 4px; color: {T.TEXT}; }}
            QMenu::item:selected {{ background-color: {T.BG}; color: {T.PRIMARY}; }}
            QMenu::indicator {{ width: 0px; height: 0px; }}
        """)
        
        method_menu = menu.addMenu("Payment Type")
        self._method_group = QActionGroup(self)
        for m in ["All Types", "Regular", "Deposit", "Summer"]:
            act = method_menu.addAction(m)
            act.setCheckable(True)
            if m == "All Types": act.setChecked(True)
            self._method_group.addAction(act)
            
        status_menu = menu.addMenu("Status")
        self._status_group = QActionGroup(self)
        for s in ["All Statuses", "Paid", "Unpaid", "Overdue"]:
            act = status_menu.addAction(s)
            act.setCheckable(True)
            if s == "All Statuses": act.setChecked(True)
            self._status_group.addAction(act)
            
        self._method_group.triggered.connect(lambda _: self._apply_filters())
        self._status_group.triggered.connect(lambda _: self._apply_filters())
        
        self._filter_btn.setMenu(menu)
        filter_row.addWidget(self._filter_btn)

        self._add_btn  = primary_button("Add Payment", "plus")
        self._add_btn.clicked.connect(self._add_payment)
        filter_row.addWidget(self._add_btn)
        card.body.addLayout(filter_row)

        self._tbl = styled_table([
            "Tenant", "Amount (₱)", "Due Date", "Date Paid", "Type", "Status", "Action"
        ])
        self._tbl.horizontalHeader().sortIndicatorChanged.connect(self._on_sort)
        self._sort_col = -1
        self._sort_order = Qt.AscendingOrder
        
        from widgets.components import update_table_headers
        update_table_headers(self._tbl, self._sort_col, self._sort_order)
        
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

    def _change_month(self, new_month: str = None):
        if new_month is None:
            new_month = self._month_picker.value()
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
            set_table_item(self._tbl, r, 0, p["tenant"])
            set_table_item(self._tbl, r, 1, f"₱ {int(p['amount']):,}")
            set_table_item(self._tbl, r, 2, p.get("due", "—"))
            set_table_item(self._tbl, r, 3, (p.get("paid_on") if p.get("paid_on") and p.get("paid_on") != "NULL" else "—"))
            set_table_item(self._tbl, r, 4, p.get("type","—"))
            set_badge_cell(self._tbl, r, 5, p["status"])
            
            pid = str(p["id"])
            action_widget = table_action_cell(
                on_edit=lambda checked, pid=pid: self._edit_payment(pid),
                on_delete=lambda checked, pid=pid: self._delete_payment(pid)
            )
            self._tbl.setCellWidget(r, 6, action_widget)
        self._count_lbl.setText(f"Showing {len(page_data)} of {len(data)} payment records")

    def _apply_filters(self, reset_page: bool = True):
        q = self._search.text().lower()
        mf = self._method_group.checkedAction().text() if self._method_group.checkedAction() else "All Types"
        sf = self._status_group.checkedAction().text() if self._status_group.checkedAction() else "All Statuses"
        filtered = [
            p for p in self._data
            if (q in str(p.get("tenant", "")).lower() or q in str(p.get("id", "")).lower())
            and (mf == "All Types" or p.get("type", "") == mf)
            and (sf == "All Statuses" or p["status"] == sf)
        ]
        
        if hasattr(self, "_sort_col") and 0 <= self._sort_col < 6:
            keys = ["tenant", "amount", "due", "paid_on", "type", "status"]
            k = keys[self._sort_col]
            rev = (self._sort_order == Qt.DescendingOrder)
            def sort_key(x):
                val = x.get(k, "")
                if k == "amount":
                    try: return float(val)
                    except: return 0.0
                return str(val).lower()
            filtered.sort(key=sort_key, reverse=rev)

        if reset_page:
            self._pagination.current_page = 1
        self._reload_table(filtered)

    def _on_sort(self, col, order):
        if col == 6: return # Action column
        
        if self._sort_col == col:
            self._sort_order = Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self._sort_col = col
            self._sort_order = Qt.AscendingOrder
            
        from widgets.components import update_table_headers
        update_table_headers(self._tbl, self._sort_col, self._sort_order)
        self._apply_filters(reset_page=False)

    def _filter_table(self, _): self._apply_filters()

    def _selected_index(self) -> int | None:
        rows = self._tbl.selectionModel().selectedRows()
        if not rows: return None
        pid = self._tbl.item(rows[0].row(), 0).text()
        for i, p in enumerate(self._data):
            if str(p.get("id")) == pid: return i
        return None

    def refresh(self):
        from database.repositories import get_payments
        self._data = get_payments(self.current_month)
        self._update_kpis()
        self._apply_filters(reset_page=False)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_payment(self):
        dlg = PaymentDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            from database.repositories import add_payment
            if add_payment(rec):
                self.refresh()
                Toast("Payment recorded successfully.", "green").show_in(self)

    def _edit_payment(self, pid: str = None):
        if not isinstance(pid, str):
            idx = self._selected_index()
        else:
            idx = next((i for i, p in enumerate(self._data) if str(p.get("id")) == pid), None)
            
        if idx is None:
            QMessageBox.information(self, "Select Payment", "Please select a payment record first.")
            return
        dlg = PaymentDialog(record=self._data[idx], parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            edit_pid = self._data[idx].get("id")
            from database.repositories import update_payment
            if edit_pid is not None:
                update_payment(int(edit_pid), rec)
            self.refresh()
            Toast("Payment updated successfully.", "blue").show_in(self)

    def _delete_payment(self, pid: str = None):
        if not isinstance(pid, str):
            idx = self._selected_index()
        else:
            idx = next((i for i, p in enumerate(self._data) if str(p.get("id")) == pid), None)
            
        if idx is None:
            QMessageBox.information(self, "Select Payment", "Please select a payment to delete.")
            return
        p_id = self._data[idx].get("id", "Unknown")
        ans = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete payment record {p_id}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            del_pid = self._data[idx].get("id")
            from database.repositories import delete_payment
            if del_pid is not None:
                delete_payment(int(del_pid))
            self.refresh()
            Toast("Payment deleted.", "red").show_in(self)
