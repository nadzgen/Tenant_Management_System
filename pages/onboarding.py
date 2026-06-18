"""
pages/onboarding.py — Tenant Onboarding Wizard
===============================================
A step-by-step wizard to create a tenant, select an available room, 
and process the initial payments (deposit + optional 1st month rent).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget, QHeaderView,
    QLineEdit, QComboBox, QDateEdit, QAbstractItemView, QMessageBox,
    QCheckBox, QListView, QApplication, QFrame, QPushButton, QDialog, QCalendarWidget
)
from PySide6.QtGui import QKeyEvent

from theme import T
from database.repositories import get_rooms
from widgets.components import (
    Card, section_title, primary_button, ghost_button, 
    styled_table, set_table_item, set_badge_cell, Toast
)


class CustomDateSelector(QWidget):
    def __init__(self, placeholder="14-06-2026", parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.bg_frame = QFrame()
        self.bg_frame.setStyleSheet(f"""
            QFrame {{
                background: {T.BG};
                border: 1.5px solid {T.BORDER};
                border-radius: 10px;
            }}
        """)
        self.bg_layout = QHBoxLayout(self.bg_frame)
        self.bg_layout.setContentsMargins(14, 0, 10, 0)
        self.bg_layout.setSpacing(5)
        
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setReadOnly(True)
        self.line_edit.setCursor(Qt.PointingHandCursor)
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {T.TEXT};
                font-size: 13px;
            }}
        """)
        self.line_edit.mousePressEvent = lambda e: self._show_calendar()
        
        self.btn = QPushButton("▼")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setFixedSize(24, 24)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {T.TEXT_MUTED};
                font-size: 10px;
            }}
            QPushButton:hover {{
                color: {T.TEXT};
            }}
        """)
        
        self.bg_layout.addWidget(self.line_edit)
        self.bg_layout.addWidget(self.btn)
        self.layout.addWidget(self.bg_frame)
        
        self.btn.clicked.connect(self._show_calendar)
        self.bg_frame.setCursor(Qt.PointingHandCursor)
        self.bg_frame.mousePressEvent = lambda e: self._show_calendar()
        
    def _show_calendar(self):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.Popup)
        dialog.setStyleSheet("QDialog { background: white; border: 1px solid #E2E8F0; border-radius: 8px; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        cal = QCalendarWidget()
        cal.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: none;
                color: #0F1B2D;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #F6F8FB;
                background-color: white;
                color: #0F1B2D;
            }
            QCalendarWidget QToolButton {
                color: #4A5568;
                font-size: 11px;
                font-weight: 500;
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                qproperty-icon: url(none);
                qproperty-text: "‹";
                qproperty-toolButtonStyle: 1;
                font-size: 17px;
            }
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                qproperty-icon: url(none);
                qproperty-text: "›";
                qproperty-toolButtonStyle: 1;
                font-size: 17px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #F6F8FB;
            }
            QCalendarWidget QMenu {
                background-color: white;
                color: #0F1B2D;
                border: 1px solid #E2E8F0;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                color: #0F1B2D;
                border: 1px solid #E2E8F0;
                selection-background-color: #0F1B2D;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #4A5568;
                background-color: white;
                selection-background-color: #0F1B2D;
                selection-color: white;
                border: none;
                outline: none;
            }
        """)
        layout.addWidget(cal)
        
        def on_date_selected(date: QDate):
            self.line_edit.setText(date.toString("dd-MM-yyyy"))
            self.bg_frame.setStyleSheet(f"""
                QFrame {{
                    background: {T.BG};
                    border: 1.5px solid {T.BORDER};
                    border-radius: 10px;
                }}
            """)
            dialog.accept()
            
        cal.clicked.connect(on_date_selected)
        
        pos = self.mapToGlobal(self.rect().bottomLeft())
        dialog.move(pos.x(), pos.y() + 2)
        dialog.exec()
        
    def date(self) -> QDate:
        return QDate.fromString(self.line_edit.text(), "dd-MM-yyyy")
        
    def setDate(self, date: QDate):
        self.line_edit.setText(date.toString("dd-MM-yyyy"))

