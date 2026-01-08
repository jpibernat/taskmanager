from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "your_secret_key"  # required for flash messages

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Marc0s.2o2%+",
    database="topics"
)
cursor = conn.cursor(dictionary=True)

# Valid statuses
VALID_STATUSES = ["Not started", "In progress", "Stuck", "Planned", "Hypercare", "Development", "Done"]

@app.route("/")
def index():
    # Fetch tasks with owner and assigned user names
    cursor.execute("""
        SELECT t.*, 
               u1.username AS owner_name, 
               u2.username AS assigned_name
        FROM tasks t
        LEFT JOIN users u1 ON t.owner_id = u1.user_id
        LEFT JOIN users u2 ON t.assigned_to = u2.user_id
        ORDER BY t.due_date ASC
    """)
    tasks = cursor.fetchall()

    return render_template("index.html", tasks=tasks)


@app.route("/task/<int:task_id>")
def task_detail(task_id):
    # Fetch the task with owner and assigned user names
    cursor.execute("""
        SELECT t.*, 
               u1.username AS owner_name, 
               u2.username AS assigned_name
        FROM tasks t
        LEFT JOIN users u1 ON t.owner_id = u1.user_id
        LEFT JOIN users u2 ON t.assigned_to = u2.user_id
        WHERE t.task_id = %s
    """, (task_id,))
    task = cursor.fetchone()

    if not task:
        flash("Task not found!", "danger")
        return redirect(url_for("index"))

    # Fetch subtasks with assigned user names
    cursor.execute("""
        SELECT s.*, u.username AS assigned_name
        FROM subtasks s
        LEFT JOIN users u ON s.assigned_to = u.user_id
        WHERE s.parent_task_id = %s
        ORDER BY s.due_date ASC
    """, (task_id,))
    subtasks = cursor.fetchall()

    # Fetch updates with user names
    cursor.execute("""
        SELECT tu.*, u.username 
        FROM task_updates tu
        LEFT JOIN users u ON tu.user_id = u.user_id
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

@app.route("/subtask/<int:subtask_id>")
def subtask_detail(subtask_id):
    # Fetch the subtask with assigned user name
    cursor.execute("""
        SELECT s.*, u.username AS assigned_name
        FROM subtasks s
        LEFT JOIN users u ON s.assigned_to = u.user_id
        WHERE s.subtask_id = %s
    """, (subtask_id,))
    subtask = cursor.fetchone()

    if not subtask:
        flash("Subtask not found!", "danger")
        return redirect(url_for("index"))

    # Fetch updates for this subtask
    cursor.execute("""
        SELECT tu.*, u.username 
        FROM task_updates tu
        LEFT JOIN users u ON tu.user_id = u.user_id
        WHERE tu.subtask_id = %s
        ORDER BY tu.update_date DESC
    """, (subtask_id,))
    updates = cursor.fetchall()

    return render_template("subtask_detail.html", subtask=subtask, updates=updates)


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        role = request.form["role"]

        if not username or not email or not role:
            flash("All fields are required!", "danger")
            return redirect(url_for("add_user"))

        try:
            cursor.execute(
                "INSERT INTO users (username, email, role) VALUES (%s, %s, %s)",
                (username, email, role)
            )
            conn.commit()
            flash("User created successfully!", "success")
            return redirect(url_for("add_task"))  # back to task creation
        except Exception as e:
            conn.rollback()
            flash(f"Error creating user: {e}", "danger")
            return redirect(url_for("add_user"))

    return render_template("add_user.html")

@app.route("/users")
def users_list():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template("users.html", users=users)

@app.route("/user/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        role = request.form["role"]

        if not username or not email or not role:
            flash("All fields are required!", "danger")
            return redirect(url_for("edit_user", user_id=user_id))

        cursor.execute(
            "UPDATE users SET username=%s, email=%s, role=%s WHERE user_id=%s",
            (username, email, role, user_id)
        )
        conn.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("users_list"))

    return render_template("edit_user.html", user=user)

@app.route("/user/<int:user_id>/delete", methods=["GET", "POST"])
def delete_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return redirect(url_for("users_list"))

    if request.method == "POST":
        cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
        conn.commit()
        flash("User deleted successfully!", "success")
        return redirect(url_for("users_list"))

    return render_template("confirm_delete_user.html", user=user)


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    # Fetch all users for dropdowns (owner and assigned_to)
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        status = request.form["status"]
        area = request.form.get("area")
        type_ = request.form.get("type")
        start_date = request.form.get("start_date")
        due_date = request.form.get("due_date")
        priority = request.form.get("priority")
        ticket_number = request.form.get("ticket_number")
        mantis_number = request.form.get("mantis_number")
        owner_id = request.form.get("owner_id")
        assigned_to = request.form.get("assigned_to")

        # Basic validation
        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("add_task"))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("add_task"))

        try:
            cursor.execute(
                """INSERT INTO tasks 
                   (title, description, status, area, type, start_date, due_date, priority, 
                    ticket_number, mantis_number, owner_id, assigned_to) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (title, description, status, area, type_, start_date, due_date, priority,
                 ticket_number, mantis_number, owner_id, assigned_to)
            )
            conn.commit()
            flash("Task added successfully!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding task: {e}", "danger")
            return redirect(url_for("add_task"))

    return render_template("add_task.html", users=users, VALID_STATUSES=VALID_STATUSES)


