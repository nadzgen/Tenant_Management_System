"""
pages/rooms.py — Room Management page
======================================
CRUD for rental rooms.  Status is colour-coded with badges.

TODO(DB): Replace ROOMS list operations with SQLite queries.
"""

from __future__ import annotations
from datetime import date

import copy
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QDialog, QFormLayout, QLineEdit, QComboBox, QListView, QDialogButtonBox,
    QMessageBox, QAbstractItemView, QGridLayout, QMenu, QTableWidgetItem
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
# Transfer Rooms
# ---------------------------------------------------------------------------

class TransferDialog(QDialog):
    def __init__(self, tenant_name: str, current_room: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transfer Tenant")
        self.setMinimumWidth(380)
        self.setStyleSheet(f"background:{T.SURFACE};")
        self.selected_room_id = None
        self._build(tenant_name, current_room)

    def _build(self, tenant_name: str, current_room: str):
        from database.repositories import get_rooms
        from PySide6.QtWidgets import QHeaderView

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(16)

        title = QLabel(f"Transfer — {tenant_name}")
        title.setStyleSheet(f"color:{T.TEXT}; font-size:16px; font-weight:700;")
        lay.addWidget(title)

        sub = QLabel(f"Select a new room to move this tenant from Room {current_room}:")
        sub.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:12.5px;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        self._rooms = [
            r for r in get_rooms()
            if r["status"] in ("Vacant", "Partially Occupied")
            and str(r.get("number", "")) != current_room
        ]

        tbl = styled_table(["Room No.", "Type", "Occupancy", "Rent"])
        tbl.setFixedHeight(200)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        for r in self._rooms:
            row = tbl.rowCount(); tbl.insertRow(row)
            set_table_item(tbl, row, 0, str(r["number"]))
            set_table_item(tbl, row, 1, r["type"])
            set_table_item(tbl, row, 2, f"{r.get('occupied_slots',0)}/{r['capacity']}")
            set_table_item(tbl, row, 3, f"₱ {int(r['rent']):,}")

        tbl.selectionModel().selectionChanged.connect(
            lambda: self._on_select(tbl)
        )
        lay.addWidget(tbl)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Transfer")
        btns.button(QDialogButtonBox.Ok).setEnabled(False)
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            f"QPushButton {{ background:{T.PRIMARY}; color:white; border:none;"
            f" border-radius:10px; padding:8px 22px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{T.PRIMARY_DK}; }}"
        )
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(
            f"QPushButton {{ background:{T.BG}; color:{T.TEXT_MUTED}; border:1px solid {T.BORDER};"
            f" border-radius:10px; padding:8px 20px; font-size:13px; }}"
        )
        self._ok_btn = btns.button(QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_select(self, tbl):
        rows = tbl.selectionModel().selectedRows()
        if rows:
            idx = rows[0].row()
            self.selected_room_id = self._rooms[idx].get("id")
            self.selected_room_rent = self._rooms[idx].get("rent", 0)
            self._ok_btn.setEnabled(True)
        else:
            self._ok_btn.setEnabled(False)


# ---------------------------------------------------------------------------
# View Rooms page
# ---------------------------------------------------------------------------

class RoomDetailDialog(QDialog):
    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Room {record.get('number', '')} — Details")
        self.setMinimumWidth(520)
        self.setStyleSheet(f"background:{T.SURFACE};")
        self._build(record)

    def _build(self, r: dict):
        from database.repositories import get_tenants
        from widgets.components import styled_table, set_table_item, set_badge_cell

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        # Title
        title = QLabel(f"Room {r.get('number', '')}")
        title.setStyleSheet(f"color:{T.TEXT}; font-size:18px; font-weight:700;")
        lay.addWidget(title)

        # Detail grid
        grid = QGridLayout(); grid.setSpacing(12)
        details = [
            ("Room Type",    r.get("type", "—")),
            ("Monthly Rent", f"₱ {int(r.get('rent', 0)):,}"),
            ("Capacity",     str(r.get("capacity", "—"))),
            ("Occupancy",    f"{r.get('occupied_slots', 0)}/{r.get('capacity', 0)}"),
            ("Status",       r.get("status", "—")),
            ("Occupant Sex", r.get("occupant_sex", "—")),
        ]
        lbl_style  = f"color:{T.TEXT_MUTED}; font-size:12px; font-weight:600;"
        val_style  = f"color:{T.TEXT}; font-size:13px; font-weight:500;"
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

        # Tenants table
        sub = QLabel("Tenants in this Room")
        sub.setStyleSheet(f"color:{T.TEXT}; font-size:14px; font-weight:700;")
        lay.addWidget(sub)

        today = date.today().isoformat()

        from PySide6.QtWidgets import QHeaderView
        room_num = str(r.get("number", ""))
        all_tenants = [t for t in get_tenants() if str(t.get("room", "")) == room_num]
        active  = [t for t in all_tenants if not t.get("end_date") or t.get("end_date") > today]
        expired = [t for t in all_tenants if t.get("end_date") and t.get("end_date") <= today]

        # ── Current Residents ────────────────────────────────────────────────
        cur_lbl = QLabel("Current Residents")
        cur_lbl.setStyleSheet(f"color:{T.SUCCESS}; font-size:13px; font-weight:700;")
        lay.addWidget(cur_lbl)

        tbl1 = styled_table(["ID", "Name", "Since"])
        tbl1.setFixedHeight(160)
        tbl1.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        tbl1.setColumnWidth(0, 55)
        tbl1.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl1.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        tbl1.setContextMenuPolicy(Qt.CustomContextMenu)
        tbl1.customContextMenuRequested.connect(
            lambda pos: self._tenant_context_menu(pos, tbl1, active, r)
        )

        for t in active:
            row = tbl1.rowCount(); tbl1.insertRow(row)
            set_table_item(tbl1, row, 0, t.get("id", ""))
            set_table_item(tbl1, row, 1, t.get("name", ""))
            set_table_item(tbl1, row, 2, t.get("start_date", "—"))

        if not active:
            tbl1.insertRow(0)
            item = QTableWidgetItem("No active tenants in this room.")
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(T.TEXT_MUTED))
            tbl1.setItem(0, 0, item)
            tbl1.setSpan(0, 0, 1, 3)

        lay.addWidget(tbl1)

        # ── Past Tenants ─────────────────────────────────────────────────────
        past_lbl = QLabel("Past Tenants")
        past_lbl.setStyleSheet(f"color:{T.TEXT_MUTED}; font-size:13px; font-weight:700;")
        lay.addWidget(past_lbl)

        tbl2 = styled_table(["ID", "Name", "Start Date", "End Date"])
        tbl2.setFixedHeight(160)
        tbl2.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        tbl2.setColumnWidth(0, 55)
        tbl2.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        tbl2.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        tbl2.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        for t in expired:
            row = tbl2.rowCount(); tbl2.insertRow(row)
            set_table_item(tbl2, row, 0, t.get("id", ""))
            set_table_item(tbl2, row, 1, t.get("name", ""))
            set_table_item(tbl2, row, 2, t.get("start_date", "—"))
            set_table_item(tbl2, row, 3, t.get("end_date", "—"))

        if not expired:
            tbl2.insertRow(0)
            item = QTableWidgetItem("No past tenants for this room.")
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(T.TEXT_MUTED))
            tbl2.setItem(0, 0, item)
            tbl2.setSpan(0, 0, 1, 4)

        lay.addWidget(tbl2)

        # Close button
        close_btn = primary_button("Close")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, 0, Qt.AlignRight)

    def _tenant_context_menu(self, pos, tbl, tenants, room):
        from database.repositories import end_rental, transfer_tenant
        idx = tbl.rowAt(pos.y())
        if idx < 0 or idx >= len(tenants):
            return
        tenant = tenants[idx]
        tid = int(tenant.get("id", 0))
        name = tenant.get("name", "")

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{T.SURFACE}; border:1px solid {T.BORDER};
                     border-radius:8px; padding:4px; }}
            QMenu::item {{ padding:8px 20px; border-radius:4px; color:{T.TEXT}; font-size:13px; }}
            QMenu::item:selected {{ background:{T.BG}; color:{T.PRIMARY}; }}
        """)

        end_act      = menu.addAction("End Rent")
        transfer_act = menu.addAction("Transfer to Another Room")
        chosen = menu.exec(tbl.viewport().mapToGlobal(pos))

        if chosen == end_act:
            ans = QMessageBox.question(
                self, "End Rent",
                f"End rental for '{name}'? Today will be set as their end date.",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans == QMessageBox.Yes:
                if end_rental(tid):
                    from widgets.components import Toast
                    Toast(f"Rental ended for {name}.", "red").show_in(self.parent() or self)
                    self.done(2)

        elif chosen == transfer_act:
            dlg = TransferDialog(name, str(room.get("number", "")), parent=self)
            if dlg.exec() == QDialog.Accepted and dlg.selected_room_id:
                if transfer_tenant(tid, dlg.selected_room_id, dlg.selected_room_rent):
                    from widgets.components import Toast
                    Toast(f"{name} transferred successfully.", "blue").show_in(self.parent() or self)
                    self.done(2)


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
        self._tbl.doubleClicked.connect(self._view_room)
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
                    try: return (0, float(val))
                    except: return (1, 0.0)
                if k == "id":
                    try: return (0, int(val))
                    except: return (1, str(val).lower())
                return (1, str(val).lower())
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

    def _view_room(self, index):
        rid = self._tbl.item(index.row(), 0).text()
        while True:
            self.refresh()
            record = next((r for r in self._data if str(r.get("id")) == rid), None)
            if not record:
                break
            dlg = RoomDetailDialog(record, parent=self)
            result = dlg.exec()
            if result != 2:
                break

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
