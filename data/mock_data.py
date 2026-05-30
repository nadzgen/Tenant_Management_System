"""
data/mock_data.py — Sample data for every page
================================================
All lists here are placeholders.  When you connect to SQLite, replace each
list with a query that returns the same shape of dict.

TODO(DB): Replace TENANTS / ROOMS / PAYMENTS with SQLite SELECT queries.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------
# TODO(DB): SELECT id, full_name, contact, age, sex, move_in, room FROM tenants
TENANTS: list[dict] = [
    {"id": "T-001", "name": "Maria Santos",    "contact": "09171234567", "age": 28, "sex": "Female", "move_in": "2024-01-15", "room": "101"},
    {"id": "T-002", "name": "Juan dela Cruz",  "contact": "09281234567", "age": 35, "sex": "Male",   "move_in": "2024-02-01", "room": "102"},
    {"id": "T-003", "name": "Ana Reyes",       "contact": "09991234567", "age": 22, "sex": "Female", "move_in": "2024-03-10", "room": "201"},
    {"id": "T-004", "name": "Pedro Bautista",  "contact": "09451234567", "age": 41, "sex": "Male",   "move_in": "2023-11-05", "room": "202"},
    {"id": "T-005", "name": "Luisa Mendoza",   "contact": "09561234567", "age": 30, "sex": "Female", "move_in": "2024-04-20", "room": "301"},
    {"id": "T-006", "name": "Carlos Garcia",   "contact": "09671234567", "age": 26, "sex": "Male",   "move_in": "2024-05-01", "room": "302"},
    {"id": "T-007", "name": "Rosa Aquino",     "contact": "09781234567", "age": 33, "sex": "Female", "move_in": "2023-09-15", "room": "103"},
]

# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
# TODO(DB): SELECT id, number, type, capacity, rent, status FROM rooms
ROOMS: list[dict] = [
    {"id": "R-101", "number": "101", "type": "Single",  "capacity": 1, "rent": 4500,  "status": "Occupied"},
    {"id": "R-102", "number": "102", "type": "Single",  "capacity": 1, "rent": 4500,  "status": "Occupied"},
    {"id": "R-103", "number": "103", "type": "Double",  "capacity": 2, "rent": 6500,  "status": "Occupied"},
    {"id": "R-104", "number": "104", "type": "Single",  "capacity": 1, "rent": 4500,  "status": "Vacant"},
    {"id": "R-201", "number": "201", "type": "Double",  "capacity": 2, "rent": 6500,  "status": "Occupied"},
    {"id": "R-202", "number": "202", "type": "Suite",   "capacity": 3, "rent": 9000,  "status": "Occupied"},
    {"id": "R-203", "number": "203", "type": "Suite",   "capacity": 3, "rent": 9000,  "status": "Vacant"},
    {"id": "R-301", "number": "301", "type": "Studio",  "capacity": 2, "rent": 7500,  "status": "Occupied"},
    {"id": "R-302", "number": "302", "type": "Studio",  "capacity": 2, "rent": 7500,  "status": "Occupied"},
    {"id": "R-303", "number": "303", "type": "Double",  "capacity": 2, "rent": 6500,  "status": "Maintenance"},
]

# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------
# TODO(DB): SELECT id, tenant_id, tenant_name, amount, due_date, pay_date, status FROM payments
PAYMENTS: list[dict] = [
    {"id": "P-001", "tenant_id": "T-001", "tenant": "Maria Santos",   "amount": 4500,  "due": "2025-06-01", "paid_on": "2025-05-30", "status": "Paid"},
    {"id": "P-002", "tenant_id": "T-002", "tenant": "Juan dela Cruz",  "amount": 4500,  "due": "2025-06-01", "paid_on": "",           "status": "Unpaid"},
    {"id": "P-003", "tenant_id": "T-003", "tenant": "Ana Reyes",       "amount": 6500,  "due": "2025-06-01", "paid_on": "2025-06-01", "status": "Paid"},
    {"id": "P-004", "tenant_id": "T-004", "tenant": "Pedro Bautista",  "amount": 9000,  "due": "2025-05-01", "paid_on": "",           "status": "Overdue"},
    {"id": "P-005", "tenant_id": "T-005", "tenant": "Luisa Mendoza",   "amount": 7500,  "due": "2025-06-01", "paid_on": "2025-05-28", "status": "Paid"},
    {"id": "P-006", "tenant_id": "T-006", "tenant": "Carlos Garcia",   "amount": 7500,  "due": "2025-06-01", "paid_on": "",           "status": "Unpaid"},
    {"id": "P-007", "tenant_id": "T-007", "tenant": "Rosa Aquino",     "amount": 6500,  "due": "2025-05-01", "paid_on": "",           "status": "Overdue"},
]

# ---------------------------------------------------------------------------
# Revenue chart data
# ---------------------------------------------------------------------------
REVENUE_MONTHLY = [12000, 15500, 17000, 21000, 19500, 23000, 24500, 26000, 28500, 27000, 31000, 28000]
REVENUE_LABELS  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
