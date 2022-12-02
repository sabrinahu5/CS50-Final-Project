import os
import sqlite3

from sql import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure to use SQLite database
#connection = sqlite3.connect("subscribe.db", check_same_thread = False)
#db = connection.cursor()
db = SQL("sqlite:///subscribe.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
    #raise RuntimeError("API_KEY not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# home page w/ subscription index

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    transactions_db = db.execute("SELECT * FROM transactions WHERE user_id = ? AND cancelled = ?", session["user_id"], 0)
    total = 0

    for entry in transactions_db:
        ren_date = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S')

        if entry["type"] == "Monthly":
            while ren_date < datetime.now():
                if ren_date.month == 12:
                    new_month = 1
                    new_year = ren_date.year + 1
                else:
                    new_month = ren_date.month + 1
                    new_year = ren_date.year
                ren_date = ren_date.replace(month = new_month, year = new_year)
            entry["ren_date"] = ren_date
            total += entry["price"]

        elif entry["type"] == "Yearly":
            while ren_date < datetime.now():
                new_year = ren_date.year + 1
                ren_date = ren_date.replace(year = new_year)
            entry["ren_date"] = ren_date

            if entry["ren_date"].month == datetime.now().month:
                total += entry["price"]

        else:
            entry["ren_date"] = ren_date + timedelta(days = int(entry["type"]))

    return render_template("index.html", transactions=transactions_db, total=total)

# page for adding a subscription
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        name = request.form.get("name")
        type = request.form.get("type")
        price = request.form.get("price")

        today = datetime.now()

        db.execute("INSERT INTO transactions (user_id, name, price, type, reg_date, cancelled) VALUES (?, ?, ?, ?, ?, FALSE)",
                   session["user_id"], name, price, type, today)

        flash("Added!")
        return redirect("/")

    else:
        return render_template("add.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Takes in input
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks username, password, verification were all submitted
        if not firstname:
            return apology("Must provide first name", 400)
        elif not lastname:
            return apology("Must provide last name", 400)
        elif not email:
            return apology("Must provide email", 400)
        elif not password:
            return apology("Must provide password", 400)
        elif not confirmation:
            return apology("Must provide confirmation", 400)

        # Checks if password and verification match
        if password != confirmation:
            return apology("Please make sure your passwords match")

        # Checks if password is long enough and has at least one number
        if len(password) < 8 or not has_numbers(password):
            return apology("Passwords must be at least 8 characters long and contain a number")

        # Checks if username is taken by looking at if username already exists in database
        if len(db.execute("SELECT * FROM users WHERE email = ?", email)) > 0:
            return apology("Email is already associated with a registered account")

        # Insert new username and password into database
        db.execute("INSERT INTO users (firstname, lastname, email, hash) VALUES(?, ?, ?, ?)", firstname, lastname, email, generate_password_hash(password))

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # request method is GET
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# page for cancelling a subscription
@app.route("/cancel", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        db.execute("INSERT INTO transactions (user_id, name, price, type, reg_date, cancelled) VALUES (?, ?, ?, ?, ?, FALSE)",
                   session["user_id"], name, price, type, today)

        flash("Added!")
        return redirect("/")

    else:
        return render_template("add.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

def has_numbers(inputString):
    # Checks if string has numbers in it
    return any(char.isdigit() for char in inputString)
