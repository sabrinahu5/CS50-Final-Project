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
    return decorated_function\

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

        reg_date = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S')
        ren_date = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S')
        entry["ren_date"] = ren_date

        if entry["type"] == "Monthly":
            while ren_date < datetime.now():
                if ren_date.month == 12:
                    new_month = 1
                    new_year = ren_date.year + 1
                else:
                    new_month = ren_date.month + 1
                    new_year = ren_date.year

                
                if new_month == 2 and (reg_date.day == 29 or reg_date.day == 30 or reg_date.day == 31):
                    ren_date = ren_date.replace(month = new_month, year = new_year, day = 28)
                elif (new_month == 4 or new_month == 6 or new_month == 9 or new_month == 11) and (reg_date.day == 31):
                    ren_date = ren_date.replace(month = new_month, year = new_year, day = 30)
                else:
                    ren_date = ren_date.replace(month = new_month, year = new_year, day = reg_date.day)
                
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
            entry["type"] = "Free Trial"
            
        entry["reg_date"] = datetime.strptime(entry["reg_date"],'%Y-%m-%d %H:%M:%S').date()
        entry["ren_date"] = entry["ren_date"].date()
        

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



def test_scheduler():
    message = MIMEMultipart()
    message['From'] = "fromsubscriptify@gmail.com"
    message['To'] = "mcheng@college.harvard.edu"
    message['Subject'] = 'This is a test email'

    mail_content = '''
Best,
The Subscriptify Team
    '''

    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("fromsubscriptify@gmail.com", "dzvfqqxwkpzyytkr")
    s.sendmail("fromsubscriptify@gmail.com", "mcheng@college.harvard.edu", message.as_string())
    s.quit()