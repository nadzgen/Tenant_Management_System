"""
main.py — Main Window & Application Entry Point
================================================
Wires together the login screen, sidebar, header, and all page modules
inside a single QMainWindow with a QStackedWidget.

Demo credentials:  username: admin  /  password: admin
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
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
from pages.onboarding import OnboardingPage
from pages.tenants import TenantsPage
from pages.rooms import RoomsPage
from pages.payments import PaymentsPage
from pages.reports import ReportsPage
from pages.settings import SettingsPage

# Navigation widgets
from widgets.navigation import Sidebar, TopHeader


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
        h.setSpacing(0)

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
        self._pages = [
            DashboardPage(),
            OnboardingPage(),
            TenantsPage(),
            RoomsPage(),
            PaymentsPage(),
            ReportsPage(),
            SettingsPage(),
        ]
        for page in self._pages:
            self.stack.addWidget(page)

        v.addWidget(self.stack, 1)
        h.addWidget(right, 1)

        # Wire navigation
        self.sidebar.navigate.connect(self._navigate)
        self._navigate(0)  # start on Dashboard

    def _navigate(self, index: int):
        self.stack.setCurrentIndex(index)
        page = self._pages[index]
        if hasattr(page, "refresh"):
            page.refresh()
            
        if 0 <= index < len(NAV_ITEMS):
            _, label, _ = NAV_ITEMS[index]
            self.header.set_context(label)
            self.sidebar.set_active(index)

    def set_user(self, username: str):
        self.header.set_user(username[0] if username else "A")


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

        # Root stacked widget: login ↔ app shell
        self._root = QStackedWidget()
        self.setCentralWidget(self._root)

        self._login_page = LoginPage()
        self._app_shell  = AppShell()

        self._root.addWidget(self._login_page)   # index 0
        self._root.addWidget(self._app_shell)    # index 1
        self._root.setCurrentIndex(0)            # start on login

        # Connections
        self._login_page.login_success.connect(self._on_login)
        self._app_shell.sidebar.do_logout.connect(self._on_logout)

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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))           
    app.setStyle("Fusion")                        # cross-platform consistency
    
    # Force a global light palette so native containers (like QComboBox popups) don't bleed Windows dark mode
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
    
    # Global stylesheet for Date Picker Calendars
    app.setStyleSheet(f"""
        QCalendarWidget {{
            background-color: {T.SURFACE};
            border: 5px solid {T.BORDER};
            border-radius: {T.RADIUS_SM}px;
            /* Padding ensures the sharp corners of the inner grid do not clip the rounded border */
            padding: 6px; 
            font-size: 11px;
        }}
        QCalendarWidget QWidget {{
            alternate-background-color: {T.BG};
            background-color: transparent;
            font-size: 11px;
        }}
        QCalendarWidget QToolButton {{
            color: {T.TEXT_MUTED};
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
            color: {T.TEXT_MUTED};
            padding: 0px 2px;
        }}
        QCalendarWidget QToolButton#qt_calendar_nextmonth {{
            qproperty-icon: url(none);
            qproperty-text: "›";
            qproperty-toolButtonStyle: 1;
            font-size: 17px;
            font-weight: 500;
            color: {T.TEXT_MUTED};
            padding: 0px 2px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: {T.BG};
            color: {T.TEXT};
        }}
        QCalendarWidget QMenu {{
            background-color: {T.SURFACE};
            color: {T.TEXT};
            border: 1px solid {T.BORDER};
            border-radius: 6px;
        }}
        QCalendarWidget QSpinBox {{
            background-color: {T.BG};
            color: {T.TEXT};
            border: 1px solid {T.BORDER};
            border-radius: 4px;
            selection-background-color: {T.PRIMARY};
        }}
        QCalendarWidget QAbstractItemView:enabled {{
            color: {T.TEXT_MUTED};
            background-color: transparent;
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
            color: {T.TEXT_SUBTLE};
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
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
