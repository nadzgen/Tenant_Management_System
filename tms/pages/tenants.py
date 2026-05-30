from PySide6.QtWidgets import (QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                                QDialog, QFormLayout, QComboBox, QSpinBox, QDateEdit, QDialogButtonBox)
from PySide6.QtCore import Qt, QDate
from tms.pages._base import PageBase
from tms.widgets.cards import Card
from tms import mock_data


class TenantDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Tenant" if data else "Add Tenant")
        self.setMinimumWidth(420)
        form = QFormLayout(self); form.setSpacing(10)
        self.tid = QLineEdit(); self.name = QLineEdit(); self.contact = QLineEdit()
        self.age = QSpinBox(); self.age.setRange(18, 120)
        self.sex = QComboBox(); self.sex.addItems(["Female", "Male", "Other"])
        self.move_in = QDateEdit(); self.move_in.setCalendarPopup(True); self.move_in.setDate(QDate.currentDate())
        self.move_in.setDisplayFormat("yyyy-MM-dd")
        self.room = QLineEdit()
        if data:
            self.tid.setText(data[0]); self.name.setText(data[1]); self.contact.setText(data[2])
            self.age.setValue(int(data[3])); self.sex.setCurrentText(data[4])
            self.move_in.setDate(QDate.fromString(data[5], "yyyy-MM-dd"))
            self.room.setText(data[6])
        else:
            self.tid.setText(f"T-{len(mock_data.TENANTS)+1:03d}")
        for label, w in [("Tenant ID", self.tid), ("Full Name", self.name), ("Contact Number", self.contact),
                         ("Age", self.age), ("Sex", self.sex), ("Move-in Date", self.move_in), ("Assigned Room", self.room)]:
            l = QLabel(label); l.setObjectName("formLabel"); form.addRow(l, w)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def values(self):
        return [self.tid.text().strip(), self.name.text().strip(), self.contact.text().strip(),
                self.age.value(), self.sex.currentText(), self.move_in.date().toString("yyyy-MM-dd"),
                self.room.text().strip()]


class TenantsPage(PageBase):
    def __init__(self):
        super().__init__()
        self.add_section_title("Tenant Management", "Add, view, and manage your tenants")

        card = Card()
        # Toolbar
        bar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setObjectName("searchBox")
        self.search.setPlaceholderText("🔍   Search by name, contact, or room...")
        self.search.textChanged.connect(self._filter)
        bar.addWidget(self.search, 1)
        add_btn = QPushButton(" +  Add Tenant"); add_btn.setObjectName("primaryBtn"); add_btn.setCursor(Qt.PointingHandCursor)
        edit_btn = QPushButton(" ✎  Edit");      edit_btn.setObjectName("ghostBtn"); edit_btn.setCursor(Qt.PointingHandCursor)
        del_btn  = QPushButton(" 🗑  Delete");    del_btn.setObjectName("dangerBtn"); del_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add); edit_btn.clicked.connect(self._edit); del_btn.clicked.connect(self._delete)
        for b in (add_btn, edit_btn, del_btn): bar.addWidget(b)
        card.layout().addLayout(bar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Tenant ID", "Full Name", "Contact", "Age", "Sex", "Move-in Date", "Room"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(420)
        card.layout().addWidget(self.table)

        self.count_lbl = QLabel(); self.count_lbl.setStyleSheet("color:#64748b; font-size:12px;")
        card.layout().addWidget(self.count_lbl)
        self.body.addWidget(card)
        self._reload()

    def _reload(self):
        # TODO: replace with SELECT * FROM tenants
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row in mock_data.TENANTS:
            r = self.table.rowCount(); self.table.insertRow(r)
            for c, v in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.table.setSortingEnabled(True)
        self.count_lbl.setText(f"Showing 1 to {len(mock_data.TENANTS)} of {len(mock_data.TENANTS)} tenants")
        self._filter(self.search.text())

    def _filter(self, text):
        text = text.lower().strip()
        for r in range(self.table.rowCount()):
            match = not text or any(text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                                    for c in range(self.table.columnCount()))
            self.table.setRowHidden(r, not match)

    def _selected_row(self):
        rows = self.table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def _add(self):
        dlg = TenantDialog(self)
        if dlg.exec() == QDialog.Accepted:
            vals = dlg.values()
            if not vals[1]:
                QMessageBox.warning(self, "Add Tenant", "Full name is required."); return
            # TODO: INSERT INTO tenants ...
            mock_data.TENANTS.append(vals); self._reload()

    def _edit(self):
        r = self._selected_row()
        if r < 0: QMessageBox.information(self, "Edit", "Please select a tenant first."); return
        # Map visible row back to data via Tenant ID
        tid = self.table.item(r, 0).text()
        idx = next((i for i, t in enumerate(mock_data.TENANTS) if t[0] == tid), -1)
        if idx < 0: return
        dlg = TenantDialog(self, mock_data.TENANTS[idx])
        if dlg.exec() == QDialog.Accepted:
            # TODO: UPDATE tenants SET ... WHERE id = ?
            mock_data.TENANTS[idx] = dlg.values(); self._reload()

    def _delete(self):
        r = self._selected_row()
        if r < 0: QMessageBox.information(self, "Delete", "Please select a tenant first."); return
        tid = self.table.item(r, 0).text()
        if QMessageBox.question(self, "Confirm Delete", f"Delete tenant {tid}?") == QMessageBox.Yes:
            # TODO: DELETE FROM tenants WHERE id = ?
            mock_data.TENANTS[:] = [t for t in mock_data.TENANTS if t[0] != tid]
            self._reload()
