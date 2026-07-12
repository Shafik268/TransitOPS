import sqlite3
import os

def get_db_connection(db_path):
    """Factory creating isolated transactional low-level connection states."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    """Construct structural tabular matrices """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Master Vehicle Database Entity
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            reg_num TEXT PRIMARY KEY,
            model TEXT NOT NULL,
            type TEXT NOT NULL,
            max_capacity REAL NOT NULL,
            odometer REAL NOT NULL,
            acquisition_cost REAL NOT NULL,
            status TEXT DEFAULT 'Available'
        )
    ''')
    
    # 2. Master Driver Database Entity
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            license_num TEXT UNIQUE NOT NULL,
            license_cat TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            contact TEXT NOT NULL,
            safety_score REAL NOT NULL,
            status TEXT DEFAULT 'Available'
        )
    ''')
    
    # 3. Transactional Trip Lifecycle Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            vehicle_ref TEXT NOT NULL,
            driver_ref INTEGER NOT NULL,
            cargo_weight REAL NOT NULL,
            planned_distance REAL NOT NULL,
            status TEXT DEFAULT 'Draft',
            FOREIGN KEY(vehicle_ref) REFERENCES vehicles(reg_num),
            FOREIGN KEY(driver_ref) REFERENCES drivers(id)
        )
    ''')

    conn.commit()
    conn.close()