"""
pages/tenants.py — Tenant Management page
==========================================
Full CRUD interface: Add / Edit / Delete tenants with a live search filter.

TODO(DB): Replace TENANTS list operations with SQLite INSERT / UPDATE / DELETE.
"""

from __future__ import annotations

import copy
from PySide6.QtCore import Qt, QSize, QDate
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QMessageBox, QFrame, QDateEdit, QAbstractItemView, QMenu, QListView,
    QHeaderView
)

from theme import T
from database.repositories import get_tenants
from widgets.components import (
    Card, section_title, styled_table, set_table_item, Toast, 
    primary_button, ghost_button, danger_button, search_bar, PaginationControl, table_action_cell, filter_button
)


# ---------------------------------------------------------------------------
# Add / Edit dialog
# ---------------------------------------------------------------------------

class TenantDialog(QDialog):
    """Modal form for adding or editing a tenant record."""

    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Tenant" if record else "Add New Tenant")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{T.SURFACE};")
        self.record = copy.deepcopy(record) if record else {}
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setSpacing(20); lay.setContentsMargins(28, 28, 28, 20)

        title = QLabel(self.windowTitle())
        title.setStyleSheet(f"color:{T.TEXT}; font-size:17px; font-weight:700;")
        lay.addWidget(title)

        form = QFormLayout(); form.setSpacing(14); form.setLabelAlignment(Qt.AlignLeft)

        def field(placeholder: str, value: str = "") -> QLineEdit:
            le = QLineEdit(value); le.setPlaceholderText(placeholder)
            le.setFixedHeight(42)
            le.setStyleSheet(
                f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
                f"QLineEdit:focus {{ border:1.5px solid {T.PRIMARY}; }}"
            )
            return le

        label_style = f"color:{T.TEXT}; font-size:13px; font-weight:600;"

        lbl = QLabel("Full Name"); lbl.setStyleSheet(label_style)
        self.name_f = field("e.g. Maria Santos", self.record.get("name", ""))
        form.addRow(lbl, self.name_f)

        lbl2 = QLabel("Contact Number"); lbl2.setStyleSheet(label_style)
        self.contact_f = field("e.g. 09171234567", self.record.get("contact", ""))
        form.addRow(lbl2, self.contact_f)

        lbl3 = QLabel("Birthdate"); lbl3.setStyleSheet(label_style)
        self.birthdate_f = QDateEdit()
        self.birthdate_f.setCalendarPopup(True)
        self.birthdate_f.setFixedHeight(42)
        self.birthdate_f.setStyleSheet(f"""
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
        date_str = self.record.get("birthdate", "2000-01-01")
        self.birthdate_f.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        form.addRow(lbl3, self.birthdate_f)

        lbl4 = QLabel("Sex"); lbl4.setStyleSheet(label_style)
        self.sex_f = QComboBox(); self.sex_f.setView(QListView()); self.sex_f.addItems(["Male", "Female",])
        self.sex_f.setView(QListView())
        sex_val = self.record.get("sex", "Female")
        idx = self.sex_f.findText(sex_val)
        if idx >= 0: self.sex_f.setCurrentIndex(idx)
        self.sex_f.setFixedHeight(42)
        self.sex_f.setStyleSheet(f"""
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
        form.addRow(lbl4, self.sex_f)


        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Save Tenant")
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
        self.record["name"]    = self.name_f.text().strip()
        self.record["contact"] = self.contact_f.text().strip()
        self.record["birthdate"] = self.birthdate_f.date().toString("yyyy-MM-dd")
        self.record["sex"]     = self.sex_f.currentText()
        if not self.record["name"]:
            QMessageBox.warning(self, "Validation", "Full name is required.")
            return
        self.accept()



# ---------------------------------------------------------------------------
# View page
# ---------------------------------------------------------------------------

class TenantDetailDialog(QDialog):
    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Tenant — {record.get('name', '')}")
        self.setMinimumWidth(540)
        self.setStyleSheet(f"background:{T.SURFACE};")
        self._build(record)

    def _build(self, t: dict):
        from database.repositories import get_payments
        from widgets.components import styled_table, set_table_item, set_badge_cell
        from PySide6.QtWidgets import QGridLayout, QHeaderView
        from PySide6.QtGui import QColor

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        # Title
        title = QLabel(t.get("name", ""))
        title.setStyleSheet(f"color:{T.TEXT}; font-size:18px; font-weight:700;")
        lay.addWidget(title)

        # Detail grid
        grid = QGridLayout(); grid.setSpacing(12)
        details = [
            ("Tenant ID",    str(t.get("id", "—"))),
            ("Contact",      t.get("contact", "—")),
            ("Birthdate",    t.get("birthdate", "—")),
            ("Sex",          t.get("sex", "—")),
            ("Room",         str(t.get("room", "—"))),
            ("Start Date",   t.get("start_date", "—")),
            ("End Date",     t.get("end_date", "—") or "Active"),
        ]
        lbl_style = f"color:{T.TEXT_MUTED}; font-size:12px; font-weight:600;"
        val_style = f"color:{T.TEXT}; font-size:13px; font-weight:500;"
        for i, (label, value) in enumerate(details):
            col = (i % 2) * 2
            row = i // 2
            l = QLabel(label); l.setStyleSheet(lbl_style)
            v = QLabel(value); v.setStyleSheet(val_style)
            grid.addWidget(l, row, col)
            grid.addWidget(v, row, col + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        lay.addLayout(grid)

        # Divider
        div = QLabel(); div.setFixedHeight(1)
        div.setStyleSheet(f"background:{T.BORDER};")
        lay.addWidget(div)

        # Payment history
        sub = QLabel("Payment History")
        sub.setStyleSheet(f"color:{T.TEXT}; font-size:14px; font-weight:700;")
        lay.addWidget(sub)

        tbl = styled_table(["ID", "Amount", "Due Date", "Paid On", "Type", "Status"])
        tbl.setFixedHeight(240)

        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        tbl.setColumnWidth(4, 120)

        tid = str(t.get("id", ""))
        payments = [p for p in get_payments() if str(p.get("tenant_id", "")) == tid]
        payments.sort(key=lambda p: p.get("due", ""), reverse=True)

        for p in payments:
            r = tbl.rowCount(); tbl.insertRow(r)
            set_table_item(tbl, r, 0, f"₱ {int(p.get('amount', 0)):,}")
            set_table_item(tbl, r, 1, p.get("due", ""))
            set_table_item(tbl, r, 2, p.get("paid_on", "") or "—")
            set_table_item(tbl, r, 3, p.get("type", ""))
            set_badge_cell(tbl, r, 4, p.get("status", ""))

        if not payments:
            tbl.insertRow(0)
            from PySide6.QtWidgets import QTableWidgetItem
            item = QTableWidgetItem("No payment records found.")
            item.setTextAlignment(Qt.AlignCenter)
            from PySide6.QtGui import QColor
            item.setForeground(QColor(T.TEXT_MUTED))
            tbl.setItem(0, 0, item)
            tbl.setSpan(0, 0, 1, 5)

        lay.addWidget(tbl)

        close_btn = primary_button("Close")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, 0, Qt.AlignRight)


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

class TenantsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = get_tenants()  # local copy for runtime edits
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

        root.addWidget(section_title("Tenant Management", "Add, view, and manage your tenants"))

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        self._search = search_bar("Search by name or contact…")
        self._search.textChanged.connect(lambda _: self._filter_table(self._search.text()))
        toolbar.addWidget(self._search, 1)

        self._filter_btn = filter_button("Filter")
        menu = QMenu(self._filter_btn)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {T.SURFACE}; border: 1px solid {T.BORDER}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px 8px 24px; border-radius: 4px; color: {T.TEXT}; }}
            QMenu::item:selected {{ background-color: {T.BG}; color: {T.PRIMARY}; }}
        """)
        
        self._sex_group = QActionGroup(self)
        for s in ["All Sexes", "Female", "Male"]:
            act = menu.addAction(s)
            act.setCheckable(True)
            if s == "All Sexes": act.setChecked(True)
            self._sex_group.addAction(act)
            
        self._sex_group.triggered.connect(lambda _: self._filter_table(self._search.text()))
        self._filter_btn.setMenu(menu)
        toolbar.addWidget(self._filter_btn)

        self._add_btn = primary_button("Add Tenant", "plus")
        self._add_btn.clicked.connect(self._add_tenant)
        toolbar.addWidget(self._add_btn)

        card = Card(padding=20)
        card.body.addLayout(toolbar)

        # Table
        self._tbl = styled_table(
            ["Tenant ID", "Full Name", "Contact", "Birthdate", "Sex", "Room", "Start Date", "End Date", "Action"]
        )
        self._tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tbl.horizontalHeader().sortIndicatorChanged.connect(self._on_sort)
        self._sort_col = -1
        self._sort_order = Qt.AscendingOrder
        
        from widgets.components import update_table_headers
        update_table_headers(self._tbl, self._sort_col, self._sort_order)
        
        self._tbl.setMinimumHeight(380)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tbl.doubleClicked.connect(self._view_tenant)
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

    # ── Table helpers ────────────────────────────────────────────────────────

    def _reload_table(self, rows: list[dict] | None = None):
        data = rows if rows is not None else self._data
        self._filtered_data = data
        self._pagination.set_total_items(len(data))
        
        start_idx = (self._pagination.current_page - 1) * self._pagination.items_per_page
        end_idx = start_idx + self._pagination.items_per_page
        page_data = data[start_idx:end_idx]

        self._tbl.setRowCount(0)
        for i, t in enumerate(page_data):
            # auto-generate ID if missing
            if "id" not in t:
                t["id"] = f"T-{len(self._data):03d}"
            r = self._tbl.rowCount(); self._tbl.insertRow(r)
            for col, key in enumerate(["id","name","contact","birthdate","sex","room","start_date","end_date"]):
                set_table_item(self._tbl, r, col, str(t.get(key, "")))
            
            tid = str(t["id"])
            action_widget = table_action_cell(
                on_edit=lambda checked, tid=tid: self._edit_tenant(tid),
                on_delete=lambda checked, tid=tid: self._delete_tenant(tid)
            )
            self._tbl.setCellWidget(r, 8, action_widget)
        self._count_lbl.setText(f"Showing {len(page_data)} of {len(data)} tenants")

    def _filter_table(self, query: str, reset_page: bool = True):
        q = query.lower()
        sf = self._sex_group.checkedAction().text() if self._sex_group.checkedAction() else "All Sexes"
        filtered = [t for t in self._data
                    if (q in t["name"].lower() or q in t.get("contact","").lower())
                    and (sf == "All Sexes" or t.get("sex") == sf)]
                    
        if hasattr(self, "_sort_col") and 0 <= self._sort_col < 8:
            keys = ["id", "name", "contact", "birthdate", "sex", "room", "start_date", "end_date"]
            k = keys[self._sort_col]
            rev = (self._sort_order == Qt.DescendingOrder)
            def sort_key(x):
                val = x.get(k, "")
                if k == "id":
                    try: return (0, int(val))
                    except: return (1, str(val).lower())
                return (1, str(val).lower())
            filtered.sort(key=sort_key, reverse=rev)

        if reset_page:
            self._pagination.current_page = 1
        self._reload_table(filtered)

    def _on_sort(self, col, order):
        if col == 8: return # Action column
        
        # Manually toggle order if the same column is clicked since we hide the native indicator
        if self._sort_col == col:
            self._sort_order = Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self._sort_col = col
            self._sort_order = Qt.AscendingOrder
            
        from widgets.components import update_table_headers
        update_table_headers(self._tbl, self._sort_col, self._sort_order)
        self._filter_table(self._search.text(), reset_page=False)

    def _selected_index(self) -> int | None:
        rows = self._tbl.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        tid = self._tbl.item(row, 0).text()
        for i, t in enumerate(self._data):
            if str(t.get("id")) == tid:
                return i
        return None

    def refresh(self):
        from database.repositories import get_tenants
        self._data = get_tenants()
        self._filter_table(self._search.text(), reset_page=False)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_tenant(self):
        dlg = TenantDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            from database.repositories import add_tenant
            if add_tenant(rec):
                self.refresh()
                Toast("Tenant created successfully.", "green").show_in(self)

    def _edit_tenant(self, tid: str = None):
        if not isinstance(tid, str):
            idx = self._selected_index()
        else:
            idx = next((i for i, t in enumerate(self._data) if str(t.get("id")) == tid), None)
            
        if idx is None:
            QMessageBox.information(self, "Select a Tenant", "Please select a tenant row first.")
            return
        dlg = TenantDialog(record=self._data[idx], parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            edit_tid = self._data[idx].get("id")
            from database.repositories import update_tenant
            if edit_tid is not None:
                update_tenant(int(edit_tid), rec)
            self.refresh()
            Toast("Tenant updated successfully.", "blue").show_in(self)

    def _delete_tenant(self, tid: str = None):
        if not isinstance(tid, str):
            idx = self._selected_index()
        else:
            idx = next((i for i, t in enumerate(self._data) if str(t.get("id")) == tid), None)
            
        if idx is None:
            QMessageBox.information(self, "Select a Tenant", "Please select a tenant row to delete.")
            return
        name = self._data[idx]["name"]
        ans = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to remove tenant '{name}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            del_tid = self._data[idx].get("id")
            self._data.pop(idx)
            from database.repositories import delete_tenant
            if del_tid is not None:
                delete_tenant(int(del_tid))
            self.refresh()
            Toast("Tenant deleted.", "red").show_in(self)

    def _view_tenant(self, index):
        tid = self._tbl.item(index.row(), 0).text()
        record = next((t for t in self._data if str(t.get("id")) == tid), None)
        if record:
            TenantDetailDialog(record, parent=self).exec()
