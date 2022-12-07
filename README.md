# CS50-Final-Project
Our final project is Subscriptify: a website that allows users to keep track of subscriptions. We used Python/Flask, SQLite, HTML, CSS, and Javascript to create our project.

To run the program, users must first install a few packages:

For SQL:
- pip3 install SQLAlchemy Flask-SQLAlchemy
- pip3 install sqlparse 
- pip3 install termcolor 

For Flask:
- pip3 install flask
- pip3 install flask-session

For helpers.py: 
- pip3 install requests

For Schedule:
- pip3 install schedule
- pip3 install APScheduler

We used a total of 12 files, divided between .html, .css, .py, and .db files.
- **layout.html** codes the general template that each individual page in the website uses
- Users interact with **add, index (homepage), login, and register.html**, which correspond to the respective pages on the website
- **apology.html** will pop up for users if their inputs (in any part of the website that asks for an input) are invalid
- **styles.css** dictates the style of our website (typeface, buttons, background, etc.)
- **sql.py** helps the program use/run SQL, taken from the CS50 github, and **subscribe.db** is the SQL database that stores all user and transaction information
- **app.py**, along with helper functions in **helpers.py**, run the bulk of our program and allow our Flask website to work

To run the program and display the Flask site, the user must start the Flask built-in web server, in their terminal:

    flask run
    
and follow the URL.

Upon entering the website, users must create an account with their first and last name, email address, password, and a password confirmation. The password must be greater than eight characters and contain at least one number. When creating a new account, an email verification with a randomly generated code is sent to users, which they must enter into the website before preceding. Once verified and logged in for the first time, the home page allows users to add their first subscription.

On the "add" page, users are asked to enter their subscription's name, type (Monthly, Yearly, or Free Trial. If it is a free trial, users are then asked to input the number of days' length.), and registration date.  

The home page displays a table of the subscriptions that a user has inputed, with their type, registration date, and (calculated) renewal date listed.
Additionally, the bottom of the table displays the total money due from subscriptions for that month, including yearly subscriptions on the months they are renewed.

An email is automated to be sent to remind users whenever a subscription of theirs is within one to two days of expiring. 

On the site header, users can log out.

Here is a video link to a project demonstration:
https://youtu.be/sEi11E6DEmU.

