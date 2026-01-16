from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from models import AuthUser

task_bp = Blueprint("task", __name__)

def get_db():
    conn = current_app.config["DB_CONN"]
    cursor = current_app.config["DB_CURSOR"]
    return conn, cursor

def get_bcrypt():
    return current_app.config["BCRYPT"]

### ADD TASK ROUTE ###
@task_bp.route("/add_task", methods=["GET", "POST"])
@login_required
def add_task():
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch all auth_users for dropdowns (owner and assigned_id)
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        status = request.form["status"]
        area = request.form.get("area")
        type_ = request.form.get("type")
        start_date = request.form.get("start_date")
        due_date = request.form.get("due_date")
        priority = request.form.get("priority")
        ticket_number = request.form.get("ticket_number")
        mantis_number = request.form.get("mantis_number")
        owner_id = request.form.get("owner_id")
        assigned_id = request.form.get("assigned_id")   # renamed field

        # Basic validation
        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("task.add_task"))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("add_task"))

        try:
            cursor.execute(
                """INSERT INTO tasks 
                   (title, description, status, area, type, start_date, due_date, priority, 
                    ticket_number, mantis_number, owner_id, assigned_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (title, description, status, area, type_, start_date, due_date, priority,
                 ticket_number, mantis_number, owner_id, assigned_id)
            )
            conn.commit()
            flash("Task added successfully!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding task: {e}", "danger")
            return redirect(url_for("task.add_task"))

    return render_template("add_task.html", users=users, VALID_STATUSES=VALID_STATUSES)

### TASK DETAIL ROUTE ###
@task_bp.route("/task/<int:task_id>")
@login_required
def task_detail(task_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch the task with owner and assigned user names
    cursor.execute("""
        SELECT t.*, 
               CONCAT(o.first_name, ' ', o.last_name) AS owner_name, 
               CONCAT(a.first_name, ' ', a.last_name) AS assigned_name
        FROM tasks t
        LEFT JOIN auth_users o ON t.owner_id = o.id
        LEFT JOIN auth_users a ON t.assigned_id = a.id
        WHERE t.task_id = %s
    """, (task_id,))
    task = cursor.fetchone()

    if not task:
        flash("Task not found!", "danger")
        return redirect(url_for("index"))

    # Fetch subtasks with assigned user names
    cursor.execute("""
        SELECT s.*, CONCAT(u.first_name, ' ', u.last_name) AS assigned_name
        FROM subtasks s
        LEFT JOIN auth_users u ON s.assigned_id = u.id
        WHERE s.parent_task_id = %s
        ORDER BY s.due_date ASC
    """, (task_id,))
    subtasks = cursor.fetchall()

    # Fetch updates with user names
    cursor.execute("""
        SELECT tu.*, CONCAT(u.first_name, ' ', u.last_name) AS user_name
        FROM task_updates tu
        LEFT JOIN auth_users u ON tu.user_id = u.id
        WHERE tu.task_id = %s
        ORDER BY tu.update_date DESC
    """, (task_id,))
    updates = cursor.fetchall()

    return render_template(
        "task_detail.html",
        task=task,
        subtasks=subtasks,
        updates=updates
    )

### EDIT TASK ROUTE ###
@task_bp.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch the task
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()

    # Fetch all auth_users for dropdowns (owner and assigned_id)
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        status = request.form["status"]
        area = request.form.get("area")
        type_ = request.form.get("type")
        start_date = request.form.get("start_date")
        due_date = request.form.get("due_date")
        priority = request.form.get("priority")
        ticket_number = request.form.get("ticket_number")
        mantis_number = request.form.get("mantis_number")
        owner_id = request.form.get("owner_id")
        assigned_id = request.form.get("assigned_id")   # renamed field

        # Basic validation
        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("task.edit_task", task_id=task_id))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("task.edit_task", task_id=task_id))

        try:
            cursor.execute(
                """UPDATE tasks 
                   SET title=%s, description=%s, status=%s, area=%s, type=%s, 
                       start_date=%s, due_date=%s, priority=%s, 
                       ticket_number=%s, mantis_number=%s, owner_id=%s, assigned_id=%s
                   WHERE task_id=%s""",
                (title, description, status, area, type_, start_date, due_date, priority,
                 ticket_number, mantis_number, owner_id, assigned_id, task_id)
            )
            conn.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for("task.task_detail", task_id=task_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating task: {e}", "danger")
            return redirect(url_for("task.edit_task", task_id=task_id))

    return render_template("edit_task.html", task=task, users=users, VALID_STATUSES=VALID_STATUSES)

### DELETE TASK ROUTE ###
@task_bp.route("/task/<int:task_id>/delete", methods=["GET", "POST"])
@login_required
def delete_task(task_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()
    if not task:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            cursor.execute("DELETE FROM task_updates WHERE task_id=%s", (task_id,))
            cursor.execute("DELETE FROM task_status_history WHERE task_id=%s", (task_id,))
            cursor.execute("DELETE FROM subtasks WHERE parent_task_id=%s", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE task_id=%s", (task_id,))
            conn.commit()
            flash("Task deleted successfully!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            conn.rollback()
            flash(f"Error deleting task: {e}", "danger")
            return redirect(url_for("task.task_detail", task_id=task_id))

    return render_template("confirm_delete_task.html", task=task)

### ADD TASK UPDATE ###
@task_bp.route("/task/<int:task_id>/add_update", methods=["GET", "POST"])
@login_required
def add_task_update(task_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch the parent task
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()

    # Fetch all auth_users for dropdown
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        update_text = request.form["update_text"]
        update_date = request.form["update_date"]
        user_id = request.form.get("user_id")

        if not update_text or not update_date or not user_id:
            flash("Update text, date, and user are required!", "danger")
            return redirect(url_for("add_update", task_id=task_id))

        try:
            cursor.execute(
                """INSERT INTO task_updates (task_id, update_date, update_text, user_id) 
                   VALUES (%s, %s, %s, %s)""",
                (task_id, update_date, update_text, user_id)
            )
            conn.commit()
            flash("Update added successfully!", "success")
            return redirect(url_for("task.task_detail", task_id=task_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding update: {e}", "danger")
            return redirect(url_for("task.add_update", task_id=task_id))

    return render_template("add_update.html", users=users, task_id=task_id)