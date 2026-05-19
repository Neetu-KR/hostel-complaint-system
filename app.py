from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "hostel_secret_key"


# ---------------- DATABASE FUNCTION ----------------
def get_db_connection():
    conn = sqlite3.connect("hostel.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            room_no TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- STUDENT REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO students (name, email, password) VALUES (?, ?, ?)",
                           (name, email, password))
            conn.commit()
            flash("Registration Successful! Please login.", "success")
            return redirect(url_for("login"))
        except:
            flash("Email already exists! Try another email.", "danger")

        conn.close()

    return render_template("register.html")


# ---------------- STUDENT LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE email=? AND password=?",
                       (email, password))
        student = cursor.fetchone()
        conn.close()

        if student:
            session["student"] = student["name"]
            return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html")


# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student_dashboard")
def student_dashboard():
    if "student" not in session:
        return redirect(url_for("login"))

    student_name = session["student"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM complaints WHERE student_name=?", (student_name,))
    complaints = cursor.fetchall()

    conn.close()

    return render_template("student_dashboard.html", student_name=student_name, complaints=complaints)


# ---------------- FILE COMPLAINT ----------------
@app.route("/complaint", methods=["GET", "POST"])
def complaint():
    if "student" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        student_name = session["student"]
        room_no = request.form["room_no"]
        category = request.form["category"]
        description = request.form["description"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO complaints (student_name, room_no, category, description)
            VALUES (?, ?, ?, ?)
        """, (student_name, room_no, category, description))

        conn.commit()
        conn.close()

        flash("Complaint Submitted Successfully!", "success")
        return redirect(url_for("student_dashboard"))

    return render_template("complaint.html")


# ---------------- STUDENT LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("student", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hardcoded admin login (simple for college project)
        if username == "admin" and password == "admin123":
            session["admin"] = "admin"
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid Admin Credentials!", "danger")

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM complaints")
    complaints = cursor.fetchall()

    conn.close()

    return render_template("admin_dashboard.html", complaints=complaints)


# ---------------- UPDATE COMPLAINT STATUS ----------------
@app.route("/update_status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    new_status = request.form["status"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE complaints SET status=? WHERE id=?",
                   (new_status, complaint_id))

    conn.commit()
    conn.close()

    flash("Complaint Status Updated!", "success")
    return redirect(url_for("admin_dashboard"))


# ---------------- DELETE COMPLAINT ----------------
@app.route("/delete_complaint/<int:complaint_id>")
def delete_complaint(complaint_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM complaints WHERE id=?", (complaint_id,))
    conn.commit()
    conn.close()

    flash("Complaint Deleted Successfully!", "success")
    return redirect(url_for("admin_dashboard"))


# ---------------- ADMIN LOGOUT ----------------
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    flash("Admin Logged out!", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)