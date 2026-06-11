import sqlite3
from typing import List, Dict, Any
from .db import get_connection

def get_tenants() -> List[Dict[str, Any]]:
    """
    Fetches all tenants and joins their most recent active rental to retrieve
    the start_date and end_date.
    """
    query = """
        SELECT 
            t.TenantID as id,
            t.first_name || ' ' || t.last_name AS name,
            t.contact_number as contact,
            t.birthdate,
            t.sex,
            COALESCE(r.start_date, '') as start_date,
            COALESCE(r.end_date, '') as end_date
        FROM Tenant t
        LEFT JOIN (
            SELECT tenant_id, start_date, end_date,
                   ROW_NUMBER() OVER(PARTITION BY tenant_id ORDER BY end_date DESC) as rn
            FROM Rental
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
        query += " WHERE strftime('%Y-%m', p.due_date) = ? OR p.status = 'Overdue'"
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
        "occupied_rooms": 0,
        "maintenance_rooms": 0,
        "total_rooms": 0,
        "paid_count": 0,
        "unpaid_count": 0,
        "overdue_count": 0,
        "total_revenue": 0
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
            
            cursor.execute("SELECT COUNT(*) FROM Room WHERE occupied_slots = 0")
            row = cursor.fetchone()
            if row: stats["vacant_units"] = row[0]
            
            cursor.execute("SELECT COUNT(*) FROM Room WHERE occupied_slots > 0")
            row = cursor.fetchone()
            if row: stats["occupied_rooms"] = row[0]
            
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

def get_revenue_monthly() -> List[int]:
    """
    Fallback mock implementation for monthly revenue chart data, as the schema 
    doesn't easily provide 12 months of historical data without more complex date parsing
    and assuming data density. In a full implementation, you would GROUP BY strftime('%m', payment_date).
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%m', payment_date) as month, SUM(amount) 
                FROM Payment 
                WHERE status = 'Paid' AND payment_date IS NOT NULL
                GROUP BY month
                ORDER BY month
            """)
            # Initialize 12 months to 0
            monthly = [0] * 12
            for row in cursor.fetchall():
                # month is '01' to '12'
                m_idx = int(row["month"]) - 1
                monthly[m_idx] = int(row[1])
            return monthly
    except (sqlite3.OperationalError, TypeError) as e:
        print(f"Warning (get_revenue_monthly): {e}")
        # Return fallback mock data to prevent UI from breaking if DB is empty
        return [12000, 15500, 17000, 21000, 19500, 23000, 24500, 26000, 28500, 27000, 31000, 28000]

def get_revenue_labels() -> List[str]:
    return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

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
                
            # 5. Insert First Month Rent Payment
            pay_rent = payment_data.get("pay_rent", False)
            if pay_rent:
                rent_paid = payment_data.get("rent", 0)
                cursor.execute("""
                    INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                    VALUES (?, ?, ?, ?, 'Paid', 'Regular')
                """, (rental_id, rent_paid, move_in, move_in))
            else:
                # Generate an Unpaid invoice for the first month
                cursor.execute("""
                    INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                    VALUES (?, ?, ?, NULL, 'Unpaid', 'Regular')
                """, (rental_id, room_rent, move_in))
            
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
            """, (record.get("number"), record.get("type"), record.get("capacity"), record.get("rent", 0), record.get("rent", 0)))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.OperationalError as e:
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
            """, (record.get("number"), record.get("type"), record.get("capacity"), record.get("rent"), room_id))
            conn.commit()
    except sqlite3.OperationalError as e:
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
                
                # Check for existing unpaid/overdue payment for this month and rental
                cursor.execute("""
                    SELECT PaymentID FROM Payment 
                    WHERE rental_id=? AND status IN ('Unpaid', 'Overdue') 
                      AND strftime('%Y-%m', due_date) = ?
                """, (rental_id, month))
                existing = cursor.fetchone()
                
                if existing:
                    # Update the existing unpaid record
                    cursor.execute("""
                        UPDATE Payment
                        SET amount=?, due_date=?, payment_date=?, status=?, payment_type='Regular'
                        WHERE PaymentID=?
                    """, (record.get("amount"), due_date, record.get("paid_on") or None, record.get("status"), existing[0]))
                    conn.commit()
                    return existing[0]
                else:
                    # Insert new record if none exists
                    cursor.execute("""
                        INSERT INTO Payment (rental_id, amount, due_date, payment_date, status, payment_type)
                        VALUES (?, ?, ?, ?, ?, 'Regular')
                    """, (rental_id, record.get("amount"), due_date, record.get("paid_on") if record.get("paid_on") else None, record.get("status")))
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
