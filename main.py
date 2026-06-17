"""
main.py — Main Window & Application Entry Point
================================================
Wires together the login screen, sidebar, header, and all page modules
inside a single QMainWindow with a QStackedWidget.

Demo credentials:  username: admin  /  password: admin
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, Signal, QEvent, QObject
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox,
)

from theme import T, NAV_ITEMS
from icons import make_icon

# Pages
from pages.login import LoginPage
from pages.dashboard import DashboardPage
from pages.onboarding import OnboardingDialog
from pages.tenants import TenantsPage
from pages.rooms import RoomsPage
from pages.payments import PaymentsPage
from pages.reports import ReportsPage
from pages.settings import SettingsPage

# Navigation widgets
from widgets.navigation import Sidebar, TopHeader

class MessageBoxFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show and isinstance(obj, QMessageBox):
            pal = obj.palette()
            pal.setColor(QPalette.ColorRole.Window, QColor("white"))
            pal.setColor(QPalette.ColorRole.WindowText, QColor("black"))
            pal.setColor(QPalette.ColorRole.Text, QColor("black"))
            obj.setPalette(pal)
            obj.setStyleSheet("""
                QWidget { background-color: #FFFFFF; color: #000000; }
                QLabel { color: #000000; font-size: 13.5px; font-weight: 500; background-color: transparent; }
                QPushButton { background-color: #2C6BFF; color: white; border: none; border-radius: 6px; padding: 6px 18px; min-width: 65px; font-weight: 600; font-size: 13px; }
                QPushButton:hover { background-color: #1a56db; }
            """)
        return super().eventFilter(obj, event)

# ---------------------------------------------------------------------------
# Shell: sidebar + header + stacked pages (shown after login)
# ---------------------------------------------------------------------------

class AppShell(QWidget):
    """The main authenticated shell — sidebar, header, and page stack."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{T.BG};")

        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(15)

        # Sidebar
        self.sidebar = Sidebar()
        h.addWidget(self.sidebar)

        # Right column: header + pages
        right = QWidget()
        right.setStyleSheet("background:transparent;")
        v = QVBoxLayout(right)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.header = TopHeader()
        v.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:transparent;")
        self._pages_cache = {}
        for i in range(6):
            self.stack.addWidget(QWidget())

        v.addWidget(self.stack, 1)
        h.addWidget(right, 1)

        # Wire navigation
        self.sidebar.navigate.connect(self._navigate)
        self.header.onboard_requested.connect(self._open_onboarding)
        self._navigate(0)  # start on Dashboard

    def _navigate(self, index: int):
        if index not in self._pages_cache:
            if index == 0: self._pages_cache[0] = DashboardPage()
            elif index == 1: pass 
            elif index == 2: self._pages_cache[2] = TenantsPage()
            elif index == 3: self._pages_cache[3] = RoomsPage()
            elif index == 4: self._pages_cache[4] = PaymentsPage()
            elif index == 5: self._pages_cache[5] = ReportsPage()
            elif index == 6:
                p = SettingsPage()
                p.profile_updated.connect(self.set_user)
                if getattr(self, "_current_user", None):
                    p.set_user(self._current_user)
                self._pages_cache[6] = p
                
            old = self.stack.widget(index)
            self.stack.removeWidget(old)
            self.stack.insertWidget(index, self._pages_cache[index])
            old.deleteLater()

        if index != 1:
            self.stack.setCurrentIndex(index)
        page = self._pages_cache[index]
        if hasattr(page, "refresh"):
            page.refresh()
            
        found_nav = False
        for icon, label, idx in NAV_ITEMS:
            if idx == index:
                self.header.set_context(label)
                self.sidebar.set_active(index)
                found_nav = True
                break
                
        if not found_nav:
            if index == 1:
                self.header.set_context("Onboarding")
                self.sidebar.set_active(-1)  # Clear selection in sidebar

    def _open_onboarding(self):
        from pages.onboarding import OnboardingDialog
        dlg = OnboardingDialog(self)
        dlg.exec()
        # Refresh dashboard/tenants/rooms/payments if open
        for idx in [0, 2, 3, 4]:
            if idx in self._pages_cache and hasattr(self._pages_cache[idx], "refresh"):
                self._pages_cache[idx].refresh()

    def set_user(self, username: str):
        self._current_user = username
        self.header.set_user(username[0] if username else "A")
        if 6 in self._pages_cache:
            self._pages_cache[6].set_user(username)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """
    Top-level window.  Contains a QStackedWidget with two layers:
        Index 0 → LoginPage
        Index 1 → AppShell (sidebar + all pages)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tenant Management System")
        self.setWindowIcon(make_icon("building", T.PRIMARY, 32))
        self.resize(1380, 880)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(f"QMainWindow {{ background:{T.BG}; }}")

        # Match native Windows 11 titlebar color to the app background
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes.wintypes import DWORD, HWND
                DWMWA_CAPTION_COLOR = 35
                bg_hex = T.BG.lstrip("#")
                r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
                colorref = r | (g << 8) | (b << 16)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    HWND(int(self.winId())),
                    DWORD(DWMWA_CAPTION_COLOR),
                    ctypes.byref(DWORD(colorref)),
                    ctypes.sizeof(DWORD)
                )
            except Exception as e:
                pass

        # Root stacked widget: # Navigation root
        self._root = QStackedWidget(self)
        self.setCentralWidget(self._root)

        # Login page
        self._login_page = LoginPage()
        self._login_page.login_success.connect(self._on_login)
        self._root.addWidget(self._login_page)

        # Main authenticated shell
        self._app_shell = AppShell()
        self._app_shell.sidebar.do_logout.connect(self._on_logout)
        self._root.addWidget(self._app_shell)

        self._root.setCurrentIndex(0)

    # ── Auth transitions ─────────────────────────────────────────────────────

    def _on_login(self, username: str):
        # TODO(DB): Store session / user ID here
        self._app_shell.set_user(username)
        self._root.setCurrentIndex(1)

    def _on_logout(self):
        ans = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            # TODO(DB): Clear session / revoke token here
            self._login_page.clear_fields()
            self._root.setCurrentIndex(0)

    def _apply_global_theme(self):
        app = QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(T.BG))
        palette.setColor(QPalette.WindowText, QColor(T.TEXT))
        palette.setColor(QPalette.Base, QColor(T.SURFACE))
        palette.setColor(QPalette.AlternateBase, QColor(T.BG))
        palette.setColor(QPalette.ToolTipBase, QColor(T.SURFACE))
        palette.setColor(QPalette.ToolTipText, QColor(T.TEXT))
        palette.setColor(QPalette.Text, QColor(T.TEXT))
        palette.setColor(QPalette.Button, QColor(T.BG))
        palette.setColor(QPalette.ButtonText, QColor(T.TEXT))
        palette.setColor(QPalette.BrightText, QColor(T.WARNING))
        palette.setColor(QPalette.Highlight, QColor(T.PRIMARY))
        palette.setColor(QPalette.HighlightedText, QColor(Qt.white))
        app.setPalette(palette)
        
        app.setStyleSheet(f"""
            QCalendarWidget {{
                background-color: white;
                border: 5px solid {T.PRIMARY};
                border-radius: {T.RADIUS_SM}px;
                padding: 6px; 
                font-size: 11px;
                color: #0F1B2D;
            }}
            QCalendarWidget QWidget {{
                alternate-background-color: #F6F8FB;
                background-color: white;
                font-size: 11px;
                color: #0F1B2D;
            }}
            QCalendarWidget QToolButton {{
                color: #4A5568;
                font-size: 11px;
                font-weight: 500;
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding:  0px 4px;
            }}
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {{
                margin: 0px;
                padding: 0px;
            }}
            QCalendarWidget QToolButton::menu-indicator {{
                subcontrol-position: right center;
                subcontrol-origin: padding;
                width: 10px;
                image: none;
            }}
            QCalendarWidget QToolButton#qt_calendar_prevmonth {{
                qproperty-icon: url(none);
                qproperty-text: "‹";
                qproperty-toolButtonStyle: 1;
                font-size: 17px;
                font-weight: 500;
                color: #4A5568;
                padding: 0px 2px;
            }}
            QCalendarWidget QToolButton#qt_calendar_nextmonth {{
                qproperty-icon: url(none);
                qproperty-text: "›";
                qproperty-toolButtonStyle: 1;
                font-size: 17px;
                font-weight: 500;
                color: #4A5568;
                padding: 0px 2px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: #F6F8FB;
                color: #0F1B2D;
            }}
            QCalendarWidget QMenu {{
                background-color: white;
                color: #0F1B2D;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
            }}
            QCalendarWidget QSpinBox {{
                background-color: white;
                color: #0F1B2D;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                selection-background-color: {T.PRIMARY};
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: #4A5568;
                background-color: white;
                selection-background-color: {T.PRIMARY};
                selection-color: white;
                border: none;
                outline: none;
                border-radius: {T.RADIUS_SM}px;
                padding: 8px;
            }}
            QCalendarWidget QTableView {{
                margin-left: 4px;
                margin-right: 4px;
                margin-bottom: 4px;
                margin-top: 0px;
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: #A0AEC0;
            }}
            #qt_calendar_navigationbar {{
                background-color: transparent;
                border-bottom: none;
                padding: 4px 4px 0px 4px;
                min-height: 28px;
            }}
            
            /* Global QComboBox Dropdown Styles */
            QComboBox QAbstractItemView {{
                background: {T.SURFACE};
                border: none;
                padding: 0px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                height: 32px;
                padding-left: 8px;
                padding-right: 8px;
                border-radius: 4px;
                color: {T.TEXT};
                margin: 2px 4px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {T.BG};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {T.PRIMARY_SOFT};
                color: {T.PRIMARY};
                font-weight: 600;
            }}
        """)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    
    # Force QMessageBox to always use light mode
    msg_filter = MessageBoxFilter()
    app.installEventFilter(msg_filter)
    
    app.setFont(QFont("Segoe UI", 10))           
    app.setStyle("Fusion")                        # cross-platform consistency
    win = MainWindow()
    win._apply_global_theme()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
