import sqlite3
from typing import List, Dict, Any, Tuple
from .db import get_connection

def init_admin_table():
    query = """
        CREATE TABLE IF NOT EXISTS Admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            contact TEXT
        )
    """
    try:
        with get_connection() as conn:
            conn.execute(query)
            # Check if admin exists, if not create default
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Admin")
            if cursor.fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO Admin (username, password, email, contact) VALUES (?, ?, ?, ?)",
                    ("admin", "admin", "admin@example.com", "09171234567")
                )
    except sqlite3.OperationalError as e:
        print(f"Warning (init_admin_table): {e}")

# Call init_admin_table when module is loaded
init_admin_table()

def validate_login(username, password) -> bool:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Admin WHERE username=? AND password=?", (username, password))
            return cursor.fetchone() is not None
    except sqlite3.OperationalError:
        return False

def get_admin_profile() -> Dict[str, Any]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Admin LIMIT 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
    except sqlite3.OperationalError:
        pass
    return {"username": "admin", "email": "", "contact": ""}

def update_admin_profile(username: str, email: str, contact: str):
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE Admin SET username=?, email=?, contact=? WHERE id=1",
                (username, email, contact)
            )
    except sqlite3.OperationalError as e:
        print(f"Warning (update_admin_profile): {e}")

def get_tenants() -> List[Dict[str, Any]]:
    """
    Fetches all tenants and joins their most recent active rental to retrieve
    the room number, start_date, and end_date.
    """
    query = """
        SELECT 
            t.TenantID as id,
            t.first_name || ' ' || t.last_name AS name,
            t.contact_number as contact,
            t.birthdate,
            t.sex,
            COALESCE(r.room_number, '—') as room,
            COALESCE(r.start_date, '') as start_date,
            COALESCE(r.end_date, '') as end_date
        FROM Tenant t
        LEFT JOIN (
            SELECT rnt.tenant_id, rnt.start_date, rnt.end_date, rm.room_number,
                   ROW_NUMBER() OVER(
                       PARTITION BY rnt.tenant_id 
                       ORDER BY COALESCE(rnt.end_date, '9999-12-31') DESC, rnt.start_date DESC
                   ) as rn
            FROM Rental rnt
            JOIN Room rm ON rnt.room_id = rm.RoomID
        ) r ON t.TenantID = r.tenant_id AND r.rn = 1
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            # sqlite3.Row objects act like dicts, we just convert them to true dicts for the UI
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"Warning (get_tenants): {e}")
        return []

def get_rooms() -> List[Dict[str, Any]]:
    """
    Fetches all rooms and determines their status based on occupied_slots.
    Also returns vacant slot count and the sex of current occupants.
    """
    query = """
        SELECT 
            rm.RoomID as id,
            rm.room_number as number,
            rm.room_type as type,
            rm.capacity,
            rm.occupied_slots,
            (rm.capacity - rm.occupied_slots) as vacant_slots,
            rm.monthly_rent as rent,
            CASE 
                WHEN rm.occupied_slots = 0 THEN 'Vacant'
                WHEN rm.occupied_slots < rm.capacity THEN 'Partially Occupied'
                ELSE 'Full'
            END as status,
            COALESCE(
                (SELECT GROUP_CONCAT(DISTINCT t.sex)
                 FROM Rental r
                 JOIN Tenant t ON r.tenant_id = t.TenantID
                 WHERE r.room_id = rm.RoomID
                   AND (r.end_date IS NULL OR r.end_date >= date('now'))
                ), ''
            ) as occupant_sex
        FROM Room rm
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = []
            for row in cursor.fetchall():
                d = dict(row)
                # Determine a friendly label for occupant sex
                sex_raw = d.get("occupant_sex", "")
                if not sex_raw:
                    d["occupant_sex"] = "—"
                elif "," in sex_raw:
                    d["occupant_sex"] = "Mixed"
                else:
                    d["occupant_sex"] = sex_raw
                rows.append(d)
            return rows
    except sqlite3.OperationalError as e:
        print(f"Warning (get_rooms): {e}")
        return []

