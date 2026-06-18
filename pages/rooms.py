"""
pages/rooms.py — Room Management page
======================================
CRUD for rental rooms.  Status is colour-coded with badges.

TODO(DB): Replace ROOMS list operations with SQLite queries.
"""

from __future__ import annotations

import copy
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QListView, QDialogButtonBox,
    QMessageBox, QAbstractItemView, QGridLayout, QMenu,
)

from theme import T
from database.repositories import get_rooms
from widgets.components import (
    Card, section_title, styled_table, set_table_item, set_badge_cell,
    primary_button, ghost_button, danger_button, search_bar,
    MiniInsightCard, KPICard, PaginationControl, table_action_cell, filter_button, Toast
)


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
            cb = QComboBox(); cb.setView(QListView()); cb.addItems(options)
            idx = cb.findText(val)
            if idx >= 0: cb.setCurrentIndex(idx)
            cb.setFixedHeight(42)
            cb.setStyleSheet(f"""
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
            return cb

        lbl = QLabel("Room Number"); lbl.setStyleSheet(lbl_style)
        self.num_f = field("e.g. 101", self.record.get("number", ""))
        form.addRow(lbl, self.num_f)

        lbl2 = QLabel("Room Type"); lbl2.setStyleSheet(lbl_style)
        self.type_f = combo(["Solo","Bedspacer","Solo Deluxe","Bedspacer Deluxe"], self.record.get("type","Solo"))
        form.addRow(lbl2, self.type_f)

        lbl3 = QLabel("Capacity"); lbl3.setStyleSheet(lbl_style)
        self.cap_f = field("e.g. 2", self.record.get("capacity", ""))
        form.addRow(lbl3, self.cap_f)

        lbl4 = QLabel("Monthly Rent (₱)"); lbl4.setStyleSheet(lbl_style)
        self.rent_f = field("e.g. 5000", self.record.get("rent", ""))
        form.addRow(lbl4, self.rent_f)

        lay.addLayout(form)

        # Lock capacity to 1 for Solo types
        def _on_type_changed(t):
            if t in ("Solo", "Solo Deluxe"):
                self.cap_f.setText("1")
                self.cap_f.setReadOnly(True)
                self.cap_f.setStyleSheet(
                    f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                    f" border-radius:10px; padding:0 14px; color:{T.TEXT_MUTED}; font-size:13px; }}"
                )
            else:
                self.cap_f.setReadOnly(False)
                self.cap_f.setStyleSheet(
                    f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER};"
                    f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px; }}"
                    f"QLineEdit:focus {{ border:1.5px solid {T.PRIMARY}; }}"
                )
        self.type_f.currentTextChanged.connect(_on_type_changed)
        _on_type_changed(self.type_f.currentText())  # apply on open

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
        ok = True
        base = "border-radius:10px; padding:0 14px; font-size:13px;"
        ok_style  = f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.BORDER}; color:{T.TEXT}; {base} }}"
        err_style = f"QLineEdit {{ background:{T.BG}; border:1.5px solid {T.DANGER}; color:{T.TEXT}; {base} }}"

        number = self.num_f.text().strip()

        if not re.match(r'^[A-Za-z0-9-]+$', number):
            self.num_f.setStyleSheet(err_style)
            ok = False
        else:
            self.num_f.setStyleSheet(ok_style)

        cap = self.cap_f.text().strip()
        if not cap or not cap.isdigit():
            self.cap_f.setStyleSheet(err_style)
            ok = False
        else:
            self.cap_f.setStyleSheet(ok_style)

        rent = self.rent_f.text().strip()

        try:
            rent = round(float(rent))
            if rent < 0:
                raise ValueError
            self.rent_f.setStyleSheet(ok_style)
        except ValueError:
            self.rent_f.setStyleSheet(err_style)
            ok = False

        if not ok:
            return

        # Check duplicate room number (skip self when editing)
        from database.repositories import get_rooms
        existing = get_rooms()
        own_id = str(self.record.get("id", ""))
        for r in existing:
            if r["number"] == number and str(r.get("id", "")) != own_id:
                self.num_f.setStyleSheet(err_style)
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Duplicate", f"Room number '{number}' already exists.")
                return

        self.record["number"]   = number
        self.record["type"]     = self.type_f.currentText()
        self.record["capacity"] = cap
        self.record["rent"]     = rent
        self.record["status"]   = "Vacant"
        self.accept()


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

class RoomsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = get_rooms()
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

        root.addWidget(section_title("Room Management", "Track and manage all your rental units"))

        # ── Summary KPIs ─────────────────────────────────────────────────────
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(20)
        total    = len(self._data)
        occupied = sum(1 for r in self._data if r["status"] in ("Full", "Partially Occupied"))
        vacant   = sum(1 for r in self._data if r["status"] == "Vacant")
        kpi_row.addWidget(KPICard("Total Rooms",    str(total),    "door",   T.PRIMARY, T.PRIMARY_SOFT, "",  True, "All units"))
        kpi_row.addWidget(KPICard("Occupied",       str(occupied), "users",  T.SUCCESS, T.SUCCESS_SOFT, "",  True, "Tenants housed"))
        kpi_row.addWidget(KPICard("Vacant",         str(vacant),   "door",   T.WARNING, T.WARNING_SOFT, "",  False,"Available now"))
        root.addLayout(kpi_row)

        # ── Toolbar ───────────────────────────────────────────────────────────
        card = Card(padding=20)
        toolbar = QHBoxLayout(); toolbar.setSpacing(12)
        self._search = search_bar("Search room number, type, or status…")
        self._search.textChanged.connect(lambda _: self._apply_filters())
        toolbar.addWidget(self._search, 1)

        self._filter_btn = filter_button("Filter")
        menu = QMenu(self._filter_btn)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {T.SURFACE}; border: 1px solid {T.BORDER}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 8px 24px 8px 24px; border-radius: 4px; color: {T.TEXT}; }}
            QMenu::item:selected {{ background-color: {T.BG}; color: {T.PRIMARY}; }}
            QMenu::indicator {{ width: 0px; height: 0px; }}
        """)
        
        type_menu = menu.addMenu("Room Type")
        self._type_group = QActionGroup(self)
        for t in ["All Types", "Solo", "Bedspacer", "Solo Deluxe", "Bedspacer Deluxe"]:
            act = type_menu.addAction(t)
            act.setCheckable(True)
            if t == "All Types": act.setChecked(True)
            self._type_group.addAction(act)
            
        status_menu = menu.addMenu("Status")
        self._status_group = QActionGroup(self)
        for s in ["All Statuses", "Full", "Partially Occupied", "Vacant"]:
            act = status_menu.addAction(s)
            act.setCheckable(True)
            if s == "All Statuses": act.setChecked(True)
            self._status_group.addAction(act)
            
        self._type_group.triggered.connect(lambda _: self._apply_filters())
        self._status_group.triggered.connect(lambda _: self._apply_filters())
        
        self._filter_btn.setMenu(menu)
        toolbar.addWidget(self._filter_btn)

        self._add_btn  = primary_button("Add Room", "plus")
        self._add_btn.clicked.connect(self._add_room)
        toolbar.addWidget(self._add_btn)
        card.body.addLayout(toolbar)

        self._tbl = styled_table(
            ["Room ID", "Room Number", "Type", "Monthly Rent", "Occupancy", "Occupant Sex", "Status", "Action"]
        )
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

    def _reload_table(self, rows: list[dict] | None = None):
        data = rows if rows is not None else self._data
        self._filtered_data = data
        self._pagination.set_total_items(len(data))
        
        start_idx = (self._pagination.current_page - 1) * self._pagination.items_per_page
        end_idx = start_idx + self._pagination.items_per_page
        page_data = data[start_idx:end_idx]

        self._tbl.setRowCount(0)
        for r_data in page_data:
            if "id" not in r_data:
                r_data["id"] = f"R-{r_data.get('number','??')}"
            r = self._tbl.rowCount(); self._tbl.insertRow(r)
            set_table_item(self._tbl, r, 0, r_data["id"])
            set_table_item(self._tbl, r, 1, r_data["number"])
            set_table_item(self._tbl, r, 2, r_data["type"])
            set_table_item(self._tbl, r, 3, f"₱ {int(r_data['rent']):,}")
            set_table_item(self._tbl, r, 4, f"{r_data.get('occupied_slots', 0)}/{r_data['capacity']}")
            set_table_item(self._tbl, r, 5, r_data.get("occupant_sex", "—"))
            set_badge_cell(self._tbl, r, 6, r_data["status"])
            
            rid = str(r_data["id"])
            action_widget = table_action_cell(
                on_edit=lambda checked, rid=rid: self._edit_room(rid),
                on_delete=lambda checked, rid=rid: self._delete_room(rid)
            )
            self._tbl.setCellWidget(r, 7, action_widget)
        self._count_lbl.setText(f"Showing {len(page_data)} of {len(data)} rooms")

    def _apply_filters(self, reset_page: bool = True):
        q = self._search.text().lower()
        tf = self._type_group.checkedAction().text() if self._type_group.checkedAction() else "All Types"
        sf = self._status_group.checkedAction().text() if self._status_group.checkedAction() else "All Statuses"
        filtered = [
            r for r in self._data
            if (q in r.get("number","").lower() or q in r.get("type","").lower() or q in r.get("status","").lower())
            and (tf == "All Types" or r.get("type") == tf)
            and (sf == "All Statuses" or r.get("status") == sf)
        ]
        
        if hasattr(self, "_sort_col") and 0 <= self._sort_col < 7:
            keys = ["id", "number", "type", "rent", "occupied_slots", "occupant_sex", "status"]
            k = keys[self._sort_col]
            rev = (self._sort_order == Qt.DescendingOrder)
            def sort_key(x):
                val = x.get(k, "")
                if k in ("occupied_slots", "rent"):
                    try: return float(val)
                    except: return 0.0
                return str(val).lower()
            filtered.sort(key=sort_key, reverse=rev)

        if reset_page:
            self._pagination.current_page = 1
        self._reload_table(filtered)

    def _on_sort(self, col, order):
        if col == 7: return # Action column
        
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
        if not rows:
            return None
        rid = self._tbl.item(rows[0].row(), 0).text()
        for i, r in enumerate(self._data):
            if str(r.get("id")) == rid:
                return i
        return None

    def refresh(self):
        from database.repositories import get_rooms
        self._data = get_rooms()
        self._apply_filters(reset_page=False)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_room(self):
        dlg = RoomDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            from database.repositories import add_room
            if add_room(rec):
                self.refresh()
                Toast("Room created successfully.", "green").show_in(self)

    def _edit_room(self, rid: str = None):
        if not isinstance(rid, str):
            idx = self._selected_index()
        else:
            idx = next((i for i, r in enumerate(self._data) if str(r.get("id")) == rid), None)
            
        if idx is None:
            QMessageBox.information(self, "Select a Room", "Please select a room first.")
            return
        dlg = RoomDialog(record=self._data[idx], parent=self)
        if dlg.exec() == QDialog.Accepted:
            rec = dlg.record
            edit_rid = self._data[idx].get("id")
            from database.repositories import update_room
            if edit_rid is not None:
                update_room(edit_rid, rec)
            self.refresh()
            Toast("Room updated successfully.", "blue").show_in(self)

    def _delete_room(self, rid: str = None):
        if not isinstance(rid, str):
            idx = self._selected_index()
        else:
            idx = next((i for i, r in enumerate(self._data) if str(r.get("id")) == rid), None)
            
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
            del_rid = self._data[idx].get("id")
            from database.repositories import delete_room
            if del_rid is not None:
                delete_room(del_rid)
            self.refresh()
            Toast("Room deleted.", "red").show_in(self)
