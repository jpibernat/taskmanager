# auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from models import AuthUser

auth_bp = Blueprint("auth", __name__)

def get_db():
    conn = current_app.config["DB_CONN"]
    cursor = current_app.config["DB_CURSOR"]
    return conn, cursor

def get_bcrypt():
    return current_app.config["BCRYPT"]

# --- Login ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn, cursor = get_db()
        bcrypt = get_bcrypt()

        cursor.execute("SELECT id, email, first_name, last_name, role, password_hash FROM auth_users WHERE email=%s", (email,))
        row = cursor.fetchone()

        if row and bcrypt.check_password_hash(row["password_hash"], password):
            user = AuthUser(row["id"], row["email"], row["first_name"], row["last_name"], row["role"])
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

# --- Register ---
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not first_name or not last_name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for("auth.register"))

        conn, cursor = get_db()
        bcrypt = get_bcrypt()

        cursor.execute("SELECT id FROM auth_users WHERE email=%s", (email,))
        existing = cursor.fetchone()
        if existing:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            cursor.execute(
                """INSERT INTO auth_users (first_name, last_name, email, password_hash, role) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (first_name, last_name, email, password_hash, "user")
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            conn.rollback()
            flash(f"Error registering user: {e}", "danger")

    return render_template("register.html")

# --- Admin Required Decorator ---
def admin_required(f): 
    @wraps(f) 
    def decorated_function(*args, **kwargs): 
        if not current_user.is_authenticated or current_user.role != "admin": 
            abort(403) 
        return f(*args, **kwargs) 
    return decorated_function

# --- Admin Dashboard ---
@auth_bp.route("/admin")
@admin_required
def admin_dashboard():
    return "Welcome, admin!"

# --- Manage Users ---
@auth_bp.route("/admin/users")
@admin_required
def manage_users():
    _, cursor = get_db()
    cursor.execute("SELECT id, first_name, last_name, email, role FROM auth_users")
    users = cursor.fetchall()
    return render_template("manage_users.html", users=users)

@auth_bp.route("/admin/user/<int:user_id>/set_role", methods=["POST"])
@admin_required
def set_role(user_id):
    new_role = request.form["role"]
    conn, cursor = get_db()
    cursor.execute("UPDATE auth_users SET role=%s WHERE id=%s", (new_role, user_id))
    conn.commit()
    flash("User role updated successfully!", "success")
    return redirect(url_for("auth.manage_users"))

@auth_bp.route("/admin/user/<int:user_id>/reset_password", methods=["POST"])
@admin_required
def reset_password(user_id):
    new_password = request.form["new_password"]
    conn, cursor = get_db()
    bcrypt = get_bcrypt()
    password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    cursor.execute("UPDATE auth_users SET password_hash=%s WHERE id=%s", (password_hash, user_id))
    conn.commit()
    flash("Password reset successfully!", "success")
    return redirect(url_for("auth.manage_users"))

# --- Logout ---
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