def get_payments(month: str = None) -> List[Dict[str, Any]]:
    """
    Fetches payments by joining the Rental and Tenant tables to get tenant names.
    If month is provided, returns payments for that month PLUS all overdue payments.
    """
    query = """
        SELECT 
            p.PaymentID as id,
            p.rental_id,
            t.TenantID as tenant_id,
            t.first_name || ' ' || t.last_name as tenant,
            p.amount,
            p.due_date as due,
            COALESCE(p.payment_date, '') as paid_on,
            COALESCE(p.payment_type, '') as type,
            p.status
        FROM Payment p
        JOIN Rental r ON p.rental_id = r.RentalID
        JOIN Tenant t ON r.tenant_id = t.TenantID
    """
    params = []
    if month:
        query += " WHERE strftime('%Y-%m', p.due_date) = ?"
        params.append(month)
        
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"Warning (get_payments): {e}")
        return []

def get_unpaid_payments_for_tenant(tenant_id: int) -> List[Dict[str, Any]]:
    """Fetches any Unpaid or Overdue payments for a specific tenant."""
    query = """
        SELECT p.PaymentID as id, p.amount, p.due_date as due, p.status, p.payment_type as type
        FROM Payment p
        JOIN Rental r ON p.rental_id = r.RentalID
        WHERE r.tenant_id = ? AND p.status IN ('Unpaid', 'Overdue')
        ORDER BY p.due_date ASC
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (tenant_id,))
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"Warning (get_unpaid_payments_for_tenant): {e}")
        return []

def get_dashboard_stats(month: str = None) -> Dict[str, Any]:
    """
    Pre-computes and returns all statistics required by the dashboard and reports pages.
    Replaces python-side len() and sum() logic.
    """
    stats = {
        "active_tenants": 0,
        "vacant_units": 0,
        "partially_occupied": 0,
        "fully_occupied": 0,
        "occupied_rooms": 0,
        "total_rooms": 0,
        "paid_count": 0,
        "unpaid_count": 0,
        "overdue_count": 0,
        "total_revenue": 0,
        "average_rent": 0,
        "projected_revenue": 0
    }
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Active Tenants (tenants with an active rental)
            cursor.execute("SELECT COUNT(DISTINCT tenant_id) FROM Rental WHERE end_date IS NULL OR end_date >= date('now')")
            row = cursor.fetchone()
            if row: stats["active_tenants"] = row[0]
            
            # Room stats
            cursor.execute("SELECT COUNT(*) FROM Room")
            row = cursor.fetchone()
            if row: stats["total_rooms"] = row[0]
            
            cursor.execute("SELECT COUNT(*) FROM Room WHERE occupied_slots < capacity")
            row = cursor.fetchone()
            if row: stats["vacant_units"] = row[0]
            
            cursor.execute("SELECT COUNT(*) FROM Room WHERE occupied_slots > 0 AND occupied_slots < capacity")
            row = cursor.fetchone()
            if row: stats["partially_occupied"] = row[0]
            
            cursor.execute("SELECT COUNT(*) FROM Room WHERE occupied_slots = capacity")
            row = cursor.fetchone()
            if row: stats["fully_occupied"] = row[0]
            
            cursor.execute("SELECT COUNT(*) FROM Room WHERE occupied_slots > 0")
            row = cursor.fetchone()
            if row: stats["occupied_rooms"] = row[0]
            
            # Rent calculations
            cursor.execute("SELECT AVG(monthly_rent) FROM Room")
            row = cursor.fetchone()
            if row and row[0]: stats["average_rent"] = int(row[0])
            
            cursor.execute("SELECT SUM(amount) FROM Payment WHERE status != 'Paid'")
            row = cursor.fetchone()
            if row and row[0]: stats["projected_revenue"] = int(row[0])
            
            # Payment stats
            if month:
                cursor.execute("""
                    SELECT status, COUNT(*), SUM(amount) 
                    FROM Payment 
                    WHERE strftime('%Y-%m', due_date) = ?
                    GROUP BY status
                """, (month,))
            else:
                cursor.execute("SELECT status, COUNT(*), SUM(amount) FROM Payment GROUP BY status")
                
            for row in cursor.fetchall():
                status = row["status"]
                count = row[1]
                if status == 'Paid':
                    stats["paid_count"] = count
                    stats["total_revenue"] = row[2] or 0
                elif status == 'Unpaid':
                    stats["unpaid_count"] = count
                elif status == 'Overdue':
                    stats["overdue_count"] = count
                    
            # Override overdue_count to always reflect global overdue payments
            cursor.execute("SELECT COUNT(*) FROM Payment WHERE status = 'Overdue'")
            row = cursor.fetchone()
            if row: stats["overdue_count"] = row[0]
                    
    except sqlite3.OperationalError as e:
        print(f"Warning (get_dashboard_stats): {e}")
        
    return stats

def get_revenue_trend(period: str = "This Year") -> Tuple[List[float], List[str]]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if period == "This Year":
                cursor.execute("""
                    SELECT strftime('%m', payment_date) as month, SUM(amount) 
                    FROM Payment 
                    WHERE status = 'Paid' AND payment_date IS NOT NULL AND strftime('%Y', payment_date) = strftime('%Y', 'now')
                    GROUP BY month ORDER BY month
                """)
                data = [0] * 12
                labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                for row in cursor.fetchall():
                    data[int(row["month"]) - 1] = int(row[1])
                return data, labels
                
            elif period == "Last 6 Months":
                cursor.execute("""
                    SELECT strftime('%Y-%m', payment_date) as month, SUM(amount)
                    FROM Payment
                    WHERE status = 'Paid' AND payment_date IS NOT NULL AND payment_date >= date('now', 'start of month', '-5 months')
                    GROUP BY month ORDER BY month
                """)
                import datetime, calendar
                now = datetime.datetime.now()
                labels = []
                data = [0] * 6
                # Generate last 6 months labels
                for i in range(5, -1, -1):
                    m = now.month - i
                    y = now.year
                    while m <= 0:
                        m += 12
                        y -= 1
                    labels.append(calendar.month_abbr[m])
                
                # Map fetched YYYY-MM
                res = {row["month"]: int(row[1]) for row in cursor.fetchall()}
                for i in range(6):
                    m = now.month - (5 - i)
                    y = now.year
                    while m <= 0:
                        m += 12
                        y -= 1
                    key = f"{y}-{m:02d}"
                    data[i] = res.get(key, 0)
                return data, labels
                
            elif period == "This Month":
                cursor.execute("""
                    SELECT 
                        (cast(strftime('%d', payment_date) as integer) - 1) / 7 + 1 as week,
                        SUM(amount)
                    FROM Payment
                    WHERE status = 'Paid' AND payment_date IS NOT NULL AND strftime('%Y-%m', payment_date) = strftime('%Y-%m', 'now')
                    GROUP BY week ORDER BY week
                """)
                data = [0] * 4
                labels = ["Week 1", "Week 2", "Week 3", "Week 4+"]
                for row in cursor.fetchall():
                    week_idx = int(row["week"]) - 1
                    if week_idx >= 3: week_idx = 3 # cap at week 4
                    data[week_idx] += int(row[1])
                return data, labels
                
    except Exception as e:
        print(f"Warning (get_revenue_trend): {e}")
        
    return [0]*12, ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def delete_tenant(tenant_id: int):
    """
    Deletes a tenant. Also handles decrementing occupied_slots for any active rentals.
    Cascading deletes for Rental and Payment are handled by SQLite foreign keys.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Find active rentals for this tenant to decrement room slots
            cursor.execute("""
                SELECT room_id FROM Rental 
                WHERE tenant_id = ? AND (end_date IS NULL OR end_date >= date('now'))
            """, (tenant_id,))
            active_rooms = cursor.fetchall()
            
            for row in active_rooms:
                cursor.execute("""
                    UPDATE Room SET occupied_slots = max(0, occupied_slots - 1)
                    WHERE RoomID = ?
                """, (row["room_id"],))
                
            # Delete tenant. This automatically deletes associated Rentals and Payments 
            # if PRAGMA foreign_keys = ON is set (which it is in db.py).
            cursor.execute("DELETE FROM Tenant WHERE TenantID = ?", (tenant_id,))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Warning (delete_tenant): {e}")

