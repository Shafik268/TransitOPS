import sqlite3
import os

# Connect to your database
db_path = os.path.join('database', 'transitops.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
print("--- REGISTERED TABLES ---")
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
for t in tables:
    print(f"📁 {t[0]}")

# Change 'managers' to any table name you want to inspect (e.g., 'vehicles', 'trips')
table_to_view = 'managers' 
print(f"\n--- DATA INSIDE '{table_to_view.upper()}' TABLE ---")

try:
    rows = cursor.execute(f"SELECT * FROM {table_to_view}").fetchall()
    if not rows:
        print("Table is currently empty.")
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error reading table: {e}")

conn.close()