# Tenant Management System (TMS)

A modern, clean desktop application for landlords and landladies to manage
tenants, rooms, and payments — built with **Python + PySide6**.

---

## Quick Start

```bash
# 1. Install dependency
pip install pyside6

# 2. Run the app
cd tms/
python main.py
```

**Demo login:**  `admin` / `admin`

---

## Project Structure

```
tms/
│
├── main.py                  ← Entry point. MainWindow, login↔shell switching
│
├── theme.py                 ← Design tokens (colours, radii, nav items)
├── icons.py                 ← SVG icon registry + make_icon() helper
│
├── data/
│   └── mock_data.py         ← Sample tenants, rooms, payments, chart data
│                               TODO(DB): Replace with SQLite queries here
│
├── widgets/
│   ├── components.py        ← Reusable widgets: Card, KPICard, LineChart,
│   │                           DonutChart, StatusBadge, buttons, tables …
│   └── navigation.py        ← Sidebar + TopHeader
│
└── pages/
    ├── login.py             ← Login screen (emits login_success signal)
    ├── dashboard.py         ← Overview KPIs, charts, recent payments
    ├── tenants.py           ← Tenant CRUD table + Add/Edit dialog
    ├── rooms.py             ← Room CRUD table + Add/Edit dialog
    ├── payments.py          ← Payment CRUD table, filter by status
    ├── reports.py           ← Full analytics: charts, KPIs, breakdowns
    └── settings.py          ← Profile, password, DB config, backup, prefs
```

---

## Connecting to SQLite

Every place a database call belongs is marked with a `# TODO(DB):` comment.
To add real persistence:

1. Create your database:
   ```python
   import sqlite3
   conn = sqlite3.connect("tms.db")
   conn.row_factory = sqlite3.Row
   ```

2. Search for `# TODO(DB)` across the project and replace the mock-list
   operations with the SQL queries shown in each comment.

3. Pass the `conn` object down through the page constructors (or use a
   module-level singleton in `data/db.py`).

---

## Design System

| Token | Value | Use |
|---|---|---|
| `T.PRIMARY` | `#2C6BFF` | Buttons, active nav, links |
| `T.SUCCESS` | `#22C55E` | Paid status, positive deltas |
| `T.WARNING` | `#F5A524` | Unpaid, maintenance |
| `T.DANGER`  | `#EF4444` | Overdue, delete actions |
| `T.BG`      | `#F6F8FB` | Window / page background |
| `T.SURFACE` | `#FFFFFF` | Cards, panels |

All tokens live in `theme.py`. Change once → updates everywhere.

---

## Adding a New Page

1. Create `pages/my_page.py` with a `QWidget` subclass.
2. Import and add it to the `_pages` list in `main.py → AppShell`.
3. Add an entry to `NAV_ITEMS` in `theme.py`.

---

## Requirements

- Python 3.10+
- PySide6 ≥ 6.6
