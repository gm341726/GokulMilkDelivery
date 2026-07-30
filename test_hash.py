import sqlite3
from werkzeug.security import check_password_hash

conn = sqlite3.connect("milk_delivery.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT * FROM admin WHERE username=?", ("Gokul",))
admin = cursor.fetchone()

print("Username:", admin["username"])
print("Hash:", admin["password"])
print("Password OK:", check_password_hash(admin["password"], "gokul@#2026",))

conn.close()
