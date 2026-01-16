from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from models import AuthUser

subtask_bp = Blueprint("subtask", __name__)

def get_db():
    conn = current_app.config["DB_CONN"]
    cursor = current_app.config["DB_CURSOR"]
    return conn, cursor

def get_bcrypt():
    return current_app.config["BCRYPT"]

### ADD SUBTASK ROUTE ###
@subtask_bp.route("/task/<int:task_id>/add_subtask", methods=["GET", "POST"])
@login_required
def add_subtask(task_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]

    # Fetch the parent task
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()

    # Fetch all auth_users for dropdown
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        status = request.form["status"]
        due_date = request.form.get("due_date")
        priority = request.form.get("priority")
        assigned_id = request.form.get("assigned_id")   # renamed field

        # Basic validation
        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("add_subtask", task_id=task_id))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("add_subtask", task_id=task_id))

        try:
            cursor.execute(
                """INSERT INTO subtasks 
                   (parent_task_id, title, description, status, due_date, priority, assigned_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (task_id, title, description, status, due_date, priority, assigned_id)
            )
            conn.commit()
            flash("Subtask added successfully!", "success")
            return redirect(url_for("task.task_detail", task_id=task_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding subtask: {e}", "danger")
            return redirect(url_for("add_subtask", task_id=task_id))

    return render_template(
        "add_subtask.html",
        task=task,
        users=users,
        VALID_STATUSES=VALID_STATUSES
    )

### SUBTASK DETAIL ROUTE ###
@subtask_bp.route("/subtask/<int:subtask_id>")
def subtask_detail(subtask_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch the subtask with assigned user name
    cursor.execute("""
        SELECT s.*, CONCAT(u.first_name, ' ', u.last_name) AS assigned_name
        FROM subtasks s
        LEFT JOIN auth_users u ON s.assigned_id = u.id
        WHERE s.subtask_id = %s
    """, (subtask_id,))
    subtask = cursor.fetchone()

    if not subtask:
        flash("Subtask not found!", "danger")
        return redirect(url_for("index"))

    # Fetch updates for this subtask
    cursor.execute("""
        SELECT tu.*, CONCAT(u.first_name, ' ', u.last_name) AS user_name
        FROM task_updates tu
        LEFT JOIN auth_users u ON tu.user_id = u.id
        WHERE tu.subtask_id = %s
        ORDER BY tu.update_date DESC
    """, (subtask_id,))
    updates = cursor.fetchall()

    return render_template("subtask_detail.html", subtask=subtask, updates=updates)

### EDIT SUBTASK ###
@subtask_bp.route("/subtask/<int:subtask_id>/edit", methods=["GET", "POST"])
@login_required
def edit_subtask(subtask_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch the subtask
    cursor.execute("SELECT * FROM subtasks WHERE subtask_id=%s", (subtask_id,))
    subtask = cursor.fetchone()

    # Fetch all auth_users for dropdown
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        status = request.form["status"]
        due_date = request.form.get("due_date")
        priority = request.form.get("priority")
        assigned_id = request.form.get("assigned_id")   # renamed field

        # Basic validation
        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("edit_subtask", subtask_id=subtask_id))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("edit_subtask", subtask_id=subtask_id))

        try:
            cursor.execute(
                """UPDATE subtasks 
                   SET title=%s, description=%s, status=%s, due_date=%s, priority=%s, assigned_id=%s
                   WHERE subtask_id=%s""",
                (title, description, status, due_date, priority, assigned_id, subtask_id)
            )
            conn.commit()
            flash("Subtask updated successfully!", "success")
            return redirect(url_for("task.task_detail", task_id=subtask["parent_task_id"]))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating subtask: {e}", "danger")
            return redirect(url_for("edit_subtask", subtask_id=subtask_id))

    return render_template(
        "edit_subtask.html",
        subtask=subtask,
        users=users,
        VALID_STATUSES=VALID_STATUSES
    )


### DELETE SUBTASK ROUTE ###
@subtask_bp.route("/subtask/<int:subtask_id>/delete", methods=["GET", "POST"])
@login_required
def delete_subtask(subtask_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    cursor.execute("SELECT * FROM subtasks WHERE subtask_id=%s", (subtask_id,))
    subtask = cursor.fetchone()
    if not subtask:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            cursor.execute("DELETE FROM subtasks WHERE subtask_id=%s", (subtask_id,))
            conn.commit()
            flash("Subtask deleted successfully!", "success")
            return redirect(url_for("task.task_detail", task_id=subtask["parent_task_id"]))
        except Exception as e:
            conn.rollback()
            flash(f"Error deleting subtask: {e}", "danger")
            return redirect(url_for("task.task_detail", task_id=subtask["parent_task_id"]))

    return render_template("confirm_delete_subtask.html", subtask=subtask)

### ADD SUBTASK UPDATES ###
@subtask_bp.route("/subtask/<int:subtask_id>/add_update", methods=["GET", "POST"])
@login_required
def add_subtask_update(subtask_id):
    conn, cursor = get_db()
    VALID_STATUSES = current_app.config["VALID_STATUSES"]
    # Fetch all auth_users for dropdown
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        update_text = request.form["update_text"]
        update_date = request.form["update_date"]
        user_id = request.form.get("user_id")   # still valid, but now references auth_users.id

        # Basic validation
        if not update_text or not update_date:
            flash("Update text and date are required!", "danger")
            return redirect(url_for("subtask.add_subtask_update", subtask_id=subtask_id))

        try:
            cursor.execute(
                """INSERT INTO task_updates (subtask_id, update_date, update_text, user_id) 
                   VALUES (%s, %s, %s, %s)""",
                (subtask_id, update_date, update_text, user_id)
            )
            conn.commit()
            flash("Update added successfully!", "success")
            return redirect(url_for("subtask.subtask_detail", subtask_id=subtask_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding update: {e}", "danger")
            return redirect(url_for("subtask.add_subtask_update", subtask_id=subtask_id))

    return render_template("add_update.html", users=users, subtask_id=subtask_id)