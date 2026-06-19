# Tenant Management System (TMS)

A desktop rental management app for landlords to handle tenants, rooms, and payments — built with **Python + PySide6** and backed by **SQLite**.

<p align="center">
  <img src="assets/screenshots/dashboard.png" alt="TMS Dashboard" width="750"/>
</p>

---

## Quick Start

```bash
pip install pyside6
python main.py
```

**Demo login:** `admin` / `admin`

---

## Features

### Dashboard
At-a-glance summary cards for total tenants, available rooms, occupied rooms, and unpaid/overdue payments — plus a recent payment activity feed and occupancy updates.

### Tenant Management
Register tenants with name, contact number, birthdate, and sex. Assign them to available rooms during onboarding. Edit details, or remove tenants (room occupancy updates automatically). Tenant history — past assignments and payment records — is preserved for future reference.

Double-click any tenant row to open a **Tenant Detail modal** showing:
- Tenant info (id, birthday, number, gender, room, start & end date)
- **Payment History** table with tenant payments based on date

### Room Management
Create rooms with a room number, type (Solo, Bedspacer, Solo Deluxe, Bedspacer Deluxe), capacity, monthly rent, and deposit. Solo and Solo Deluxe rooms are locked to a capacity of 1. Occupancy is tracked automatically — rooms are marked **Vacant**, **Partially Occupied**, or **Full**, and new assignments are blocked once capacity is reached.

Double-click any room row to open a **Room Detail modal** showing:
- Room info (type, rent, capacity, status, occupancy)
- **Current Residents** table with tenant name and move-in date
- **Past Tenants** table with start and end dates
- Right-click any current resident to **End Rent** (sets today as end date and frees the slot) or **Transfer to Another Room** (moves the tenant to a selected available room)

### Onboarding
A step-by-step modal for adding new tenants — collects personal info, assigns a room, and records the first payment in one flow. Room selection shows room number, type, occupancy, and rent. Double-click a room in the onboarding table to preview its full detail before assigning.

### Payment Management
Record payments against a rental with a due date, payment date, amount, and type (Regular, Summer, Deposit, or Advance). Status is categorized automatically as **Paid**, **Unpaid**, or **Overdue**. Full payment history is kept per tenant, and individual records can be edited or deleted as needed.

### Search, Filter & Sort
Search across tenant names, IDs, room numbers, room types, contact numbers, payment status, and due dates. Filter by room availability, occupancy status, room type, or payment status. Sort records by move-in date, due date, monthly rent, capacity, room type, payment status, or tenant name. Tables update in real time after any add, edit, or delete action.

### Toast Notifications
All create, edit, and delete actions show a brief fade-in/fade-out toast notification anchored to the bottom-right of the app window — green for create, blue for edit, red for delete.

---

## Project Structure

```
Tenant_Management_System/
│
├── main.py                  ← Entry point; login ↔ shell switching
├── theme.py                 ← Design tokens (colours, radii, nav items)
├── icons.py                 ← SVG icon registry + make_icon() helper
│
├── data/
│   └── tms.db               ← SQLite database
│
├── database/
│   ├── db.py                ← Connection configuration
│   └── repositories.py      ← SQL queries and monthly aggregations
│
├── widgets/
│   ├── components.py        ← Cards, charts, badges, tables, buttons
│   └── navigation.py        ← Sidebar + top header
│
└── pages/
    ├── login.py
    ├── dashboard.py
    ├── tenants.py
    ├── rooms.py
    ├── payments.py
    ├── reports.py
    └── settings.py
```

---

## Design Tokens

| Token | Value | Use |
|---|---|---|
| `T.PRIMARY` | `#2C6BFF` | Buttons, active nav, links |
| `T.SUCCESS` | `#22C55E` | Paid status, positive deltas |
| `T.WARNING` | `#F5A524` | Unpaid, maintenance |
| `T.DANGER` | `#EF4444` | Overdue, delete actions |
| `T.BG` | `#F6F8FB` | Window / page background |
| `T.SURFACE` | `#FFFFFF` | Cards, panels |

All tokens live in `theme.py`.

---

## Requirements

- Python 3.10+
- PySide6 ≥ 6.6