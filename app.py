from flask import Flask, render_template, request
from flask import redirect

app = Flask(__name__)

transactions = []

@app.route("/")
def home():
    return render_template("index.html", transactions=transactions)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]

        transaction = {
                    "amount": float(amount),
                    "category": category
                }

        transactions.append(transaction)

        return redirect("/")
            
    return render_template("add.html")


if __name__ == "__main__":
    app.run(debug=True)