class StepIndicator(QWidget):
    """A visual breadcrumb/stepper showing current progress."""
    def __init__(self, steps: list[str], parent=None):
        super().__init__(parent)
        self.labels = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        
        for i, step in enumerate(steps):
            lbl = QLabel(f"{i+1}. {step}")
            lay.addWidget(lbl)
            self.labels.append(lbl)
            if i < len(steps) - 1:
                arrow = QLabel("›")
                arrow.setStyleSheet(f"color:{T.DIVIDER}; font-size:16px; font-weight:700;")
                lay.addWidget(arrow)
        
        lay.addStretch(1)
        self.set_step(0)
        
    def set_step(self, index: int):
        for i, lbl in enumerate(self.labels):
            if i == index:
                lbl.setStyleSheet(f"color:{T.PRIMARY}; font-size:14px; font-weight:700;")
            elif i < index:
                lbl.setStyleSheet(f"color:{T.TEXT}; font-size:14px; font-weight:600;")
            else:
                lbl.setStyleSheet(f"color:{T.TEXT_SUBTLE}; font-size:14px; font-weight:500;")


class OnboardingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tenant Onboarding")
        self.setMinimumSize(620, 700)
        self.setStyleSheet(f"background:{T.SURFACE};")
        self.tenant_data = {}
        self.room_data = None
        self.payment_data = {}
        self._build()
        
    def refresh(self):
        self._load_rooms()
        self._set_step(0)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(20)
        
        self.stepper = StepIndicator(["Tenant Details", "Select Room", "Initial Payments", "Review"])
        root.addWidget(self.stepper)
        
        self.stack = QStackedWidget()
        
        # ── Step 1: Tenant ──
        self.w_tenant = Card(padding=24)
        lay_tenant = QVBoxLayout()
        lay_tenant.setSpacing(16)
        
        def field(ph):
            le = QLineEdit()
            le.setPlaceholderText(ph)
            le.setFixedHeight(42)
            le.setStyleSheet(f"background:{T.BG}; border:1.5px solid {T.BORDER}; border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px;")
            return le
            
        self.f_name = field("Full Name (e.g. Maria Santos)")
        self.btn_next1 = primary_button("Next Step")
        self.f_contact = field("Contact Number (e.g. 09171234567)")

        ok_style = (
            f"background:{T.BG}; border:1.5px solid {T.BORDER};"
            f" border-radius:10px; padding:0 14px; color:{T.TEXT}; font-size:13px;"
        )
        self.f_name.textChanged.connect(lambda t: self.f_name.setStyleSheet(ok_style) if t.strip() else None)
        self.f_contact.textChanged.connect(lambda t: self.f_contact.setStyleSheet(ok_style) if t.strip() else None)
        
        self.f_dob = CustomDateSelector("14-06-2026")
        
        self.f_sex = QComboBox()
        self.f_sex.addItems(["Female", "Male"])
        self.f_sex.setView(QListView())
        self.f_sex.setFixedHeight(42)
        self.f_sex.setFixedWidth(160)
        self.f_sex.setStyleSheet(f"""
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
        
        lbl_style = f"color:{T.TEXT}; font-size:13px; font-weight:600;"
        
        lbl1 = QLabel("Full Name"); lbl1.setStyleSheet(lbl_style); lay_tenant.addWidget(lbl1); lay_tenant.addWidget(self.f_name)
        lbl2 = QLabel("Contact Number"); lbl2.setStyleSheet(lbl_style); lay_tenant.addWidget(lbl2); lay_tenant.addWidget(self.f_contact)
        lbl3 = QLabel("Birthdate"); lbl3.setStyleSheet(lbl_style); lay_tenant.addWidget(lbl3); lay_tenant.addWidget(self.f_dob)
        lbl4 = QLabel("Sex"); lbl4.setStyleSheet(lbl_style); lay_tenant.addWidget(lbl4); lay_tenant.addWidget(self.f_sex)
        lay_tenant.addStretch(1)
        self.btn_discard = ghost_button("Discard", "trash")
        self.btn_discard.clicked.connect(self.clear_fields)
        
        self.btn_next1.clicked.connect(self._goto_step2)
        r1 = QHBoxLayout()
        r1.addWidget(self.btn_discard)
        r1.addStretch(1)
        r1.addWidget(self.btn_next1)
        lay_tenant.addLayout(r1)
        self.w_tenant.body.addLayout(lay_tenant)
        self.stack.addWidget(self.w_tenant)
        
        # ── Step 2: Room ──
        self.w_room = Card(padding=20)
        lay_room = QVBoxLayout()
        lay_room.setSpacing(12)
        
        self.tbl_rooms = styled_table(["Room ID", "Number", "Type", "Capacity", "Rent", "Status"])
        self.tbl_rooms.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_rooms.setMinimumHeight(260)

        hh = self.tbl_rooms.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Room ID
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Number
        hh.setSectionResizeMode(2, QHeaderView.Stretch)           # Type stretches
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Capacity
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Rent
        hh.setSectionResizeMode(5, QHeaderView.Fixed)             # Status
        self.tbl_rooms.setColumnWidth(5, 140)

        self.tbl_rooms.verticalHeader().setDefaultSectionSize(38)
        self._load_rooms()
        lay_room.addWidget(self.tbl_rooms)
        
        r2 = QHBoxLayout()
        btn_prev2 = ghost_button("Back")
        btn_prev2.clicked.connect(lambda: self._set_step(0))
        btn_next2 = primary_button("Next Step")
        btn_next2.clicked.connect(self._goto_step3)
        r2.addWidget(btn_prev2); r2.addStretch(1); r2.addWidget(btn_next2)
        lay_room.addLayout(r2)
        self.w_room.body.addLayout(lay_room)
        self.stack.addWidget(self.w_room)
        
        # ── Step 3: Payment ──
        self.w_pay = Card(padding=24)
        lay_pay = QVBoxLayout()
        lay_pay.setSpacing(16)
        
        self.f_deposit = field("Deposit Amount")
        self.f_deposit.setReadOnly(True)
        self.f_deposit.setStyleSheet(f"background:{T.BG}; border:1.5px solid {T.BORDER}; border-radius:10px; padding:0 14px; color:{T.TEXT_MUTED}; font-size:13px;")
        
        self.cb_first_month = QCheckBox("Pay 1st Month Rent Now")
        self.cb_first_month.setChecked(True)
        self.cb_first_month.setStyleSheet(f"color:{T.TEXT}; font-size:14px; font-weight:600;")
        self.f_rent = field("1st Month Rent Amount")
        self.f_rent.setReadOnly(True)
        self.f_rent.setStyleSheet(f"background:{T.BG}; border:1.5px solid {T.BORDER}; border-radius:10px; padding:0 14px; color:{T.TEXT_MUTED}; font-size:13px;")
        
        self.f_move_in = CustomDateSelector("14-06-2026")
        
        # self.f_dob.setDate(QDate.currentDate())
        # self.f_move_in.setDate(QDate.currentDate())
        
        lbl_dep = QLabel("Required Deposit (₱)"); lbl_dep.setStyleSheet(lbl_style); lay_pay.addWidget(lbl_dep); lay_pay.addWidget(self.f_deposit)
        lay_pay.addSpacing(10)
        lay_pay.addWidget(self.cb_first_month)
        self.lbl_rent = QLabel("1st Month Rent (₱)"); self.lbl_rent.setStyleSheet(lbl_style); lay_pay.addWidget(self.lbl_rent); lay_pay.addWidget(self.f_rent)
        lbl_mi = QLabel("Move-in Date"); lbl_mi.setStyleSheet(lbl_style); lay_pay.addWidget(lbl_mi); lay_pay.addWidget(self.f_move_in)
        lay_pay.addStretch(1)
        
        self.cb_first_month.stateChanged.connect(lambda state: self._toggle_rent(state == Qt.Checked))
        
        r3 = QHBoxLayout()
        btn_prev3 = ghost_button("Back")
        btn_prev3.clicked.connect(lambda: self._set_step(1))
        btn_next3 = primary_button("Review")
        btn_next3.clicked.connect(self._goto_step4)
        r3.addWidget(btn_prev3); r3.addStretch(1); r3.addWidget(btn_next3)
        lay_pay.addLayout(r3)
        self.w_pay.body.addLayout(lay_pay)
        self.stack.addWidget(self.w_pay)
        
        # ── Step 4: Summary ──
        self.w_sum = Card(padding=24)
        lay_sum = QVBoxLayout()
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet(f"color:{T.TEXT}; font-size:14px; line-height: 1.6;")
        self.lbl_summary.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lay_sum.addWidget(self.lbl_summary)
        
        r4 = QHBoxLayout()
        btn_prev4 = ghost_button("Back")
        btn_prev4.clicked.connect(lambda: self._set_step(2))
        btn_finish = primary_button("Complete Onboarding")
        btn_finish.clicked.connect(self._finish)
        r4.addWidget(btn_prev4); r4.addStretch(1); r4.addWidget(btn_finish)
        lay_sum.addLayout(r4)
        self.w_sum.body.addLayout(lay_sum)
        self.stack.addWidget(self.w_sum)
        
        root.addWidget(self.stack, 1)
        self._set_step(0)

    def _toggle_rent(self, enabled: bool):
        self.f_rent.setEnabled(enabled)
        color = T.TEXT if enabled else T.TEXT_SUBTLE
        self.lbl_rent.setStyleSheet(f"color:{color}; font-size:13px; font-weight:600;")

    def _load_rooms(self):
        rooms = get_rooms()
        self.avail_rooms = [r for r in rooms if r["status"] in ["Vacant", "Partially Occupied"]]
        self.tbl_rooms.setRowCount(0)
        for r_data in self.avail_rooms:
            row = self.tbl_rooms.rowCount(); self.tbl_rooms.insertRow(row)
            set_table_item(self.tbl_rooms, row, 0, str(r_data["id"]))
            set_table_item(self.tbl_rooms, row, 1, str(r_data["number"]))
            set_table_item(self.tbl_rooms, row, 2, r_data["type"])
            set_table_item(self.tbl_rooms, row, 3, str(r_data["capacity"]))
            set_table_item(self.tbl_rooms, row, 4, f"₱ {int(r_data['rent']):,}")
            set_badge_cell(self.tbl_rooms, row, 5, r_data["status"])

    def _set_step(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.stepper.set_step(idx)

    def clear_fields(self):
        self.f_name.clear()
        self.f_contact.clear()
        self.f_sex.setCurrentIndex(0)
        self.tenant_data = {}
        self.room_data = None
        self.payment_data = {}
        self.tbl_rooms.clearSelection()
        self.reject()

    def _goto_step2(self):
        ok = True
        name = self.f_name.text().strip()
        contact = self.f_contact.text().strip()

        base = (
            f"border-radius:10px; padding:0 14px; font-size:13px;"
        )
        ok_style   = f"background:{T.BG}; border:1.5px solid {T.BORDER}; color:{T.TEXT}; " + base
        err_style  = f"background:{T.BG}; border:1.5px solid {T.DANGER}; color:{T.TEXT}; " + base

        if not name:
            self.f_name.setStyleSheet(err_style)
            ok = False
        else:
            self.f_name.setStyleSheet(ok_style)

        if not contact or not contact.isdigit():
            self.f_contact.setStyleSheet(err_style)
            ok = False
        else:
            self.f_contact.setStyleSheet(ok_style)

        dob = self.f_dob.date()
        if not dob.isValid():
            self.f_dob.bg_frame.setStyleSheet(f"""
                QFrame {{
                    background: {T.BG};
                    border: 1.5px solid {T.DANGER};
                    border-radius: 10px;
                }}
            """)
            ok = False
        else:
            self.f_dob.bg_frame.setStyleSheet(f"""
                QFrame {{
                    background: {T.BG};
                    border: 1.5px solid {T.BORDER};
                    border-radius: 10px;
                }}
            """)

        if not ok:
            return

        self.tenant_data = {
            "name": name,
            "contact": contact,
            "birthdate": self.f_dob.date().toString("yyyy-MM-dd"),
            "sex": self.f_sex.currentText()
        }
        self._load_rooms()
        self._set_step(1)

    def _goto_step3(self):
        selected = self.tbl_rooms.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Required", "Please select a room.")
            return
        
        row = selected[0].row()
        self.room_data = self.avail_rooms[row]
        
        # Auto-calculate
        rent = int(self.room_data["rent"])
        self.f_deposit.setText(str(rent))
        self.f_rent.setText(str(rent))
        self._set_step(2)

    def _goto_step4(self):
        dep_str = self.f_deposit.text().strip()
        if not dep_str.isdigit():
            QMessageBox.warning(self, "Required", "Valid Deposit Amount is required.")
            return
        
        pay_rent = self.cb_first_month.isChecked()
        rent_str = self.f_rent.text().strip()
        if pay_rent and not rent_str.isdigit():
            QMessageBox.warning(self, "Required", "Valid Rent Amount is required if paying first month.")
            return

        self.payment_data = {
            "deposit": int(dep_str),
            "pay_rent": pay_rent,
            "rent": int(rent_str) if pay_rent else 0,
            "move_in": self.f_move_in.date().toString("yyyy-MM-dd")
        }
        
        sum_html = f"""
        <h3 style="color:{T.PRIMARY}; margin-bottom: 2px;">1. Tenant Information</h3>
        <b>Name:</b> {self.tenant_data['name']}<br>
        <b>Contact:</b> {self.tenant_data['contact']}<br>
        
        <br><h3 style="color:{T.PRIMARY}; margin-bottom: 2px;">2. Room Selection</h3>
        <b>Room:</b> {self.room_data['number']} ({self.room_data['type']})<br>
        <b>Rent:</b> ₱ {int(self.room_data['rent']):,}<br>
        
        <br><h3 style="color:{T.PRIMARY}; margin-bottom: 2px;">3. Initial Payments</h3>
        <b>Deposit:</b> ₱ {self.payment_data['deposit']:,}<br>
        """
        if pay_rent:
            sum_html += f"<b>1st Month Rent:</b> ₱ {self.payment_data['rent']:,} <span style='color:{T.TEXT_MUTED}'>(Move-in: {self.payment_data['move_in']})</span><br>"
        else:
            sum_html += f"<b>Move-in Date:</b> {self.payment_data['move_in']} <span style='color:{T.WARNING}'>(Rent not paid yet)</span><br>"
            
        total = self.payment_data['deposit'] + self.payment_data['rent']
        sum_html += f"<br><b style='font-size: 16px;'>Total Due Today: ₱ {total:,}</b>"
        
        self.lbl_summary.setText(sum_html)
        self._set_step(3)

    def _finish(self):
        from database.repositories import onboard_tenant
        
        room_id = int(self.room_data['id'])
        room_rent = float(self.room_data['rent'])
        
        success = onboard_tenant(self.tenant_data, room_id, room_rent, self.payment_data)
        
        if success:
            # QMessageBox.information(self, "Success", f"Tenant '{self.tenant_data['name']}' onboarded successfully!") // -> Replace with toast
            Toast("Tenant onboarded successfully.", "green").show_in(self.parent() or self)
        else:
            QMessageBox.critical(self, "Error", "Failed to onboard tenant. Please check database logs.")
            return
        
        # Reset form
        self.f_name.clear()
        self.f_contact.clear()
        self.f_deposit.clear()
        self.cb_first_month.setChecked(True)
        self.tbl_rooms.clearSelection()
        self.accept()
