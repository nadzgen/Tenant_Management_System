"""
theme.py — Design tokens & app-wide constants
==============================================
All colours, radii, and fonts live here.  Change a value once; every widget
inherits it automatically.
"""


class T:
    # ── Surfaces ────────────────────────────────────────────────────────────
    BG           = "#F6F8FB"   # app / window background
    SURFACE      = "#FFFFFF"   # cards, panels
    SIDEBAR      = "#FFFFFF"
    BORDER       = "#E6EAF0"
    DIVIDER      = "#EEF1F6"

    # ── Text ────────────────────────────────────────────────────────────────
    TEXT         = "#0F1B2D"
    TEXT_MUTED   = "#6B7A90"
    TEXT_SUBTLE  = "#94A3B8"

    # ── Brand ───────────────────────────────────────────────────────────────
    PRIMARY      = "#2C6BFF"
    PRIMARY_SOFT = "#EAF1FF"
    PRIMARY_DK   = "#1E55D6"

    # ── Semantic ────────────────────────────────────────────────────────────
    SUCCESS      = "#22C55E"
    SUCCESS_SOFT = "#E8F8EE"
    WARNING      = "#F5A524"
    WARNING_SOFT = "#FDF1DE"
    DANGER       = "#EF4444"
    DANGER_SOFT  = "#FDECEC"
    PURPLE       = "#8B5CF6"
    PURPLE_SOFT  = "#F1ECFE"

    # ── Shape ───────────────────────────────────────────────────────────────
    RADIUS       = 14
    RADIUS_SM    = 10


# Navigation items: (icon_key, display_label, page_index)
NAV_ITEMS = [
    ("home",      "Dashboard",           0),
    ("user-plus", "Onboarding",          1),
    ("users",     "Tenant Management",   2),
    ("door",      "Room Management",     3),
    ("wallet",    "Payment Tracking",    4),
    ("chart",     "Reports & Analytics", 5),
    ("gear",      "Settings",            6),
]
