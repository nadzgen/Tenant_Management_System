"""In-memory mock data. Replace with SQLite queries (see tms/db.py)."""

TENANTS = [
    # id, name, contact, age, sex, move_in, room
    ["T-001", "Maria Santos",  "09171234567", 28, "Female", "2024-01-15", "101"],
    ["T-002", "Juan dela Cruz", "09281234567", 35, "Male",   "2024-02-01", "102"],
    ["T-003", "Ana Reyes",     "09991234567", 22, "Female", "2024-03-10", "201"],
    ["T-004", "Pedro Bautista","09451234567", 41, "Male",   "2023-11-05", "202"],
    ["T-005", "Luisa Mendoza", "09561234567", 30, "Female", "2024-04-20", "301"],
    ["T-006", "Carlos Garcia", "09671234567", 26, "Male",   "2024-05-01", "302"],
    ["T-007", "Rosa Aquino",   "09781234567", 33, "Female", "2023-09-15", "103"],
]

ROOMS = [
    # id, number, type, capacity, rent, status
    ["R-101", "101", "Solo",       1, 4500, "Occupied"],
    ["R-102", "102", "Solo",       1, 4500, "Occupied"],
    ["R-103", "103", "Bed Spacer", 2, 6500, "Occupied"],
    ["R-104", "104", "Solo",       1, 4500, "Occupied"],
    ["R-201", "201", "Bed Spacer", 2, 6500, "Vacant"],
    ["R-202", "202", "Bed Spacer", 3, 9000, "Vacant"],
    ["R-203", "203", "Bed Spacer", 3, 9000, "Occupied"],
    ["R-301", "301", "Solo",       1, 4500, "Under Maintenance"],
    ["R-302", "302", "Solo",       1, 4500, "Occupied"],
    ["R-303", "303", "Bed Spacer", 2, 6500, "Occupied"],
]

PAYMENTS = [
    # id, tenant_id, tenant_name, amount, due, paid_on, status
    ["P-001", "T-001", "Maria Santos",   4500, "2025-06-01", "2025-05-30", "Paid"],
    ["P-002", "T-002", "Juan dela Cruz", 4500, "2025-06-01", "",           "Unpaid"],
    ["P-003", "T-003", "Ana Reyes",      6500, "2025-06-01", "2025-06-01", "Paid"],
    ["P-004", "T-004", "Pedro Bautista", 9000, "2025-05-01", "",           "Overdue"],
    ["P-005", "T-005", "Luisa Mendoza",  7500, "2025-06-01", "2025-05-28", "Paid"],
    ["P-006", "T-006", "Carlos Garcia",  7500, "2025-05-01", "",           "Unpaid"],
    ["P-007", "T-007", "Rosa Aquino",    6500, "2025-05-01", "",           "Unpaid"],
]
