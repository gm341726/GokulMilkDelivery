import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import Flask, render_template, request, redirect, send_file, session
from datetime import date

app = Flask(__name__)
app.secret_key = "gokul_milk_secret_key"
# =========================
# Login Page
# =========================
@app.route("/")
def login():
    return render_template("login.html")


# =========================
# Login Verification
# =========================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("milk_delivery.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )

        admin = cursor.fetchone()

        if admin is None:
            conn.close()
            return "<h2>❌ Invalid Username or Password</h2><a href='/'>Back to Login</a>"

        session["username"] = username

    else:
        # User opened /dashboard directly
        if "username" not in session:
            return redirect("/")

        username = session["username"]

        conn = sqlite3.connect("milk_delivery.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    # Total Customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    # Active Customers
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status='Active'")
    active_customers = cursor.fetchone()[0]

    # Inactive Customers
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status='Inactive'")
    inactive_customers = cursor.fetchone()[0]

    # Monthly Revenue
    cursor.execute("""
        SELECT SUM(
            (CAST(morning AS REAL) + CAST(evening AS REAL))
            * price_per_litre * 30
        )
        FROM customers
        WHERE status='Active'
    """)

    monthly_revenue = cursor.fetchone()[0] or 0
# Today's Deliveries
    cursor.execute("""
    SELECT COUNT(*)
    FROM deliveries
    WHERE delivery_date = DATE('now')
    """)
    today_deliveries = cursor.fetchone()[0]

# Pending Payments
    cursor.execute("""
    SELECT COUNT(*)
    FROM payments
    WHERE status='Pending'
    """)
    pending_payments = cursor.fetchone()[0]
    conn.close()

    return render_template(
    "dashboard.html",
    username=username,
    total_customers=total_customers,
    active_customers=active_customers,
    inactive_customers=inactive_customers,
    monthly_revenue=monthly_revenue,
    today_deliveries=today_deliveries,
    pending_payments=pending_payments
)

# =========================
# Add Customer Page
# =========================
@app.route("/customers")
def customers(): 
    if "username" not in session:
        return redirect("/")
        return render_template("customers.html")


# =========================
# Save Customer
# =========================
@app.route("/save_customer", methods=["POST"])
def save_customer():

    conn = sqlite3.connect("milk_delivery.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers (
            name, house_no, mobile, address, route,
            morning, evening, price_per_litre,
            start_date, status, latitude, longitude
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form.get("name"),
        request.form.get("house_no"),
        request.form.get("mobile"),
        request.form.get("address"),
        request.form.get("route"),
        request.form.get("morning"),
        request.form.get("evening"),
        request.form.get("price_per_litre"),
        request.form.get("start_date"),
        request.form.get("status"),
        request.form.get("latitude"),
        request.form.get("longitude")
    ))

    conn.commit()
    conn.close()
    backup_database()
    return redirect("/customer_list")


# =========================
# Customer List + Search
# =========================
@app.route("/customer_list")
def customer_list():
    if "username" not in session:
        return redirect("/")
    search = request.args.get("search", "")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM customers
            WHERE name LIKE ?
               OR mobile LIKE ?
               OR route LIKE ?
               OR house_no LIKE ?
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))
    else:
        cursor.execute("SELECT * FROM customers ORDER BY id DESC")

    customers = cursor.fetchall()

    conn.close()

    return render_template(
        "customer_list.html",
        customers=customers,
        search=search
    )


# =========================
# Edit Customer
# =========================
@app.route("/edit_customer/<int:id>")
def edit_customer(id):
    if "username" not in session:
        return redirect("/")
    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers WHERE id=?", (id,))
    customer = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_customer.html",
        customer=customer
    )


# =========================
# Update Customer
# =========================
@app.route("/update_customer/<int:id>", methods=["POST"])
def update_customer(id):
    if "username" not in session:
        return redirect("/")
    conn = sqlite3.connect("milk_delivery.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE customers
        SET name=?, house_no=?, mobile=?, address=?, route=?,
            morning=?, evening=?, price_per_litre=?,
            start_date=?, status=?, latitude=?, longitude=?
        WHERE id=?
    """, (
        request.form.get("name"),
        request.form.get("house_no"),
        request.form.get("mobile"),
        request.form.get("address"),
        request.form.get("route"),
        request.form.get("morning"),
        request.form.get("evening"),
        request.form.get("price_per_litre"),
        request.form.get("start_date"),
        request.form.get("status"),
        request.form.get("latitude"),
        request.form.get("longitude"),
        id
    ))

    conn.commit()
    conn.close()

    return redirect("/customer_list")


# =========================
# Delete Customer
# =========================
@app.route("/delete_customer/<int:id>")
def delete_customer(id):

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM customers WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/customer_list")


# =========================
# Customer Map
# =========================
@app.route("/map")
def customer_map():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM customers
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)

    customers = cursor.fetchall()

    conn.close()

    return render_template(
        "map.html",
        customers=customers
    )


# =========================
# Monthly Bill
# =========================
@app.route("/bill/<int:id>")
def bill(id):

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers WHERE id=?", (id,))
    customer = cursor.fetchone()

    conn.close()

    return render_template(
        "bill.html",
        customer=customer
    )

@app.route("/check_customers")
def check_customers():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, latitude, longitude
        FROM customers
    """)

    rows = cursor.fetchall()

    conn.close()

    result = ""

    for r in rows:
        result += f"{r['id']} | {r['name']} | {r['latitude']} | {r['longitude']}<br>"

    return result
