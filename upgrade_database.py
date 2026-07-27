import sqlite3

conn = sqlite3.connect("milk_delivery.db")
cursor = conn.cursor()

columns = [
    ("house_no", "TEXT"),
    ("price_per_litre", "REAL"),
    ("start_date", "TEXT"),
    ("latitude", "REAL"),
    ("longitude", "REAL")
]

for column_name, column_type in columns:
    try:
        cursor.execute(
            f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}"
        )
        print(f"{column_name} added.")
    except sqlite3.OperationalError:
        print(f"{column_name} already exists.")

conn.commit()
conn.close()

print("Database upgraded successfully.")