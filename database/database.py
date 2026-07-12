import sqlite3
import os

def get_db_connection(db_path):
    """Factory creating isolated transactional connections with foreign keys enabled."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db(db_path):
    """Construct structural tabular matrices including auth entities."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
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
            FOREIGN KEY(vehicle_ref) REFERENCES vehicles(reg_num) ON DELETE CASCADE,
            FOREIGN KEY(driver_ref) REFERENCES drivers(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ref TEXT NOT NULL,
            title TEXT NOT NULL,
            cost REAL NOT NULL,
            log_date TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            notes TEXT,
            FOREIGN KEY(vehicle_ref) REFERENCES vehicles(reg_num) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fuel_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ref TEXT NOT NULL,
            liters REAL NOT NULL,
            cost REAL NOT NULL,
            log_date TEXT NOT NULL,
            FOREIGN KEY(vehicle_ref) REFERENCES vehicles(reg_num) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_ref TEXT NOT NULL,
            expense_type TEXT NOT NULL,
            cost REAL NOT NULL,
            log_date TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY(vehicle_ref) REFERENCES vehicles(reg_num) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS managers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()