def onboard_tenant(tenant_data: dict, room_id: int, room_rent: float, payment_data: dict) -> bool:
    """
    Onboards a new tenant by inserting records into Tenant, Rental, and Payment tables.
    Also increments the occupied_slots for the assigned Room.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Insert Tenant
            full_name = tenant_data.get("name", "").strip()
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""
            
            cursor.execute("""
                INSERT INTO Tenant (first_name, last_name, contact_number, birthdate, sex)
                VALUES (?, ?, ?, ?, ?)
            """, (first_name, last_name, tenant_data.get("contact"), tenant_data.get("birthdate"), tenant_data.get("sex")))
            
            tenant_id = cursor.lastrowid
            
            # 2. Insert Rental
            move_in = payment_data.get("move_in")
            cursor.execute("""
                INSERT INTO Rental (tenant_id, room_id, start_date)
                VALUES (?, ?, ?)
            """, (tenant_id, room_id, move_in))
            
            rental_id = cursor.lastrowid
            
            # 3. Update Room Occupancy
            cursor.execute("""
                UPDATE Room SET occupied_slots = occupied_slots + 1
                WHERE RoomID = ?
            """, (room_id,))
            
            # 4. Insert Deposit Payment
            deposit = payment_data.get("deposit", 0)
            if deposit > 0:
                cursor.execute("""
                    INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                    VALUES (?, ?, ?, ?, 'Paid', 'Deposit')
                """, (rental_id, deposit, move_in, move_in))
                
            # 5. First month rent is always paid on move-in
            rent_paid = payment_data.get("rent", room_rent)
            cursor.execute("""
                INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                VALUES (?, ?, ?, ?, 'Paid', 'Regular')
            """, (rental_id, rent_paid, move_in, move_in))
            
            conn.commit()
            return True
    except sqlite3.OperationalError as e:
        print(f"Error onboarding tenant: {e}")
        return False

def add_tenant(record: dict) -> int:
    name = record.get("name", "").strip()
    parts = name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Tenant (first_name, last_name, contact_number, birthdate, sex)
                VALUES (?, ?, ?, ?, ?)
            """, (first_name, last_name, record.get("contact"), record.get("birthdate"), record.get("sex")))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.OperationalError as e:
        print(f"Warning (add_tenant): {e}")
        return 0

