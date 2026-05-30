"""
pages/rooms.py — Room Management page
======================================
CRUD for rental rooms.  Status is colour-coded with badges.

TODO(DB): Replace ROOMS list operations with SQLite queries.
"""

from __future__ import annotations

import copy
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QMessageBox, QAbstractItemView,
)

from theme import T
from data.mock_data import ROOMS
from widgets.components import (
    Card, section_title, styled_table, set_table_item, set_badge_cell,
    primary_button, ghost_button, danger_button, search_bar,
    MiniInsightCard, KPICard,
)
from PySide6.QtWidgets import QGridLayout


# ---------------------------------------------------------------------------
# Add / Edit dialog
# ---------------------------------------------------------------------------

class RoomDialog(QDialog):
    def __init__(self, record: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Room" if record else "Add New Room")
        self.setMinimumWidth(400)
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
            le = QLineEdit(str(val)); le.setPlaceholderText(ph)
            le.setFixedHeight(42)
            le.setStyleSheet(
                f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
                f"QLineEdit:focus {{ border:1.5px solid {T.PRIMARY}; }}"
            )
            return le

        def combo(options, val=""):
            cb = QComboBox(); cb.addItems(options)
            idx = cb.findText(val)
            if idx >= 0: cb.setCurrentIndex(idx)
            cb.setFixedHeight(42)
            cb.setStyleSheet(
                f"QComboBox {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
                f"QComboBox::drop-down {{ border:none; }}"
            )
            return cb

        lbl = QLabel("Room Number"); lbl.setStyleSheet(lbl_style)
        self.num_f = field("e.g. 101", self.record.get("number", ""))
        form.addRow(lbl, self.num_f)

        lbl2 = QLabel("Room Type"); lbl2.setStyleSheet(lbl_style)
        self.type_f = combo(["Single","Double","Suite","Studio"], self.record.get("type","Single"))
        form.addRow(lbl2, self.type_f)

        lbl3 = QLabel("Capacity"); lbl3.setStyleSheet(lbl_style)
        self.cap_f = field("e.g. 2", self.record.get("capacity", ""))
        form.addRow(lbl3, self.cap_f)

        lbl4 = QLabel("Monthly Rent (₱)"); lbl4.setStyleSheet(lbl_style)
        self.rent_f = field("e.g. 5000", self.record.get("rent", ""))
        form.addRow(lbl4, self.rent_f)

        lbl5 = QLabel("Status"); lbl5.setStyleSheet(lbl_style)
        self.status_f = combo(["Occupied","Vacant","Maintenance"], self.record.get("status","Vacant"))
        form.addRow(lbl5, self.status_f)

        lay.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Save Room")
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
        self.record["number"]   = self.num_f.text().strip()
        self.record["type"]     = self.type_f.currentText()
        self.record["capacity"] = self.cap_f.text().strip()
        self.record["rent"]     = self.rent_f.text().strip()
        self.record["status"]   = self.status_f.currentText()
        if not self.record["number"]:
            QMessageBox.warning(self, "Validation", "Room number is required.")
            return
        self.accept()


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

class RoomsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = list(ROOMS)
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

        root.addWidget(section_title("Room Management", "Track and manage all your rental units"))

        # ── Summary KPIs ─────────────────────────────────────────────────────
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(20)
        total    = len(self._data)
        occupied = sum(1 for r in self._data if r["status"] == "Occupied")
        vacant   = sum(1 for r in self._data if r["status"] == "Vacant")
        maint    = sum(1 for r in self._data if r["status"] == "Maintenance")
        kpi_row.addWidget(KPICard("Total Rooms",    str(total),    "door",   T.PRIMARY, T.PRIMARY_SOFT, "",  True, "All units"))
        kpi_row.addWidget(KPICard("Occupied",       str(occupied), "users",  T.SUCCESS, T.SUCCESS_SOFT, "",  True, "Tenants housed"))
        kpi_row.addWidget(KPICard("Vacant",         str(vacant),   "door",   T.WARNING, T.WARNING_SOFT, "",  False,"Available now"))
        kpi_row.addWidget(KPICard("Under Maintenance",str(maint),  "gear",   T.DANGER,  T.DANGER_SOFT,  "",  False,"Currently offline"))
        root.addLayout(kpi_row)

        # ── Toolbar ───────────────────────────────────────────────────────────
        card = Card(padding=20)
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        self._search = search_bar("Search room number, type, or status…")
        self._search.textChanged.connect(self._filter_table)
        toolbar.addWidget(self._search, 1)

        self._add_btn  = primary_button("Add Room", "plus")
        self._edit_btn = ghost_button("Edit", "edit")
        self._del_btn  = danger_button("Delete", "trash")
        self._add_btn.clicked.connect(self._add_room)
        self._edit_btn.clicked.connect(self._edit_room)
        self._del_btn.clicked.connect(self._delete_room)
        toolbar.addWidget(self._add_btn)
        toolbar.addWidget(self._edit_btn)
        toolbar.addWidget(self._del_btn)
        card.body.addLayout(toolbar)

        self._tbl = styled_table(
            ["Room ID", "Room Number", "Type", "Capacity", "Monthly Rent", "Status"]
        )
        self._tbl.setMinimumHeight(380)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        card.body.addWidget(self._tbl)

        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12px;")
        card.body.addWidget(self._count_lbl)

        root.addWidget(card)
        root.addStretch(1)

    # ── Table helpers ─────────────────────────────────────────────────────────

    def _reload_table(self, rows: list[dict] | None = None):
        data = rows if rows is not None else self._data
        self._tbl.setRowCount(0)
        for r_data in data:
            if "id" not in r_data:
                r_data["id"] = f"R-{r_data.get('number','??')}"
            r = self._tbl.rowCount(); self._tbl.insertRow(r)
            set_table_item(self._tbl, r, 0, r_data["id"])
            set_table_item(self._tbl, r, 1, r_data["number"])
            set_table_item(self._tbl, r, 2, r_data["type"])
            set_table_item(self._tbl, r, 3, str(r_data["capacity"]))
            set_table_item(self._tbl, r, 4, f"₱ {int(r_data['rent']):,}")
            set_badge_cell(self._tbl, r, 5, r_data["status"])
        self._count_lbl.setText(f"{len(data)} room(s) listed")

    def _filter_table(self, query: str):
        q = query.lower()
        filtered = [r for r in self._data
                    if q in r.get("number","").lower()
                    or q in r.get("type","").lower()
                    or q in r.get("status","").lower()]
        self._reload_table(filtered)

    def _selected_index(self) -> int | None:
        rows = self._tbl.selectionModel().selectedRows()
        if not rows:
            return None
        rid = self._tbl.item(rows[0].row(), 0).text()
        for i, r in enumerate(self._data):
            if r.get("id") == rid:
                return i
        return None

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_room(self):
        dlg = RoomDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            rec["id"] = f"R-{rec['number']}"
            self._data.append(rec)
            # TODO(DB): INSERT INTO rooms VALUES (...)
            self._reload_table()

    def _edit_room(self):
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select a Room", "Please select a room first.")
            return
        dlg = RoomDialog(record=self._data[idx], parent=self)
        if dlg.exec() == QDialog.Accepted:
            self._data[idx] = dlg.record
            # TODO(DB): UPDATE rooms SET ... WHERE id=?
            self._reload_table()

    def _delete_room(self):
        idx = self._selected_index()
        if idx is None:
            QMessageBox.information(self, "Select a Room", "Please select a room to delete.")
            return
        num = self._data[idx]["number"]
        ans = QMessageBox.question(
            self, "Confirm Delete",
            f"Remove room '{num}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            self._data.pop(idx)
            # TODO(DB): DELETE FROM rooms WHERE id=?
            self._reload_table()
