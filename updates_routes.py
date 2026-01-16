from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app 
from flask_login import login_required 

updates_bp = Blueprint("updates", __name__) 

def get_db(): 
    conn = current_app.config["DB_CONN"] 
    cursor = current_app.config["DB_CURSOR"] 
    return conn, cursor

@updates_bp.route("/update/<int:update_id>/edit", methods=["GET", "POST"])
@login_required
def edit_update(update_id):
    conn, cursor = get_db()

    # Fetch update with assigned user full name
    cursor.execute("""
        SELECT tu.*, CONCAT(u.first_name, ' ', u.last_name) AS user_name
        FROM task_updates tu
        LEFT JOIN auth_users u ON tu.user_id = u.id
        WHERE tu.update_id = %s
    """, (update_id,))
    update = cursor.fetchone()

    if not update:
        flash("Update not found!", "danger")
        return redirect(url_for("index"))

    # Fetch all auth_users for dropdown
    cursor.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM auth_users")
    users = cursor.fetchall()

    if request.method == "POST":
        update_text = request.form["update_text"]
        update_date = request.form["update_date"]
        user_id = request.form.get("user_id")

        if not update_text or not update_date or not user_id:
            flash("Update text, date, and user are required!", "danger")
            return redirect(url_for("edit_update", update_id=update_id))

        try:
            cursor.execute(
                """UPDATE task_updates 
                   SET update_text=%s, update_date=%s, user_id=%s 
                   WHERE update_id=%s""",
                (update_text, update_date, int(user_id), update_id)
            )
            conn.commit()
            flash("Update edited successfully!", "success")

            # Redirect back to task or subtask detail depending on context
            if update["task_id"]:
                return redirect(url_for("task.task_detail", task_id=update["task_id"]))
            else:
                return redirect(url_for("subtask.subtask_detail", subtask_id=update["subtask_id"]))
        except Exception as e:
            conn.rollback()
            flash(f"Error editing update: {e}", "danger")
            return redirect(url_for("updates.edit_update", update_id=update_id))

    return render_template("edit_update.html", update=update, users=users)


@updates_bp.route("/update/<int:update_id>/delete", methods=["GET", "POST"])
@login_required
def delete_update(update_id):
    conn, cursor = get_db()

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
            return redirect(url_for("task.task_detail", task_id=update["task_id"]))
        else:
            return redirect(url_for("subtask.subtask_detail", subtask_id=update["subtask_id"]))

    return render_template("confirm_delete_update.html", update=update)