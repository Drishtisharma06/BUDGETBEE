from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import io
import csv
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "change_this_to_a_secure_key"
app.config["DATABASE"] = os.path.join(os.path.dirname(__file__), "expense_tracker.db")

CATEGORIES = ["Food", "Shopping", "Bills", "Entertainment", "Travel", "Health", "Others"]
PAYMENT_METHODS = ["Cash", "Card", "UPI", "Bank Transfer", "Wallet"]


def get_db_connection():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            profile_image TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month_year TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            savings_target REAL DEFAULT 0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month_year TEXT NOT NULL,
            total_expenses REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    conn.commit()
    conn.close()


def setup_database():
    init_db()

setup_database()


def login_required(view):
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped.__name__ = view.__name__
    return wrapped


def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user


@app.route("/")
def index():
    user = get_current_user()
    return render_template("index.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, 0)",
                (username, email, hashed_password),
            )
            conn.commit()
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email is already registered. Please use a different email.", "danger")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    conn = get_db_connection()
    expenses = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 5", (user["id"],)
    ).fetchall()
    total_expenses = conn.execute(
        "SELECT IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()["total"]
    category_summary = conn.execute(
        "SELECT category, IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? GROUP BY category",
        (user["id"],),
    ).fetchall()
    budget = conn.execute(
        "SELECT * FROM budgets WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
        (user["id"],),
    ).fetchone()
    conn.close()

    budget_limit = budget["limit_amount"] if budget else 0
    remaining_budget = max(0, budget_limit - total_expenses) if budget_limit else 0
    budget_usage = int(min(100, (total_expenses / budget_limit) * 100)) if budget_limit else 0

    return render_template(
        "dashboard.html",
        user=user,
        expenses=expenses,
        total_expenses=total_expenses,
        category_summary=category_summary,
        budget=budget,
        remaining_budget=remaining_budget,
        budget_usage=budget_usage,
    )


@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    user = get_current_user()
    if request.method == "POST":
        amount = request.form.get("amount", type=float)
        category = request.form.get("category")
        date_value = request.form.get("date")
        payment_method = request.form.get("payment_method")
        notes = request.form.get("notes", "").strip()

        if not amount or not category or not date_value or not payment_method:
            flash("Please complete all required fields.", "danger")
            return redirect(url_for("add_expense"))

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, payment_method, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["id"], amount, category, date_value, payment_method, notes, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        flash("Expense added successfully.", "success")
        return redirect(url_for("expenses"))

    return render_template(
        "add_expense.html",
        user=user,
        categories=CATEGORIES,
        payment_methods=PAYMENT_METHODS,
        today=datetime.utcnow().strftime("%Y-%m-%d"),
    )


@app.route("/expenses")
@login_required
def expenses():
    user = get_current_user()
    search = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "")
    month_filter = request.args.get("month", "")
    sort_by = request.args.get("sort", "date_desc")

    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user["id"]]

    if search:
        # match search across notes, category, payment_method, date, and amount (as text)
        query += " AND (LOWER(notes) LIKE LOWER(?) OR LOWER(category) LIKE LOWER(?) OR LOWER(payment_method) LIKE LOWER(?) OR date LIKE ? OR CAST(amount AS TEXT) LIKE ?)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term, like_term, like_term])
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    if month_filter:
        query += " AND strftime('%Y-%m', date) = ?"
        params.append(month_filter)

    if sort_by == "amount_asc":
        query += " ORDER BY amount ASC"
    elif sort_by == "amount_desc":
        query += " ORDER BY amount DESC"
    else:
        query += " ORDER BY date DESC"

    conn = get_db_connection()
    expenses = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    return render_template(
        "expenses.html",
        user=user,
        expenses=expenses,
        categories=CATEGORIES,
        filters={"search": search, "category": category_filter, "month": month_filter, "sort": sort_by},
    )