@app.route("/task/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    # Fetch the task
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()

    # Fetch all users for dropdowns (owner and assigned_to)
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        status = request.form["status"]
        area = request.form.get("area")
        type_ = request.form.get("type")
        start_date = request.form.get("start_date")
        due_date = request.form.get("due_date")
        priority = request.form.get("priority")
        ticket_number = request.form.get("ticket_number")
        mantis_number = request.form.get("mantis_number")
        owner_id = request.form.get("owner_id")
        assigned_to = request.form.get("assigned_to")

        # Basic validation
        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        try:
            cursor.execute(
                """UPDATE tasks 
                   SET title=%s, description=%s, status=%s, area=%s, type=%s, 
                       start_date=%s, due_date=%s, priority=%s, 
                       ticket_number=%s, mantis_number=%s, owner_id=%s, assigned_to=%s
                   WHERE task_id=%s""",
                (title, description, status, area, type_, start_date, due_date, priority,
                 ticket_number, mantis_number, owner_id, assigned_to, task_id)
            )
            conn.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for("task_detail", task_id=task_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating task: {e}", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

    return render_template("edit_task.html", task=task, users=users, VALID_STATUSES=VALID_STATUSES)

@app.route("/task/<int:task_id>/add_update", methods=["GET", "POST"])
def add_task_update(task_id):
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if request.method == "POST":
        update_text = request.form["update_text"]
        update_date = request.form["update_date"]
        user_id = request.form.get("user_id")

        if not update_text or not update_date:
            flash("Update text and date are required!", "danger")
            return redirect(url_for("add_task_update", task_id=task_id))

        cursor.execute(
            "INSERT INTO task_updates (task_id, update_date, update_text, user_id) VALUES (%s, %s, %s, %s)",
            (task_id, update_date, update_text, user_id)
        )
        conn.commit()
        flash("Update added successfully!", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    return render_template("add_update.html", users=users, task_id=task_id)

@app.route("/update/<int:update_id>/edit", methods=["GET", "POST"])
def edit_update(update_id):
    # Fetch update
    cursor.execute("""
        SELECT tu.*, u.username 
        FROM task_updates tu
        LEFT JOIN users u ON tu.user_id = u.user_id
        WHERE tu.update_id = %s
    """, (update_id,))
    update = cursor.fetchone()

    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if not update:
        flash("Update not found!", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        update_text = request.form["update_text"]
        update_date = request.form["update_date"]
        user_id = request.form.get("user_id")

        if not update_text or not update_date:
            flash("Update text and date are required!", "danger")
            return redirect(url_for("edit_update", update_id=update_id))

        cursor.execute(
            "UPDATE task_updates SET update_text=%s, update_date=%s, user_id=%s WHERE update_id=%s",
            (update_text, update_date, user_id, update_id)
        )
        conn.commit()
        flash("Update edited successfully!", "success")

        # Redirect back to task or subtask detail depending on context
        if update["task_id"]:
            return redirect(url_for("task_detail", task_id=update["task_id"]))
        else:
            return redirect(url_for("subtask_detail", subtask_id=update["subtask_id"]))

    return render_template("edit_update.html", update=update, users=users)

@app.route("/update/<int:update_id>/delete", methods=["GET", "POST"])
def delete_update(update_id):
    cursor.execute("SELECT * FROM task_updates WHERE update_id=%s", (update_id,))
    update = cursor.fetchone()

    if not update:
        flash("Update not found!", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        cursor.execute("DELETE FROM task_updates WHERE update_id=%s", (update_id,))
        conn.commit()
        flash("Update deleted successfully!", "success")

        if update["task_id"]:
            return redirect(url_for("task_detail", task_id=update["task_id"]))
        else:
            return redirect(url_for("subtask_detail", subtask_id=update["subtask_id"]))

    return render_template("confirm_delete_update.html", update=update)


@app.route("/task/<int:task_id>/delete", methods=["GET", "POST"])
def delete_task(task_id):
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
            return redirect(url_for("task_detail", task_id=task_id))

    return render_template("confirm_delete_task.html", task=task)

@app.route("/task/<int:task_id>/add_subtask", methods=["GET", "POST"])
def add_subtask(task_id):
    # Fetch the parent task
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()

    # Fetch all users for dropdown
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        status = request.form["status"]
        due_date = request.form["due_date"]
        priority = request.form.get("priority")
        assigned_to = request.form.get("assigned_to")

        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("add_subtask", task_id=task_id))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("add_subtask", task_id=task_id))

        cursor.execute(
            "INSERT INTO subtasks (parent_task_id, title, description, status, due_date, priority, assigned_to) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (task_id, title, description, status, due_date, priority, assigned_to)
        )
        conn.commit()
        flash("Subtask added successfully!", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    return render_template(
        "add_subtask.html",
        task=task,
        users=users,
        VALID_STATUSES=VALID_STATUSES
    )



@app.route("/subtask/<int:subtask_id>/edit", methods=["GET", "POST"])
def edit_subtask(subtask_id):
    # Fetch the subtask
    cursor.execute("SELECT * FROM subtasks WHERE subtask_id=%s", (subtask_id,))
    subtask = cursor.fetchone()

    # 🔑 Fetch all users for dropdown
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        status = request.form["status"]
        due_date = request.form["due_date"]
        priority = request.form.get("priority")
        assigned_to = request.form.get("assigned_to")

        if not title or not status:
            flash("Title and Status are required!", "danger")
            return redirect(url_for("edit_subtask", subtask_id=subtask_id))

        if status not in VALID_STATUSES:
            flash("Invalid status selected!", "danger")
            return redirect(url_for("edit_subtask", subtask_id=subtask_id))

        cursor.execute(
            "UPDATE subtasks SET title=%s, description=%s, status=%s, due_date=%s, priority=%s, assigned_to=%s "
            "WHERE subtask_id=%s",
            (title, description, status, due_date, priority, assigned_to, subtask_id)
        )
        conn.commit()
        flash("Subtask updated successfully!", "success")
        return redirect(url_for("task_detail", task_id=subtask["parent_task_id"]))

    # ✅ Now users is defined and passed to the template
    return render_template(
        "edit_subtask.html",
        subtask=subtask,
        users=users,
        VALID_STATUSES=VALID_STATUSES
    )

@app.route("/subtask/<int:subtask_id>/add_update", methods=["GET", "POST"])
def add_subtask_update(subtask_id):
    # Fetch users for dropdown
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()

    if request.method == "POST":
        update_text = request.form["update_text"]
        update_date = request.form["update_date"]
        user_id = request.form.get("user_id")

        if not update_text or not update_date:
            flash("Update text and date are required!", "danger")
            return redirect(url_for("add_subtask_update", subtask_id=subtask_id))

        try:
            cursor.execute(
                "INSERT INTO task_updates (subtask_id, update_date, update_text, user_id) VALUES (%s, %s, %s, %s)",
                (subtask_id, update_date, update_text, user_id)
            )
            conn.commit()
            flash("Update added successfully!", "success")
            return redirect(url_for("subtask_detail", subtask_id=subtask_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding update: {e}", "danger")
            return redirect(url_for("add_subtask_update", subtask_id=subtask_id))

    return render_template("add_update.html", users=users, subtask_id=subtask_id)



@app.route("/subtask/<int:subtask_id>/delete", methods=["GET", "POST"])
def delete_subtask(subtask_id):
    cursor.execute("SELECT * FROM subtasks WHERE subtask_id=%s", (subtask_id,))
    subtask = cursor.fetchone()
    if not subtask:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            cursor.execute("DELETE FROM subtasks WHERE subtask_id=%s", (subtask_id,))
            conn.commit()
            flash("Subtask deleted successfully!", "success")
            return redirect(url_for("task_detail", task_id=subtask["parent_task_id"]))
        except Exception as e:
            conn.rollback()
            flash(f"Error deleting subtask: {e}", "danger")
            return redirect(url_for("task_detail", task_id=subtask["parent_task_id"]))

    return render_template("confirm_delete_subtask.html", subtask=subtask)

@app.route("/task/<int:task_id>/add_update", methods=["GET", "POST"])
def add_update(task_id):
    cursor.execute("SELECT * FROM tasks WHERE task_id=%s", (task_id,))
    task = cursor.fetchone()

    if request.method == "POST":
        username = request.form["username"]
        comment = request.form["comment"]

        if not username or not comment:
            flash("Username and Comment are required!", "danger")
            return redirect(url_for("add_update", task_id=task_id))

        cursor.execute(
            "INSERT INTO task_updates (task_id, username, comment, update_date) VALUES (%s, %s, %s, NOW())",
            (task_id, username, comment)
        )
        conn.commit()
        flash("Update added successfully!", "success")
        return redirect(url_for("task_detail", task_id=task_id))

    return render_template("add_update.html", task=task)


#@app.route("/update/<int:update_id>/edit", methods=["GET", "POST"])
#def edit_update(update_id):
#    cursor.execute("SELECT * FROM task_updates WHERE update_id=%s", (update_id,))
#    update = cursor.fetchone()
#
#    if request.method == "POST":
#        username = request.form["username"]
#        comment = request.form["comment"]
#
#        if not username or not comment:
#            flash("Username and Comment are required!", "danger")
#            return redirect(url_for("edit_update", update_id=update_id))
#
#        cursor.execute(
#            "UPDATE task_updates SET username=%s, comment=%s WHERE update_id=%s",
#            (username, comment, update_id)
#        )
#        conn.commit()
#        flash("Update edited successfully!", "success")
#        return redirect(url_for("task_detail", task_id=update["task_id"]))
#
#    return render_template("edit_update.html", update=update)
#
#
#@app.route("/update/<int:update_id>/delete", methods=["GET", "POST"])
#def delete_update(update_id):
#    cursor.execute("SELECT * FROM task_updates WHERE update_id=%s", (update_id,))
#    update = cursor.fetchone()
#    if not update:
#        return redirect(url_for("index"))
#
#    if request.method == "POST":
#        try:
#            cursor.execute("DELETE FROM task_updates WHERE update_id=%s", (update_id,))
#            conn.commit()
#            flash("Update deleted successfully!", "success")
#            return redirect(url_for("task_detail", task_id=update["task_id"]))
#        except Exception as e:
#            conn.rollback()
#            flash(f"Error deleting update: {e}", "danger")
#            return redirect(url_for("task_detail", task_id=update["task_id"]))
#
#    return render_template("confirm_delete_update.html", update=update)


if __name__ == "__main__":
    app.run(debug=True)
