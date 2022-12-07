# CS50 FINAL PROJECT
Idea:
Our inspiration for this project arose about a month ago, when Maria's CVS Care Pass renewed after she set a mental reminder to cancel her subscription. That event sparked a conversation between all of us on how under-the-wraps the process of subscription services renewing is: often times, we forget about which services we have monthly and yearly memberships to, even if we mean to cancel them in a set amount of time. Whether that be anything from Spotify, to Netflix, to Hulu, to the New York Times, we'll sometimes take advantage of special deals, then lose track that we needed to change (or cancel) that subscription - or even had it in the first place. Thus, Subscriptify was born.
# BACKEND
To ensure Subscriptify runs smoothly, we used a combination of Python, Flask and SQL components to keep track of our users' data. The first component we completed for the backend of our website was creating subscribe.db, a database that keeps track of users and their current subscriptions, in SQL. Within subscribe.db, we have two tables, users and transactions:
- users: The table users records the information of each individual user, and has the following fields for each user: 
    - id: the user's unique ID number (primary key)
    - firstname
    - lastname
    - email
    - password (hash)
    - code: the code Subscriptify sends to the user to verify their email address
    - verified: a boolean value that checks whether or not the user has verified their email address
- transactions: The table transactions keeps track of each user's current and past subscriptions, and has the following fields for each subscription: 
    - id: the subscription's unique ID number (primary key)
    - user_id: the foreign key that references the primary key id in users
    - name: the name of the service that the user has subscribed to 
    - price: how much the user has to pay within the designated time frame
    - type: specifies whether the susbcription is monthly, yearly, or a free trial
    - reg_date: the date the user began their subscription
    - cancelled: whether the subscription has been cancelled or not
Subscriptify is a Python-based website, so all of the website's functions are contained in the file **app.py**. The app routes within this file are as follows:
    - /register: [POST] registers the user into the database once they fill out the required fields appropriately. 
    - /add: [POST] allows the user to add a subscription to their account once they fill out the required fields appropriately. 
    - /: This directs the user back to the homepage. 
    - /verify: [POST] allows the user to access their account once the user enters the correct verification code. 
    - /login: [POST] logs the user in after they correctly enter their email and password. 
    - /delete: This takes in the id of the subscription that is to be deleted and removes it from displaying of the homepage
    - /logout:
    - /: This takes the user to the homepage, where the user can add and delete subscriptions. 
For register, we decided to add a email verification system for users to register using Python libraries called MIME and SMTP, in order to add another layer or verification to creating a new user.
For add, we have features allows users to add either a monthly or yearly subscription or a free trial. A key technical aspect of this part was calculating the renewal date for the subscriptions, in which we had to consider special cases like subscription registration at the end of the month. Additionally, we calculate the monthly cost in subscriptions, including the months where yearly subscriptions renew.
# FRONTEND
For the interface of our website, we used HTML to create the pages of Subscriptify. 
The file styles.css gives Subscriptify a clean yet aesthetically pleasing design. 