@app.route("/analytics")
@login_required
def analytics():
    user = get_current_user()
    conn = get_db_connection()
    monthly_data = conn.execute(
        "SELECT strftime('%Y-%m', date) AS month, IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? GROUP BY month ORDER BY month ASC",
        (user["id"],),
    ).fetchall()
    category_data = conn.execute(
        "SELECT category, IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? GROUP BY category",
        (user["id"],),
    ).fetchall()
    total_expenses = conn.execute(
        "SELECT IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()["total"]
    conn.close()

    return render_template(
        "analytics.html",
        user=user,
        monthly_data=monthly_data,
        category_data=category_data,
        total_expenses=total_expenses,
    )


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    user = get_current_user()
    conn = get_db_connection()
    current_budget = conn.execute(
        "SELECT * FROM budgets WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
        (user["id"],),
    ).fetchone()

    total_expenses = conn.execute(
        "SELECT IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()["total"]

    # fetch recent budget history and monthly snapshots
    budget_history = conn.execute(
        "SELECT month_year, limit_amount, savings_target, updated_at FROM budgets WHERE user_id = ? ORDER BY updated_at DESC LIMIT 12",
        (user["id"],),
    ).fetchall()
    monthly_history = conn.execute(
        "SELECT month_year, total_expenses, created_at FROM monthly_history WHERE user_id = ? ORDER BY month_year DESC LIMIT 24",
        (user["id"],),
    ).fetchall()

    if request.method == "POST":
        # snapshot current month
        if request.form.get("snapshot"):
            month_year = datetime.utcnow().strftime("%Y-%m")
            conn.execute(
                "INSERT INTO monthly_history (user_id, month_year, total_expenses, created_at) VALUES (?, ?, ?, ?)",
                (user["id"], month_year, total_expenses, datetime.utcnow().isoformat()),
            )
            conn.commit()
            flash("Monthly snapshot saved.", "success")
            conn.close()
            return redirect(url_for("budget"))

        # update budget
        limit_amount = request.form.get("limit_amount", type=float)
        savings_target = request.form.get("savings_target", type=float)

        if limit_amount is None:
            flash("Enter a valid budget limit.", "danger")
            return redirect(url_for("budget"))

        conn.execute(
            "INSERT INTO budgets (user_id, month_year, limit_amount, savings_target, updated_at) VALUES (?, ?, ?, ?, ?)",
            (
                user["id"],
                datetime.utcnow().strftime("%Y-%m"),
                limit_amount,
                savings_target or 0,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        flash("Budget updated successfully.", "success")
        conn.close()
        return redirect(url_for("budget"))

    conn.close()

    if current_budget:
        remaining = max(0, current_budget["limit_amount"] - total_expenses)
        usage = int(min(100, (total_expenses / current_budget["limit_amount"]) * 100)) if current_budget["limit_amount"] else 0
    else:
        remaining = 0
        usage = 0

    return render_template(
        "budget.html",
        user=user,
        budget=current_budget,
        total_expenses=total_expenses,
        remaining=remaining,
        usage=usage,
        budget_history=budget_history,
        monthly_history=monthly_history,
    )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = get_current_user()
    conn = get_db_connection()
    budgets_count = conn.execute("SELECT COUNT(*) as cnt FROM budgets WHERE user_id = ?", (user["id"],)).fetchone()["cnt"]
    conn.close()

    if request.method == "POST":
        username = request.form.get("username", user["username"]).strip()
        password = request.form.get("password")
        if username:
            conn = get_db_connection()
            if password:
                conn.execute(
                    "UPDATE users SET username = ?, password = ? WHERE id = ?",
                    (username, generate_password_hash(password), user["id"]),
                )
            else:
                conn.execute(
                    "UPDATE users SET username = ? WHERE id = ?",
                    (username, user["id"]),
                )
            conn.commit()
            conn.close()
            session["username"] = username
            flash("Profile updated successfully.", "success")
            return redirect(url_for("profile"))

    return render_template("profile.html", user=user, budgets_count=budgets_count)


@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    user = get_current_user()
    conn = get_db_connection()
    expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not expense:
        conn.close()
        flash("Expense not found.", "danger")
        return redirect(url_for('expenses'))
    if expense['user_id'] != user['id']:
        conn.close()
        flash('You are not authorized to delete this expense.', 'danger')
        return redirect(url_for('expenses'))
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    flash('Expense deleted successfully.', 'success')
    return redirect(url_for('expenses'))


@app.route("/reports")
@login_required
def reports():
    user = get_current_user()
    conn = get_db_connection()
    total_expenses = conn.execute(
        "SELECT IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()["total"]
    category_summary = conn.execute(
        "SELECT category, IFNULL(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 5",
        (user["id"],),
    ).fetchall()
    highest_category = category_summary[0]["category"] if category_summary else "N/A"
    conn.close()
    return render_template(
        "reports.html",
        user=user,
        total_expenses=total_expenses,
        category_summary=category_summary,
        highest_category=highest_category,
    )


@app.route("/export-csv")
@login_required
def export_csv():
    user = get_current_user()
    conn = get_db_connection()
    expenses = conn.execute(
        "SELECT date, category, payment_method, amount, notes FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (user["id"],),
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Category", "Payment Method", "Amount", "Notes"])
    for expense in expenses:
        writer.writerow([expense["date"], expense["category"], expense["payment_method"], expense["amount"], expense["notes"]])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        download_name="expenses_report.csv",
        as_attachment=True,
    )


@app.route("/notifications")
@login_required
def notifications():
    user = get_current_user()
    alerts = [
        {"title": "Budget update available", "message": "Set a new monthly budget to stay on track.", "type": "info"},
        {"title": "High spending alert", "message": "Your Entertainment category is trending high this month.", "type": "warning"},
        {"title": "Report ready", "message": "Your monthly expense report is ready to download.", "type": "success"},
    ]
    return render_template("notifications.html", user=user, alerts=alerts)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = get_current_user()
    if request.method == "POST":
        flash("Settings saved successfully.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", user=user)


@app.route("/admin")
@login_required
def admin():
    user = get_current_user()
    if not user or not user["is_admin"]:
        flash("Admin access required.", "danger")
        return redirect(url_for("dashboard"))
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, email, is_admin FROM users ORDER BY username ASC").fetchall()
    expenses = conn.execute("SELECT * FROM expenses ORDER BY date DESC LIMIT 20").fetchall()
    conn.close()
    return render_template("admin.html", user=user, users=users, expenses=expenses)


if __name__ == "__main__":
    app.run(debug=True)