#===============
#daily delivery
#===============
@app.route("/daily_delivery")
def daily_delivery():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM customers
        WHERE status='Active'
        ORDER BY name
    """)

    customers = cursor.fetchall()

    conn.close()

    return render_template(
        "daily_delivery.html",
        customers=customers
    )
    # =========================
# Mark Daily Delivery
# =========================
@app.route("/mark_delivery/<int:customer_id>", methods=["POST"])
def mark_delivery(customer_id):

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    cursor = conn.cursor()

    today = date.today().isoformat()

    morning_status = request.form.get("morning_status")
    evening_status = request.form.get("evening_status")

    cursor.execute("""
        INSERT INTO deliveries
        (customer_id, delivery_date, morning_status, evening_status)
        VALUES (?, ?, ?, ?)
    """, (
        customer_id,
        today,
        morning_status,
        evening_status
    ))

    conn.commit()
    conn.close()

    return redirect("/daily_delivery")
    
    # =========================
# Delivery History
# =========================
@app.route("/delivery_history")
def delivery_history():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT deliveries.*,
               customers.name
        FROM deliveries
        JOIN customers
        ON deliveries.customer_id = customers.id
        ORDER BY delivery_date DESC
    """)

    deliveries = cursor.fetchall()

    conn.close()

    return render_template(
        "delivery_history.html",
        deliveries=deliveries
    )
    # =========================
# Payment Page
# =========================
@app.route("/payments")
def payments():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM customers
        ORDER BY name
    """)

    customers = cursor.fetchall()

    conn.close()

    return render_template(
        "payments.html",
        customers=customers
    )
    # =========================
# Payment Form
# =========================
@app.route("/pay/<int:id>")
def pay(id):

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM customers WHERE id=?",
        (id,)
    )

    customer = cursor.fetchone()

    conn.close()

    return render_template(
        "pay.html",
        customer=customer
    )
    # =========================
# Save Payment
# =========================
@app.route("/save_payment/<int:id>", methods=["POST"])
def save_payment(id):

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO payments
        (
            customer_id,
            payment_date,
            amount,
            payment_method,
            status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (

        id,
        request.form.get("payment_date"),
        request.form.get("amount"),
        request.form.get("payment_method"),
        request.form.get("status")

    ))

    conn.commit()
    conn.close()
    backup_database()
    return redirect("/payments")
    # =========================
# Payment History
# =========================
@app.route("/payment_history")
def payment_history():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT payments.*,
               customers.name
        FROM payments
        JOIN customers
        ON payments.customer_id = customers.id
        ORDER BY payment_date DESC
    """)

    payments = cursor.fetchall()

    conn.close()

    return render_template(
        "payment_history.html",
        payments=payments
    )
    # =========================
# Download PDF Bill
# =========================
@app.route("/download_bill/<int:id>")
def download_bill(id):

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers WHERE id=?", (id,))
    customer = cursor.fetchone()

    conn.close()

    pdf_file = f"bill_{id}.pdf"

    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Gokul Milk Delivery</b>", styles["Title"]))
    story.append(Paragraph(f"Customer: {customer['name']}", styles["Normal"]))
    story.append(Paragraph(f"House No: {customer['house_no']}", styles["Normal"]))
    story.append(Paragraph(f"Mobile: {customer['mobile']}", styles["Normal"]))

    morning = float(customer["morning"] or 0)
    evening = float(customer["evening"] or 0)
    price = float(customer["price_per_litre"] or 0)

    total = (morning + evening) * price * 30

    story.append(Paragraph(f"Monthly Bill: ₹ {total:.2f}", styles["Heading2"]))

    doc.build(story)

    return send_file(pdf_file, as_attachment=True)
    # =========================
# Revenue Report
# =========================
@app.route("/revenue")
def revenue():

    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect("milk_delivery.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT SUM(amount)
        FROM payments
        WHERE status='Paid'
    """)
    total_revenue = cursor.fetchone()[0]

    if total_revenue is None:
        total_revenue = 0

    cursor.execute("SELECT COUNT(*) FROM payments")
    total_payments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("""
        SELECT payments.*,
               customers.name
        FROM payments
        JOIN customers
        ON payments.customer_id = customers.id
        ORDER BY payment_date DESC
        LIMIT 10
    """)

    payments = cursor.fetchall()

    conn.close()

    return render_template(
        "revenue.html",
        total_revenue=total_revenue,
        total_payments=total_payments,
        total_customers=total_customers,
        payments=payments
    )
    # =========================
# Logout
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#====page not found======
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"),404
#====server error==========
@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"),500
#====data base==============
import shutil
import datetime

def backup_database():

    date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    shutil.copy(
        "milk_delivery.db",
        f"backup/milk_delivery_{date}.db"
    )

# =========================
# Run Flask App
# =========================
import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )