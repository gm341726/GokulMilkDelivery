import sqlite3

conn = sqlite3.connect("milk_delivery.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    mobile TEXT,
    address TEXT,
    route TEXT,
    morning REAL,
    evening REAL,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")