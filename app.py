from flask import Flask, render_template, request, redirect
import sqlite3
from pathlib import Path

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
    conn.close()
    return render_template("index.html", rows=rows)

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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)