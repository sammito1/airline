from cs50 import SQL
import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

# from flask_session import Session
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# db = SQL("postgres://postgres:postgres@localhost:5432/COSC3380") # local db
db = SQL("postgres://cosc0168:1934844MS@code.cs.uh.edu:5432/COSC3380")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Missing username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Missing password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM app_users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    session.clear()

    if request.method == 'POST':
        if request.form.get("username") == '':
            return apology("Missing username.")

        if request.form.get("password") == '':
            return apology("Missing password.")

        
        #if request.form.get("password (again)") == '':
        if request.form.get("confirmation") == '':
            return apology("Please confirm password.")

        # if request.form.get("password") != request.form.get("password (again)"):
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match.")

        hashed_password = generate_password_hash(request.form.get("password"))

        # ensure username is unique
        rows = db.execute("SELECT * FROM app_users WHERE username = :username", username=request.form.get("username"))
        if len(rows) >= 1:
                return apology("Username already taken.")

        result = db.execute("INSERT INTO app_users (username, hash) VALUES(:username, :password)",
                           username = request.form.get("username"), password = hashed_password)
        if not result:
            return apology("Username already taken.")

        # Query database for username
        rows = db.execute("SELECT * FROM app_users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

# index
@app.route('/')
@login_required
def index():
    """ Display available flights """ 
    flights_query = db.execute("SELECT * FROM app_flights")

    # format data in returned rows
    """
    for row in flights_query:
        datetime_obj = row["scheduled_departure"]
        print(datetime_obj.strftime("%B %d, %Y"))
        print(datetime_obj.strftime("%-I:%M %p"))
    """

    return render_template('index.html', rows=flights_query)