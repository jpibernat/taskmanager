from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user,  current_user
from flask_bcrypt import Bcrypt
from models import AuthUser
from functools import wraps
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

# Store shared objects in app.config 
app.config["DB_CONN"] = conn 
app.config["DB_CURSOR"] = cursor

bcrypt = Bcrypt(app)
app.config["BCRYPT"] = bcrypt

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader 
def load_user(user_id): 
    cur = app.config["DB_CURSOR"] 
    cur.execute("SELECT id, email, first_name, last_name, role FROM auth_users WHERE id=%s", (user_id,)) 
    row = cur.fetchone() 
    if row: 
        return AuthUser(row["id"], row["email"], row["first_name"], row["last_name"], row["role"]) 
    return None

# Register blueprints 
from auth_routes import auth_bp
from task_routes import task_bp
from subtask_routes import subtask_bp
from updates_routes import updates_bp
app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(subtask_bp)
app.register_blueprint(updates_bp)
# Valid statuses
VALID_STATUSES = ["Not started", "In progress", "Stuck", "Planned", "Hypercare", "Development", "Done"]
app.config["VALID_STATUSES"] = VALID_STATUSES

###################
### INDEX ROUTE ###
###################

@app.route("/")
@login_required
def index():
    # Collect filters/search inputs
    status = request.args.get("status")
    priority = request.args.get("priority")
    type_ = request.args.get("type")
    title_search = request.args.get("title_search")
    area_search = request.args.get("area_search")
    ticket_search = request.args.get("ticket_search")
    mantis_search = request.args.get("mantis_search")
    owner_search = request.args.get("owner_search")
    assigned_search = request.args.get("assigned_search")
    sort = request.args.get("sort", "due_date")  # default sort
    order = request.args.get("order", "asc")     # default ascending

    # Base query
    query = """
    SELECT t.task_id, t.title, t.status, t.priority, t.due_date,
           CONCAT(o.first_name, ' ', o.last_name) AS owner_name,
           CONCAT(a.first_name, ' ', a.last_name) AS assigned_name
    FROM tasks t
    LEFT JOIN auth_users o ON t.owner_id = o.id
    LEFT JOIN auth_users a ON t.assigned_id = a.id
    WHERE 1=1
    """
    params = []

    # Apply filters
    if status:
        query += " AND t.status = %s"
        params.append(status)
    if priority:
        query += " AND t.priority = %s"
        params.append(priority)
    if type_:
        query += " AND t.type = %s"
        params.append(type_)

    # Apply per-column searches
    if title_search:
        query += " AND t.title LIKE %s"
        params.append(f"%{title_search}%")
    if area_search:
        query += " AND t.area LIKE %s"
        params.append(f"%{area_search}%")
    if ticket_search:
        query += " AND t.ticket_number LIKE %s"
        params.append(f"%{ticket_search}%")
    if mantis_search:
        query += " AND t.mantis_number LIKE %s"
        params.append(f"%{mantis_search}%")
    if owner_search:
        query += " AND CONCAT(o.first_name, ' ', o.last_name) LIKE %s"
        params.append(f"%{owner_search}%")
    if assigned_search:
        query += " AND CONCAT(a.first_name, ' ', a.last_name) LIKE %s"
        params.append(f"%{assigned_search}%")

    # Sorting
    allowed_sorts = {
        "due_date": "t.due_date",
        "start_date": "t.start_date",
        "priority": "t.priority",
        "status": "t.status",
        "type": "t.type",
        "title": "t.title",
        "area": "t.area",
        "ticket_number": "t.ticket_number",
        "mantis_number": "t.mantis_number",
        "owner": "owner_name",
        "assigned": "assigned_name"
    }
    sort_column = allowed_sorts.get(sort, "t.due_date")
    order_sql = "ASC" if order.lower() == "asc" else "DESC"

    query += f" ORDER BY {sort_column} {order_sql}"

    cursor.execute(query, tuple(params))
    tasks = cursor.fetchall()

    return render_template("index.html", tasks=tasks)

######################################################
### MANAGING NON SYSTEM USERS (NEEDS TO BE REVIEWED###
######################################################
@app.route("/add_user", methods=["GET", "POST"])
@login_required
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
@login_required
def users_list():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template("users.html", users=users)

@app.route("/user/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
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
@login_required
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
#######################################
### END NON SYSTEM USERS MANAGEMENT ###
#######################################

############################################################################


@app.route("/task/<int:task_id>/add_update", methods=["GET", "POST"])
@login_required
def add_update(task_id):
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
            return redirect(url_for("task_detail", task_id=task_id))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding update: {e}", "danger")
            return redirect(url_for("add_update", task_id=task_id))

    return render_template("add_update.html", users=users, task_id=task_id)



if __name__ == "__main__":
    app.run(debug=True)