def update_tenant(tenant_id: int, record: dict):
    name = record.get("name", "").strip()
    parts = name.split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Tenant 
                SET first_name=?, last_name=?, contact_number=?, birthdate=?, sex=?
                WHERE TenantID=?
            """, (first_name, last_name, record.get("contact"), record.get("birthdate"), record.get("sex"), tenant_id))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Warning (update_tenant): {e}")

def add_room(record: dict) -> int:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Room (room_number, room_type, capacity, occupied_slots, monthly_rent, deposit)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (
                record.get("number"),
                record.get("type"),
                int(record.get("capacity", 1)),
                int(record.get("rent", 0)),
                int(record.get("rent", 0))
            ))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Warning (add_room): {e}")
        return 0

def update_room(room_id: int, record: dict):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Room 
                SET room_number=?, room_type=?, capacity=?, monthly_rent=?
                WHERE RoomID=?
            """, (record.get("number"), record.get("type"), int(record.get("capacity", 1)), int(record.get("rent", 0)), room_id))
            conn.commit()
    except Exception as e:
        print(f"Warning (update_room): {e}")

def delete_room(room_id: int):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Room WHERE RoomID=?", (room_id,))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Warning (delete_room): {e}")

def add_payment(record: dict) -> int:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            tid_val = record.get("tenant_id", "0")
            if isinstance(tid_val, str):
                tid_val = tid_val.replace("T-", "").strip()
            tenant_id = int(tid_val or 0)
            
            cursor.execute("SELECT RentalID FROM Rental WHERE tenant_id=? ORDER BY end_date DESC LIMIT 1", (tenant_id,))
            row = cursor.fetchone()
            if row:
                rental_id = row[0]
                due_date = record.get("due")
                month = due_date[:7] if due_date else ""
                
                # Check for any existing payment for this month and rental
                cursor.execute("""
                    SELECT PaymentID, status FROM Payment 
                    WHERE rental_id=?
                      AND strftime('%Y-%m', due_date) = ?
                      AND payment_type = 'Regular'
                """, (rental_id, month))
                existing = cursor.fetchone()

                if existing:
                    # Always update existing record — replaces unpaid/overdue/advance
                    cursor.execute("""
                        UPDATE Payment
                        SET amount=?, due_date=?, payment_date=?, status=?, payment_type='Regular'
                        WHERE PaymentID=?
                    """, (record.get("amount"), due_date, record.get("paid_on") or None, record.get("status"), existing[0]))
                    conn.commit()
                    return existing["PaymentID"]
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                        VALUES (?, ?, ?, ?, ?, 'Regular')
                    """, (rental_id, record.get("amount"), due_date, record.get("paid_on") or None, record.get("status")))
                    conn.commit()
                    return cursor.lastrowid
            return 0
    except sqlite3.OperationalError as e:
        print(f"Warning (add_payment): {e}")
        return 0

def update_payment(payment_id: int, record: dict):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Payment SET amount=?, due_date=?, payment_date=?, status=? WHERE PaymentID=?
            """, (record.get("amount"), record.get("due"), record.get("paid_on") if record.get("paid_on") else None, record.get("status"), payment_id))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Warning (update_payment): {e}")

