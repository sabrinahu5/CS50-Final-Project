import os
import requests
import urllib.parse

from datetime import datetime, timedelta

import smtplib
import schedule
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def renew_email(user_name, user_email, site):

    message = MIMEMultipart()
    message['From'] = "fromsubscriptify@gmail.com"
    message['To'] = user_email
    message['Subject'] = 'Heads up — your subscription renews soon'

    mail_content = '''Dear ''' + user_name + ''',
Your subscription to ''' + site + ''' will automatically renew in the next one to two days.

To cancel, please visit the subscription service's site.

Best,
The Subscriptify Team
    '''

    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)


    s.starttls()
    s.login("fromsubscriptify@gmail.com", "dzvfqqxwkpzyytkr")
    s.sendmail("fromsubscriptify@gmail.com", user_email, message.as_string())
    s.quit()


def job():
    user_name = db.execute("SELECT firstname FROM users WHERE user_id = ?", session["user_id"])
    user_email = db.execute("SELECT email FROM users WHERE user_id = ?", session["user_id"])
    transactions_db = db.execute("SELECT * FROM transactions WHERE user_id = ? AND cancelled = ?", session["user_id"], 0)
    for entry in transactions_db:
        site = entry["name"]
        if datetime.now() + timedelta(days = 2) > entry["ren_date"]:
            renew_email(user_name, user_email, site)

def verify_email(user_name, user_email, code):
    message = MIMEMultipart()
    message['From'] = "fromsubscriptify@gmail.com"
    message['To'] = user_email
    message['Subject'] = 'Please verify your email'

    mail_content = '''Dear ''' + user_name + ''',
Your email verification code is: ''' + code + ''' 

Please return to your homepage and enter the code above.

Best,
The Subscriptify Team
    '''

    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)


    s.starttls()
    s.login("fromsubscriptify@gmail.com", "dzvfqqxwkpzyytkr")
    s.sendmail("fromsubscriptify@gmail.com", user_email, message.as_string())
    s.quit()