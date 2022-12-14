import os
import sqlite3

import smtplib
import time

import string
import random

from sql import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from helpers import apology, login_required, usd, job, verify_email#, test_scheduler

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


# Homepage (index)

@app.route("/")
@login_required
def index():
    # Gets first and last name of user to display on the homepage
    firstnames = db.execute("SELECT firstname FROM users WHERE id = ?", session["user_id"])  
    lastnames = db.execute("SELECT lastname FROM users WHERE id = ?", session["user_id"])  
    first_name = firstnames[0]["firstname"] 
    last_name = lastnames[0]["lastname"] 
    
    # Selects all subscriptions to display
    transactions_db = db.execute("SELECT * FROM transactions WHERE user_id = ? AND cancelled = ?", session["user_id"], 0)
    total = 0

    # Checks if user is email verified
    user_verified = db.execute("SELECT verified FROM users WHERE id = ?", session["user_id"])  
    user_verified_bool = user_verified[0]["verified"]
    if user_verified_bool == 0:
            return apology("User not verified", 400)

    # Calculates subscription renewal date to display on screen
    for entry in transactions_db:
        reg_date = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S')
        ren_date = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S')
        entry["ren_date"] = ren_date

        # Monthly subscriptions
        if entry["type"] == "Monthly":
            # Runs until next subscription renewal date (in the future)
            while ren_date < datetime.now():
                # Wrap-around from December to January
                if ren_date.month == 12:
                    new_month = 1
                    new_year = ren_date.year + 1
                else:
                    new_month = ren_date.month + 1
                    new_year = ren_date.year

                # Handles case when subscription was made on the last day of the month or on shorter months
                if new_month == 2 and (reg_date.day == 29 or reg_date.day == 30 or reg_date.day == 31):
                    ren_date = ren_date.replace(month = new_month, year = new_year, day = 28)
                elif (new_month == 4 or new_month == 6 or new_month == 9 or new_month == 11) and (reg_date.day == 31):
                    ren_date = ren_date.replace(month = new_month, year = new_year, day = 30)
                else:
                    ren_date = ren_date.replace(month = new_month, year = new_year, day = reg_date.day)
            
            # Updates renewal date and total price of subscriptions this month
            entry["ren_date"] = ren_date
            total += entry["price"]

        # Yearly subscriptions
        elif entry["type"] == "Yearly":
            # Runs until next subscription renewal date (in the future)
            while ren_date < datetime.now():
                new_year = ren_date.year + 1
                ren_date = ren_date.replace(year = new_year)
            entry["ren_date"] = ren_date

            if entry["ren_date"].month == datetime.now().month:
                total += entry["price"]
        
        # Free trial
        else:
            # Shows when free trial ends under the "renewal date"
            entry["ren_date"] = ren_date + timedelta(days = int(entry["type"]))
            entry["type"] = "Free Trial"
            
        entry["reg_date"] = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S').date()
        entry["ren_date"] = entry["ren_date"].date()

    return render_template("index.html", firstname=first_name, lastname=last_name, transactions=transactions_db, total=total)

# Page for adding a subscription
@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":

        # Gets subscription info from user (name, type, price, date)
        name = request.form.get("name")
        type = request.form.get("type")
        if type == "free_trial":
            type = request.form.get("trial_dates")
        price = request.form.get("price")
        month = request.form.get("month")
        day = request.form.get("day")
        year = request.form.get("year")

        # Checks if all fields are filled out / and are valid
        if not name:
            return apology("Must provide subscription name", 400)
        elif not type:
            return apology("Must provide subscription type", 400)
        elif type == "free_trial":
            if not trial_dates:
                return apology("Must provide length of free trial", 400)
        elif not price and type != "free_trial":
            return apology("Must provide subscription price", 400)
        elif not month or not day or not year:
            return apology("Must provide valid subscription date", 400)

        reg_date = month + "-" + day + "-" + year
        reg_date = datetime.strptime(reg_date,'%m-%d-%Y')

        # Adds new subscription for user into database
        db.execute("INSERT INTO transactions (user_id, name, price, type, reg_date, cancelled) VALUES (?, ?, ?, ?, ?, FALSE)",
                   session["user_id"], name, price, type, reg_date)

        flash("Added!")
        return redirect("/")

    else:
        return render_template("add.html")


# Registers new user
@app.route("/register", methods=["GET", "POST"])
def register():

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
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        db.execute("INSERT INTO users (firstname, lastname, email, hash, code, verified) VALUES(?, ?, ?, ?, ?, FALSE)", firstname, lastname, email, generate_password_hash(password), code)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Verify email
        verify_email(firstname, email, code)

        # Redirect user to home page
        return redirect("/verify")

    # request method is GET
    else:
        return render_template("register.html")

# Verifies new user with email verification
@app.route("/verify", methods=["GET", "POST"])
def verify():

    if request.method == "POST":

        # Takes in user's verification code input and checks if it matches the user's given code
        code = request.form.get("code")
        correct_code = db.execute("SELECT code FROM users WHERE id = ?", session["user_id"])[0]["code"]
        if code != str(correct_code):
            return apology("Invalid verification code", 400)

        # Redirect user to home page
        db.execute("UPDATE users SET verified = 1 WHERE id = ?", session["user_id"])
        return redirect("/")

    # request method is GET
    else:
        return render_template("verify.html")

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

        if rows[0]["verified"] == 0:
            return apology("Email not verified. Please register with another email.")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Deletes subscription entry
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    db.execute("UPDATE transactions SET cancelled = ? WHERE id = ?", 1, id)
    return redirect("/")

# Logs user out
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

def has_numbers(inputString):
    # Checks if string has numbers in it
    return any(char.isdigit() for char in inputString)

scheduler = BackgroundScheduler()
## The below code can help test the background scheduler, and will send an email every 20 seconds
##scheduler.add_job(func=test_scheduler, trigger="interval", seconds=20)

# schedules "job" (sends emails to users who have a subscription about to expire in the next 2 days) to run every day
scheduler.add_job(func=job, trigger="interval", days=1)
scheduler.start()