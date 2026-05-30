"""
pages/tenants.py — Tenant Management page
==========================================
Full CRUD interface: Add / Edit / Delete tenants with a live search filter.

TODO(DB): Replace TENANTS list operations with SQLite INSERT / UPDATE / DELETE.
"""

from __future__ import annotations

import copy
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QMessageBox, QFrame, QDateEdit, QAbstractItemView,
)
from PySide6.QtCore import QDate

from theme import T
from data.mock_data import TENANTS
from widgets.components import (
    Card, section_title, styled_table, set_table_item,
    primary_button, ghost_button, danger_button, search_bar,
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

        lbl3 = QLabel("Age"); lbl3.setStyleSheet(label_style)
        self.age_f = field("e.g. 28", str(self.record.get("age", "")))
        form.addRow(lbl3, self.age_f)

        lbl4 = QLabel("Sex"); lbl4.setStyleSheet(label_style)
        self.sex_f = QComboBox(); self.sex_f.addItems(["Male", "Female", "Other"])
        sex_val = self.record.get("sex", "Male")
        idx = self.sex_f.findText(sex_val)
        if idx >= 0: self.sex_f.setCurrentIndex(idx)
        self.sex_f.setFixedHeight(42)
        self.sex_f.setStyleSheet(
            f"QComboBox {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
            f"QComboBox::drop-down {{ border:none; subcontrol-position:right center; width:24px; }}"
        )
        form.addRow(lbl4, self.sex_f)

        lbl5 = QLabel("Move-in Date"); lbl5.setStyleSheet(label_style)
        self.movein_f = QDateEdit()
        self.movein_f.setCalendarPopup(True)
        self.movein_f.setFixedHeight(42)
        self.movein_f.setStyleSheet(
            f"QDateEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
        )
        date_str = self.record.get("move_in", QDate.currentDate().toString("yyyy-MM-dd"))
        self.movein_f.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
        form.addRow(lbl5, self.movein_f)

        lbl6 = QLabel("Assigned Room"); lbl6.setStyleSheet(label_style)
        self.room_f = field("e.g. 101", self.record.get("room", ""))
        form.addRow(lbl6, self.room_f)

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
        self.record["age"]     = self.age_f.text().strip()
        self.record["sex"]     = self.sex_f.currentText()
        self.record["move_in"] = self.movein_f.date().toString("yyyy-MM-dd")
        self.record["room"]    = self.room_f.text().strip()
        if not self.record["name"]:
            QMessageBox.warning(self, "Validation", "Full name is required.")
            return
        self.accept()


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

class TenantsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = list(TENANTS)  # local copy for runtime edits
        self._build()
        self._reload_table()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget(); scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 12, 28, 28); root.setSpacing(20)

        root.addWidget(section_title("Tenant Management", "Add, view, and manage your tenants"))

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        self._search = search_bar("Search by name, contact, or room…")
        self._search.textChanged.connect(self._filter_table)
        toolbar.addWidget(self._search, 1)

        self._add_btn = primary_button("Add Tenant", "plus")
        self._add_btn.clicked.connect(self._add_tenant)
        self._edit_btn = ghost_button("Edit", "edit")
        self._edit_btn.clicked.connect(self._edit_tenant)
        self._del_btn  = danger_button("Delete", "trash")
        self._del_btn.clicked.connect(self._delete_tenant)
        toolbar.addWidget(self._add_btn)
        toolbar.addWidget(self._edit_btn)
        toolbar.addWidget(self._del_btn)

        card = Card(padding=20)
        card.body.addLayout(toolbar)

        # Table
        self._tbl = styled_table(
            ["Tenant ID", "Full Name", "Contact", "Age", "Sex", "Move-in Date", "Room"]
        )
        self._tbl.setMinimumHeight(380)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        card.body.addWidget(self._tbl)

        # Row count label
        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12px;")
        card.body.addWidget(self._count_lbl)

        root.addWidget(card)
        root.addStretch(1)

    # ── Table helpers ────────────────────────────────────────────────────────

    def _reload_table(self, rows: list[dict] | None = None):
        data = rows if rows is not None else self._data
        self._tbl.setRowCount(0)
        for i, t in enumerate(data):
            # auto-generate ID if missing
            if "id" not in t:
                t["id"] = f"T-{len(self._data):03d}"
            r = self._tbl.rowCount(); self._tbl.insertRow(r)
            for col, key in enumerate(["id","name","contact","age","sex","move_in","room"]):
                set_table_item(self._tbl, r, col, str(t.get(key, "")))
        self._count_lbl.setText(f"{len(data)} tenant(s) found")

    def _filter_table(self, query: str):
        q = query.lower()
        filtered = [t for t in self._data
                    if q in t["name"].lower()
                    or q in t.get("contact","").lower()
                    or q in t.get("room","").lower()]
        self._reload_table(filtered)

    def _selected_index(self) -> int | None:
        rows = self._tbl.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        tid = self._tbl.item(row, 0).text()
        for i, t in enumerate(self._data):
            if t.get("id") == tid:
                return i
        return None

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def _add_tenant(self):
        dlg = TenantDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            rec["id"] = f"T-{(len(self._data)+1):03d}"
            self._data.append(rec)
            # TODO(DB): INSERT INTO tenants VALUES (...)
            self._reload_table()

    def _edit_tenant(self):
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select a Tenant", "Please select a tenant row first.")
            return
        dlg = TenantDialog(record=self._data[idx], parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._data[idx] = dlg.record
            # TODO(DB): UPDATE tenants SET ... WHERE id=?
            self._reload_table()

    def _delete_tenant(self):
        idx = self._selected_index()
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
            self._data.pop(idx)
            # TODO(DB): DELETE FROM tenants WHERE id=?
            self._reload_table()
