from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                                QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox,
                                QGridLayout, QDialogButtonBox)
from PySide6.QtCore import Qt
from tms.pages._base import PageBase
from tms.widgets.cards import Card, StatCard
from tms.widgets.badges import make_badge
from tms import mock_data


class RoomDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Room" if data else "Add Room")
        self.setMinimumWidth(420)
        form = QFormLayout(self); form.setSpacing(10)
        self.rid = QLineEdit(); self.num = QLineEdit()
        self.type = QComboBox(); self.type.addItems(["Solo", "Bed Spacer", "Family"])
        self.cap = QSpinBox(); self.cap.setRange(1, 20)
        self.rent = QDoubleSpinBox(); self.rent.setRange(0, 1_000_000); self.rent.setPrefix("₱ "); self.rent.setDecimals(0); self.rent.setSingleStep(500)
        self.status = QComboBox(); self.status.addItems(["Vacant", "Occupied", "Under Maintenance"])
        if data:
            self.rid.setText(data[0]); self.num.setText(data[1]); self.type.setCurrentText(data[2])
            self.cap.setValue(int(data[3])); self.rent.setValue(float(data[4])); self.status.setCurrentText(data[5])
        else:
            self.rid.setText(f"R-{len(mock_data.ROOMS)+101}")
        for label, w in [("Room ID", self.rid), ("Room Number", self.num), ("Type", self.type),
                         ("Capacity", self.cap), ("Monthly Rent", self.rent), ("Status", self.status)]:
            l = QLabel(label); l.setObjectName("formLabel"); form.addRow(l, w)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def values(self):
        return [self.rid.text().strip(), self.num.text().strip(), self.type.currentText(),
                self.cap.value(), int(self.rent.value()), self.status.currentText()]


class RoomsPage(PageBase):
    def __init__(self):
        super().__init__()
        self.add_section_title("Overview", "Track and manage all your rental units")

        self.stats_grid = QGridLayout(); self.stats_grid.setSpacing(14)
        self.body.addLayout(self.stats_grid)

        card = Card()
        bar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setObjectName("searchBox")
        self.search.setPlaceholderText("🔍   Search room number, type, or status...")
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search, 1)
        add_btn = QPushButton(" +  Add Room"); add_btn.setObjectName("primaryBtn"); add_btn.setCursor(Qt.PointingHandCursor)
        edit_btn = QPushButton(" ✎  Edit");     edit_btn.setObjectName("ghostBtn"); edit_btn.setCursor(Qt.PointingHandCursor)
        del_btn  = QPushButton(" 🗑  Delete");   del_btn.setObjectName("dangerBtn"); del_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add); edit_btn.clicked.connect(self._edit); del_btn.clicked.connect(self._delete)
        for b in (add_btn, edit_btn, del_btn): bar.addWidget(b)
        card.layout().addLayout(bar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Room ID", "Room Number", "Type", "Capacity", "Monthly Rent", "Status"])
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
        # clear
        while self.stats_grid.count():
            item = self.stats_grid.takeAt(0); w = item.widget()
            if w: w.deleteLater()
        total = len(mock_data.ROOMS)
        occ = sum(1 for r in mock_data.ROOMS if r[5] == "Occupied")
        vac = sum(1 for r in mock_data.ROOMS if r[5] == "Vacant")
        maint = sum(1 for r in mock_data.ROOMS if r[5] == "Under Maintenance")
        cards = [
            StatCard("Total Rooms", str(total), "All units", "🚪", "#dbeafe", "#2563eb"),
            StatCard("Occupied",    str(occ),   "Tenants housed", "👥", "#dcfce7", "#16a34a"),
            StatCard("Vacant",      str(vac),   "Available now", "🚪", "#fef3c7", "#d97706"),
            StatCard("Under Maintenance", str(maint), "Currently offline", "🛠", "#fee2e2", "#dc2626"),
        ]
        for i, c in enumerate(cards): self.stats_grid.addWidget(c, 0, i)

    def _reload(self):
        # TODO: SELECT * FROM rooms
        self._refresh_stats()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row in mock_data.ROOMS:
            r = self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row[0]))
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            self.table.setCellWidget(r, 2, make_badge(row[2]))
            self.table.setItem(r, 3, QTableWidgetItem(f"👤  {row[3]}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"₱ {row[4]:,}"))
            self.table.setCellWidget(r, 5, make_badge(row[5]))
        self.table.setSortingEnabled(True)
        self._filter(self.search.text())

    def _filter(self, text):
        text = text.lower().strip()
        for r in range(self.table.rowCount()):
            cells = []
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c); w = self.table.cellWidget(r, c)
                if it: cells.append(it.text().lower())
                elif w and hasattr(w, "text"): cells.append(w.text().lower())
            match = not text or any(text in s for s in cells)
            self.table.setRowHidden(r, not match)

    def _sel_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return None
        return self.table.item(rows[0].row(), 0).text()

    def _add(self):
        dlg = RoomDialog(self)
        if dlg.exec() == QDialog.Accepted:
            # TODO: INSERT INTO rooms
            mock_data.ROOMS.append(dlg.values()); self._reload()

    def _edit(self):
        rid = self._sel_id()
        if not rid: QMessageBox.information(self, "Edit", "Please select a room first."); return
        idx = next((i for i, r in enumerate(mock_data.ROOMS) if r[0] == rid), -1)
        if idx < 0: return
        dlg = RoomDialog(self, mock_data.ROOMS[idx])
        if dlg.exec() == QDialog.Accepted:
            # TODO: UPDATE rooms SET ...
            mock_data.ROOMS[idx] = dlg.values(); self._reload()

    def _delete(self):
        rid = self._sel_id()
        if not rid: QMessageBox.information(self, "Delete", "Please select a room first."); return
        if QMessageBox.question(self, "Confirm Delete", f"Delete room {rid}?") == QMessageBox.Yes:
            # TODO: DELETE FROM rooms WHERE id = ?
            mock_data.ROOMS[:] = [r for r in mock_data.ROOMS if r[0] != rid]
            self._reload()
