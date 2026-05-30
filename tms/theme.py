"""Global QSS — white background, blue accent, light-gray secondary, rounded corners."""

PRIMARY = "#2563eb"
PRIMARY_HOVER = "#1d4ed8"
PRIMARY_SOFT = "#eff6ff"
BG = "#ffffff"
SURFACE = "#f8fafc"
BORDER = "#e2e8f0"
TEXT = "#0f172a"
MUTED = "#64748b"
SUCCESS = "#16a34a"
SUCCESS_SOFT = "#dcfce7"
WARNING = "#d97706"
WARNING_SOFT = "#fef3c7"
DANGER = "#dc2626"
DANGER_SOFT = "#fee2e2"
PURPLE_SOFT = "#ede9fe"
PURPLE = "#7c3aed"

APP_QSS = f"""
* {{ font-family: 'Segoe UI', 'Inter', sans-serif; color: {TEXT}; }}
QMainWindow, QWidget#rightArea {{ background: {SURFACE}; }}
QStackedWidget {{ background: {SURFACE}; }}

/* Sidebar */
QFrame#sidebar {{
    background: {BG};
    border-right: 1px solid {BORDER};
}}
QLabel#brandTitle {{ color: {PRIMARY}; font-size: 22px; font-weight: 800; }}
QLabel#brandSub {{ color: {MUTED}; font-size: 11px; }}
QPushButton#navBtn {{
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 10px;
    background: transparent;
    color: {TEXT};
    font-size: 14px;
}}
QPushButton#navBtn:hover {{ background: {SURFACE}; }}
QPushButton#navBtn:checked {{ background: {PRIMARY_SOFT}; color: {PRIMARY}; font-weight: 600; }}
QPushButton#logoutBtn {{
    text-align: left; padding: 12px 16px; border: none; border-radius: 10px;
    background: transparent; color: {DANGER}; font-size: 14px; font-weight: 600;
}}
QPushButton#logoutBtn:hover {{ background: {DANGER_SOFT}; }}
QFrame#sidebarTip {{
    background: {PRIMARY_SOFT}; border-radius: 12px; padding: 14px;
}}
QLabel#tipTitle {{ font-weight: 700; color: {TEXT}; }}
QLabel#tipSub {{ color: {MUTED}; font-size: 11px; }}

/* Header */
QFrame#header {{
    background: {BG};
    border-bottom: 1px solid {BORDER};
}}
QLabel#pageTitle {{ font-size: 26px; font-weight: 800; color: {TEXT}; }}
QLabel#pageCrumb {{ font-size: 12px; color: {MUTED}; }}
QLineEdit#searchTop {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 22px;
    padding: 8px 16px 8px 36px; min-width: 320px; font-size: 13px;
}}
QLineEdit#searchTop:focus {{ border-color: {PRIMARY}; background: {BG}; }}
QPushButton#bellBtn {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 18px;
    min-width: 36px; min-height: 36px;
}}
QPushButton#bellBtn:hover {{ background: {PRIMARY_SOFT}; }}
QLabel#avatar {{
    background: {PRIMARY}; color: white; border-radius: 18px;
    min-width: 36px; min-height: 36px; font-weight: 700;
    qproperty-alignment: AlignCenter;
}}

/* Page container */
QScrollArea {{ border: none; background: {SURFACE}; }}
QWidget#pageContent {{ background: {SURFACE}; }}
QLabel#sectionTitle {{ color: {PRIMARY}; font-size: 16px; font-weight: 700; }}
QLabel#sectionSub {{ color: {MUTED}; font-size: 12px; }}

/* Cards */
QFrame#card {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 14px;
}}
QFrame#statCard {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 14px;
}}
QLabel#statLabel {{ color: {MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }}
QLabel#statValue {{ color: {TEXT}; font-size: 26px; font-weight: 800; }}
QLabel#statHint  {{ color: {MUTED}; font-size: 11px; }}
QLabel#statIcon  {{ border-radius: 12px; min-width: 48px; min-height: 48px; qproperty-alignment: AlignCenter; font-size: 20px; }}

/* Buttons */
QPushButton#primaryBtn {{
    background: {PRIMARY}; color: white; border: none; border-radius: 10px;
    padding: 10px 18px; font-weight: 600; font-size: 13px;
}}
QPushButton#primaryBtn:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton#ghostBtn {{
    background: {BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 10px 18px; font-weight: 600; font-size: 13px;
}}
QPushButton#ghostBtn:hover {{ background: {SURFACE}; }}
QPushButton#dangerBtn {{
    background: {DANGER_SOFT}; color: {DANGER}; border: none; border-radius: 10px;
    padding: 10px 18px; font-weight: 600; font-size: 13px;
}}
QPushButton#dangerBtn:hover {{ background: #fecaca; }}
QPushButton#heroBtn {{
    background: {PRIMARY}; color: white; border: none; border-radius: 12px;
    padding: 14px 24px; font-weight: 700; font-size: 15px;
}}
QPushButton#heroBtn:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton#linkBtn {{ background: transparent; border: none; color: {PRIMARY}; font-weight: 600; }}
QPushButton#linkBtn:hover {{ color: {PRIMARY_HOVER}; }}

/* Inputs */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 9px 12px; font-size: 13px; min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    border-color: {PRIMARY};
}}
QLineEdit#searchBox {{
    background: {SURFACE}; padding-left: 36px;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QLabel#formLabel {{ font-size: 12px; font-weight: 700; color: {TEXT}; }}

/* Table */
QTableWidget {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 12px;
    gridline-color: transparent; font-size: 13px;
}}
QTableWidget::item {{ padding: 12px 8px; border-bottom: 1px solid {BORDER}; }}
QTableWidget::item:selected {{ background: {PRIMARY_SOFT}; color: {TEXT}; }}
QHeaderView::section {{
    background: {SURFACE}; color: {MUTED}; padding: 12px 8px;
    border: none; border-bottom: 1px solid {BORDER};
    font-weight: 700; font-size: 12px;
}}
QTableCornerButton::section {{ background: {SURFACE}; border: none; }}

/* Scrollbars */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 4px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 5px; min-width: 30px; }}

/* Checkbox */
QCheckBox {{ spacing: 8px; font-size: 13px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border: 1px solid {BORDER}; border-radius: 4px; background: {BG};
}}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border-color: {PRIMARY}; }}

/* Login */
QWidget#loginLeft {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #eff6ff, stop:1 #dbeafe); }}
QWidget#loginRight {{ background: {SURFACE}; }}
QFrame#loginCard {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 18px; }}
QLabel#loginHeroTitle {{ font-size: 38px; font-weight: 800; color: {TEXT}; }}
QLabel#loginHeroSub {{ font-size: 14px; color: {MUTED}; }}
QFrame#loginFeature {{ background: rgba(255,255,255,0.7); border: 1px solid {BORDER}; border-radius: 12px; }}
QLabel#loginTip {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px; color: {MUTED}; font-size: 11px; }}

/* Badge labels (handled inline via stylesheet on QLabel) */
"""
