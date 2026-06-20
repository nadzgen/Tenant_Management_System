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


class CustomDateSelector(QDateEdit):
    def __init__(self, placeholder="DD/MM/YYYY", parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setFixedHeight(42)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setDate(QDate.currentDate())
        self.setStyleSheet(f"""
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

    def _view_room_detail(self, index):
        row = index.row()
        if row < len(self.avail_rooms):
            from pages.rooms import RoomDetailDialog
            RoomDetailDialog(self.avail_rooms[row], parent=self).exec()
        
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
        
        self.f_dob = CustomDateSelector("DD/MM/YYYY")
        
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
        
        filter_lay = QHBoxLayout()
        filter_lay.setContentsMargins(0, 0, 0, 0)
        self.lbl_room_filter = QLabel()
        self.lbl_room_filter.setFixedHeight(24)
        self.lbl_room_filter.setStyleSheet(f"""
            QLabel {{
                background: {T.BG};
                border: 1px solid {T.BORDER};
                border-radius: 12px;
                color: {T.PRIMARY};
                font-size: 11px;
                font-weight: 600;
                padding: 0 10px;
            }}
        """)
        filter_lay.addWidget(self.lbl_room_filter)
        filter_lay.addStretch(1)
        lay_room.addLayout(filter_lay)
        
        self.tbl_rooms = styled_table(["Room No.", "Type", "Occupancy", "Monthly Rent"])
        self.tbl_rooms.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_rooms.setMinimumHeight(260)
        self.tbl_rooms.doubleClicked.connect(self._view_room_detail)

        hh = self.tbl_rooms.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Room No.
        hh.setSectionResizeMode(1, QHeaderView.Stretch)           # Type
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Occupancy
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Rent

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
        
        self.f_move_in = CustomDateSelector("DD/MM/YYYY")
        
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
        self.summary_content = QVBoxLayout()
        self.summary_content.setSpacing(12)
        lay_sum.addLayout(self.summary_content)
        lay_sum.addStretch(1)
        
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
        tenant_sex = self.tenant_data.get("sex")
        
        if hasattr(self, "lbl_room_filter"):
            if tenant_sex:
                self.lbl_room_filter.setText(f"✦ Filter: Vacant & {tenant_sex}-Only")
                self.lbl_room_filter.show()
            else:
                self.lbl_room_filter.hide()
                
        self.avail_rooms = []
        for r in rooms:
            if r["status"] == "Vacant":
                self.avail_rooms.append(r)
            elif r["status"] == "Partially Occupied":
                if tenant_sex and r.get("occupant_sex") == tenant_sex:
                    self.avail_rooms.append(r)
                elif not tenant_sex:
                    self.avail_rooms.append(r)
                    
        self.tbl_rooms.setRowCount(0)
        for r_data in self.avail_rooms:
            row = self.tbl_rooms.rowCount(); self.tbl_rooms.insertRow(row)
            set_table_item(self.tbl_rooms, row, 0, str(r_data["number"]))
            set_table_item(self.tbl_rooms, row, 1, r_data["type"])
            set_table_item(self.tbl_rooms, row, 2, f"{r_data.get('occupied_slots', 0)}/{r_data['capacity']}")
            set_table_item(self.tbl_rooms, row, 3, f"₱ {int(r_data['rent']):,}")

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
        base_date_style = f"""
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
        """
        if not dob.isValid():
            self.f_dob.setStyleSheet(f"""
                QDateEdit {{
                    background: {T.BG};
                    border: 1.5px solid {T.DANGER};
                    border-radius: 10px;
                    padding: 0 14px;
                    color: {T.TEXT};
                    font-size: 13px;
                }}
                {base_date_style}
            """)
            ok = False
        else:
            self.f_dob.setStyleSheet(f"""
                QDateEdit {{
                    background: {T.BG};
                    border: 1.5px solid {T.BORDER};
                    border-radius: 10px;
                    padding: 0 14px;
                    color: {T.TEXT};
                    font-size: 13px;
                }}
                {base_date_style}
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

        if not self.f_move_in.date().isValid():
            QMessageBox.warning(self, "Required", "Valid Move-in Date is required (dd/MM/yyyy).")
            return

        self.payment_data = {
            "deposit": int(dep_str),
            "pay_rent": pay_rent,
            "rent": int(rent_str) if pay_rent else 0,
            "move_in": self.f_move_in.date().toString("yyyy-MM-dd")
        }
        
        # Clear existing summary layout
        while self.summary_content.count():
            item = self.summary_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        def make_card(title, data_pairs):
            f = QFrame()
            f.setStyleSheet(f"QFrame {{ background:{T.BG}; border:1px solid {T.BORDER}; border-radius:10px; }} QLabel {{ border:none; background:transparent; }}")
            l = QVBoxLayout(f)
            l.setContentsMargins(16, 14, 16, 14)
            l.setSpacing(8)
            t = QLabel(title)
            t.setStyleSheet(f"color:{T.PRIMARY}; font-size:12px; font-weight:700; text-transform:uppercase;")
            l.addWidget(t)
            for k, v in data_pairs:
                r = QHBoxLayout()
                lk = QLabel(k)
                lk.setStyleSheet(f"color:{T.TEXT_SUBTLE}; font-size:13px;")
                lv = QLabel(str(v))
                lv.setStyleSheet(f"color:{T.TEXT}; font-size:13px; font-weight:600;")
                lv.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                r.addWidget(lk); r.addWidget(lv)
                l.addLayout(r)
            return f

        self.summary_content.addWidget(make_card("1. Tenant Information", [
            ("Name", self.tenant_data['name']),
            ("Contact", self.tenant_data['contact'])
        ]))
        
        self.summary_content.addWidget(make_card("2. Room Selection", [
            ("Room", f"{self.room_data['number']} ({self.room_data['type']})"),
            ("Rent", f"₱ {int(self.room_data['rent']):,}")
        ]))
        
        pay_info = [("Deposit", f"₱ {self.payment_data['deposit']:,}")]
        if pay_rent:
            pay_info.append(("1st Month Rent", f"₱ {self.payment_data['rent']:,}"))
            pay_info.append(("Move-in Date", self.payment_data['move_in']))
        else:
            pay_info.append(("Move-in Date", f"{self.payment_data['move_in']} (Rent pending)"))
            
        self.summary_content.addWidget(make_card("3. Initial Payments", pay_info))
        
        total = self.payment_data['deposit'] + self.payment_data['rent']
        
        tot_frame = QFrame()
        tot_frame.setStyleSheet(f"QFrame {{ background:{T.SURFACE}; border:2px solid {T.PRIMARY}; border-radius:10px; }} QLabel {{ border:none; background:transparent; }}")
        tot_lay = QHBoxLayout(tot_frame)
        tot_lay.setContentsMargins(16, 16, 16, 16)
        lbl_tot_text = QLabel("Total Due Today")
        lbl_tot_text.setStyleSheet(f"color:{T.PRIMARY}; font-size:15px; font-weight:700;")
        lbl_tot_val = QLabel(f"₱ {total:,}")
        lbl_tot_val.setStyleSheet(f"color:{T.PRIMARY}; font-size:18px; font-weight:800;")
        lbl_tot_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        tot_lay.addWidget(lbl_tot_text); tot_lay.addWidget(lbl_tot_val)
        
        self.summary_content.addWidget(tot_frame)
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