def delete_payment(payment_id: int):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Payment WHERE PaymentID=?", (payment_id,))
            conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Warning (delete_payment): {e}")


def end_rental(tenant_id: int) -> bool:
    """Sets today as the end_date on the tenant's active rental and decrements room slot."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT RentalID, room_id FROM Rental
                WHERE tenant_id = ? AND (end_date IS NULL OR end_date >= date('now'))
                ORDER BY start_date DESC LIMIT 1
            """, (tenant_id,))
            row = cursor.fetchone()
            if not row:
                return False
            cursor.execute("""
                UPDATE Rental SET end_date = date('now') WHERE RentalID = ?
            """, (row["RentalID"],))
            cursor.execute("""
                UPDATE Room SET occupied_slots = max(0, occupied_slots - 1) WHERE RoomID = ?
            """, (row["room_id"],))
            conn.commit()
            return True
    except Exception as e:
        print(f"Warning (end_rental): {e}")
        return False

def transfer_tenant(tenant_id: int, new_room_id: int, new_rent: float) -> bool:
    """Ends the active rental and creates a new one in the target room."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # End current rental
            cursor.execute("""
                SELECT RentalID, room_id FROM Rental
                WHERE tenant_id = ? AND (end_date IS NULL OR end_date >= date('now'))
                ORDER BY start_date DESC LIMIT 1
            """, (tenant_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE Rental SET end_date = date('now') WHERE RentalID = ?
                """, (row["RentalID"],))
                cursor.execute("""
                    UPDATE Room SET occupied_slots = max(0, occupied_slots - 1) WHERE RoomID = ?
                """, (row["room_id"],))
            # Start new rental
            cursor.execute("""
                INSERT INTO Rental (tenant_id, room_id, start_date)
                VALUES (?, ?, date('now'))
            """, (tenant_id, new_room_id))
            cursor.execute("""
                UPDATE Room SET occupied_slots = occupied_slots + 1 WHERE RoomID = ?
            """, (new_room_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Warning (transfer_tenant): {e}")
        return False

def get_tenant_rent(tenant_id: int) -> float:
    """Returns the monthly rent of the tenant's currently active room."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rm.monthly_rent FROM Rental rnt
                JOIN Room rm ON rnt.room_id = rm.RoomID
                WHERE rnt.tenant_id = ?
                  AND (rnt.end_date IS NULL OR rnt.end_date > date('now'))
                ORDER BY rnt.start_date DESC LIMIT 1
            """, (tenant_id,))
            row = cursor.fetchone()
            return float(row[0]) if row else 0.0
    except Exception as e:
        print(f"Warning (get_tenant_rent): {e}")
        return 0.0

def generate_monthly_payments():
    """
    For every active rental, generates an Unpaid payment record for each month
    from start_date up to the current month if one doesn't already exist.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rnt.RentalID, rnt.tenant_id, rnt.start_date, rnt.end_date,
                       rm.monthly_rent
                FROM Rental rnt
                JOIN Room rm ON rnt.room_id = rm.RoomID
                WHERE rnt.end_date IS NULL OR rnt.end_date > date('now')
            """)
            rentals = cursor.fetchall()

            from datetime import date, timedelta
            today = date.today()

            for rental in rentals:
                rental_id   = rental["RentalID"]
                start       = date.fromisoformat(rental["start_date"])
                rent        = rental["monthly_rent"]

                # Walk month by month from start+1 month up to today
                m = start.month + 1
                y = start.year
                if m > 12:
                    m = 1
                    y += 1
                next_m = today.month + 1
                next_y = today.year
                if next_m > 12:
                    next_m = 1
                    next_y += 1
                while (y, m) <= (next_y, next_m):
                    import calendar
                    last_day = calendar.monthrange(y, m)[1]
                    day = min(start.day, last_day)
                    due = date(y, m, day)
                    month_key = f"{y}-{m:02d}"

                    # Check if a payment already exists for this rental+month
                    cursor.execute("""
                        SELECT PaymentID FROM Payment
                        WHERE rental_id = ?
                          AND strftime('%Y-%m', due_date) = ?
                          AND payment_type = 'Regular'
                    """, (rental_id, month_key))
                    if not cursor.fetchone():
                        status = "Overdue" if due < today else "Unpaid"
                        # Next month's payment is always Unpaid not Overdue
                        if (y, m) == (next_y, next_m):
                            status = "Unpaid"
                        cursor.execute("""
                            INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                            VALUES (?, ?, ?, NULL, ?, 'Regular')
                        """, (rental_id, rent, due.isoformat(), status))

                    # Advance one month
                    m += 1
                    if m > 12:
                        m = 1
                        y += 1

            conn.commit()
    except Exception as e:
        print(f"Warning (generate_monthly_payments): {e}")

def mark_payment_paid(payment_id: int) -> bool:
    """Marks a payment as Paid with today as the payment date."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Payment SET status='Paid', payment_date=date('now')
                WHERE PaymentID=?
            """, (payment_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Warning (mark_payment_paid): {e}")
        return False

def update_overdue_payments():
    """Marks any Unpaid payments past their due date as Overdue."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Payment SET status = 'Overdue'
                WHERE status = 'Unpaid' AND due_date < date('now')
            """)
            conn.commit()
    except Exception as e:
        print(f"Warning (update_overdue_payments): {e}")