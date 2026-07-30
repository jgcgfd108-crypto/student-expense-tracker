import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from models import init_db


app = Flask(__name__)

app.secret_key = "expense_tracker"


# ---------------- Database Connection ----------------

def get_db():

    conn = sqlite3.connect("database.db")

    conn.row_factory = sqlite3.Row

    return conn


# ---------------- Home ----------------

@app.route("/")
def home():

    return render_template("index.html")


# ---------------- Register ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users
                (username, email, password)
                VALUES (?, ?, ?)
                """,
                (username, email, password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return "Username or Email already exists"

    return render_template("register.html")


# ---------------- Login ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        else:

            return "Invalid Email or Password"

    return render_template("login.html")


# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    total_expense = conn.execute(
        """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()["total"]

    expense_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM expenses
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()["count"]

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_expense=total_expense or 0,
        expense_count=expense_count
    )



# ---------------- Add Expense ----------------

@app.route("/add_expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        category = request.form["category"]
        amount = request.form["amount"]
        date = request.form["date"]

        conn = get_db()

        conn.execute(
            """
            INSERT INTO expenses
            (description, amount, category, date, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                title,
                amount,
                category,
                date,
                session["user_id"]
            )
        )

        conn.commit()

        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")


# ---------------- View Expenses ----------------

@app.route("/view_expense")
def view_expense():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    expenses = conn.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "view_expense.html",
        expenses=expenses
    )
    # ---------------- Delete Expense ----------------

@app.route("/delete_expense/<int:expense_id>")
def delete_expense(expense_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM expenses
        WHERE id = ?
        AND user_id = ?
        """,
        (expense_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("view_expense"))
    # ---------------- Edit Expense ----------------

@app.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    expense = conn.execute(
        """
        SELECT *
        FROM expenses
        WHERE id = ?
        AND user_id = ?
        """,
        (expense_id, session["user_id"])
    ).fetchone()

    if not expense:
        conn.close()
        return "Expense not found"

    if request.method == "POST":

        title = request.form["title"]
        category = request.form["category"]
        amount = request.form["amount"]
        date = request.form["date"]

        conn.execute(
            """
            UPDATE expenses
            SET description = ?,
                category = ?,
                amount = ?,
                date = ?
            WHERE id = ?
            AND user_id = ?
            """,
            (
                title,
                category,
                amount,
                date,
                expense_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("view_expense"))

    conn.close()

    return render_template(
        "edit_expense.html",
        expense=expense
    )


# ---------------- Profile ----------------

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# ---------------- Logout ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ---------------- Run App ----------------

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)