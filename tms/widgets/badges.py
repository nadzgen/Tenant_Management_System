from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

PALETTE = {
    "Paid":              ("#dcfce7", "#16a34a"),
    "Unpaid":            ("#fef3c7", "#d97706"),
    "Overdue":           ("#fee2e2", "#dc2626"),
    "Occupied":          ("#dcfce7", "#16a34a"),
    "Vacant":            ("#fef3c7", "#d97706"),
    "Under Maintenance": ("#fee2e2", "#dc2626"),
    "Solo":              ("#dbeafe", "#2563eb"),
    "Bed Spacer":        ("#ede9fe", "#7c3aed"),
}

def make_badge(text: str) -> QLabel:
    bg, fg = PALETTE.get(text, ("#e2e8f0", "#475569"))
    dot = "●  " if text in ("Paid", "Unpaid", "Overdue", "Occupied", "Vacant", "Under Maintenance") else ""
    lbl = QLabel(f"{dot}{text}")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; padding:5px 12px; border-radius:10px;"
        f"font-size:12px; font-weight:600;"
    )
    return lbl
