from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

DB_PATH = Path("instance") / "expenses.db"

def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            ttype TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            merchant TEXT,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

transactions = []

@app.route("/")
def home():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions ORDER BY date DESC, id DESC"
    ).fetchall()

    total_income = 0.0
    total_expense = 0.0
    by_category = {}

    for r in rows:
        amt = float(r["amount"])
        if r["ttype"] == "income":
            total_income += amt
        else:
            total_expense += amt
            cat = r["category"]
            by_category[cat] = by_category.get(cat, 0.0) + amt

    conn.close()

    net = total_income - total_expense

    return render_template(
        "index.html",
        rows=rows,
        total_income=total_income,
        total_expense=total_expense,
        net=net,
        by_category=by_category
    )

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = request.form["date"].strip()
        ttype = request.form["ttype"].strip()
        amount = float(request.form["amount"])
        category = request.form["category"].strip()
        merchant = request.form.get("merchant", "").strip()
        note = request.form.get("note", "").strip()

        conn = get_db()
        conn.execute(
            """
            INSERT INTO transactions (date, ttype, amount, category, merchant, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (date, ttype, amount, category, merchant, note)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add.html")

@app.route("/months")
def months():
    conn = get_db()
    rows = conn.execute("""
        SELECT
            substr(date, 1, 7) AS yyyy_mm,
            COALESCE(SUM(CASE WHEN ttype='income' THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN ttype='expense' THEN amount ELSE 0 END), 0) AS expense
        FROM transactions
        GROUP BY substr(date, 1, 7)
        ORDER BY yyyy_mm DESC
    """).fetchall()
    conn.close()

    return render_template("months.html", rows=rows)


@app.route("/month/<yyyy_mm>")
def month_view(yyyy_mm):
    year, month = map(int, yyyy_mm.split("-"))
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year+1:04d}-01-01"
    else:
        end = f"{year:04d}-{month+1:02d}-01"

    conn = get_db()

    tx = conn.execute("""
        SELECT * FROM transactions
        WHERE date >= ? AND date < ?
        ORDER BY date DESC, id DESC
    """, (start, end)).fetchall()

    total_income = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) AS s
        FROM transactions
        WHERE date >= ? AND date < ? AND ttype='income'
    """, (start, end)).fetchone()["s"]

    total_expense = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) AS s
        FROM transactions
        WHERE date >= ? AND date < ? AND ttype='expense'
    """, (start, end)).fetchone()["s"]

    by_category_rows = conn.execute("""
        SELECT category, COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE date >= ? AND date < ? AND ttype='expense'
        GROUP BY category
        ORDER BY total DESC
    """, (start, end)).fetchall()

    conn.close()

    net = float(total_income) - float(total_expense)

    # prev/next month links
    if month == 1:
        prev_month = f"{year-1:04d}-12"
    else:
        prev_month = f"{year:04d}-{month-1:02d}"

    if month == 12:
        next_month = f"{year+1:04d}-01"
    else:
        next_month = f"{year:04d}-{month+1:02d}"

    # chart data (optional, for later)
    chart_labels = [r["category"] for r in by_category_rows]
    chart_values = [float(r["total"]) for r in by_category_rows]

    return render_template(
        "month.html",
        yyyy_mm=yyyy_mm,
        tx=tx,
        total_income=total_income,
        total_expense=total_expense,
        net=net,
        by_category_rows=by_category_rows,
        prev_month=prev_month,
        next_month=next_month,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)