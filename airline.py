from cs50 import SQL
import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import helpers
from helpers import *

# read from password file
password_file = open("password.txt")
password_file_lines = password_file.read().splitlines()
login_info = {"username": password_file_lines[0], "password": password_file_lines[1]}
username = login_info["username"]
password = login_info["password"]

# from flask_session import Session
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

#db = SQL("postgres://postgres:postgres@localhost:5432/COSC3380") # local db
db = SQL(f"postgres://{username}:{password}@code.cs.uh.edu:5432/COSC3380") # uh db
helpers.db = SQL(f"postgres://{username}:{password}@code.cs.uh.edu:5432/COSC3380") # uh db

#db = SQL(f"postgres://{username}:{password}@ec2-54-146-118-15.compute-1.amazonaws.com:5432/d963gfgsgh737s") # heroku db

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

# display available flights
@app.route('/')
@login_required
def display_flights():
    """ Display available departures """ 

    cities = db.execute(
        """
        SELECT DISTINCT city
        FROM app_airports
        ORDER BY city
        """
    )

    # check if any url params have been passed. if not, just display some defaults and empty table
    if not request.args:
        departure_city = "Moscow"
        arrival_city = "St. Petersburg"
        departure_date = "2020-12-16"
        arrival_date = "2020-12-17"
        flight_type = "one-way-nonstop"
        flights = []
        flight_id_string = ""
        return render_template(
            'display_flights.html', flights=flights, cities=cities, departure_city=departure_city,
            arrival_city=arrival_city, flight_type=flight_type, departure_date=departure_date,
            arrival_date=arrival_date, flight_id_string=flight_id_string
        )

    # at this point, a get request was submitted by form, passing in the following args
    departure_city = request.args.get('departure-city')
    arrival_city = request.args.get('arrival-city')
    departure_date = request.args.get('departure-date')
    arrival_date = request.args.get('arrival-date')
    flight_type = request.args.get('flight-type')
    flight_id_string = request.args.get('flight-id-string')

    if not request.args.get('chosen-departure-flight-id'):
        # if get request was a result of simple search... simply display flights and empty cart
        flight_id_string = "" 
        if flight_type == "one-way-nonstop" or flight_type == "round-trip":
            flights = get_nonstop_departures(departure_city, arrival_city, departure_date) 
        elif flight_type == "one-way-connection":
            flights = get_first_leg(departure_city, arrival_city, departure_date)
    else:
        # otherwise, a flight must have been selected from table
        flight_id_string += request.args.get('chosen-departure-flight-id')
        flight_id_string += ','
        flight_id_list = flight_id_string.split(',')[:-1]

        if flight_type == "one-way-nonstop" and len(flight_id_list) == 1:
            # one-way nonstop trips need max one flight, so send to checkout
            ticket_list = get_order_from_one_id(flight_id_list[0])
            format_flights(ticket_list)
            return render_template('confirm_trip.html', order=ticket_list, flight_id_string = flight_id_string)
        elif flight_type == "one-way-connection":
            if len(flight_id_list) == 1:
                # next, we must find the flight for the second leg of the trip
                flights = get_second_leg(request.args.get('arrival-airport'), request.args.get('form-arrival-city'), request.args.get('chosen-arrival-date'))
            elif len(flight_id_list) == 2:
                # it's now time to render ticket checkout
                ticket_list = get_order_from_two_id(flight_id_list[0], flight_id_list[1])
                format_flights(ticket_list)
                return render_template('confirm_trip.html', order=ticket_list, flight_id_string = flight_id_string)
        elif flight_type == "round-trip":
            if len(flight_id_list) == 1:
                # we must find the return flight for the arrival leg of the trip
                flights = get_roundtrip_arrivals(request.args.get('departure-airport'), request.args.get('arrival-airport'),
                request.args.get('chosen-arrival-date'), arrival_date)
            elif len(flight_id_list) == 2:
                # it's now time to render ticket checkout
                ticket_list = get_order_from_two_id(flight_id_list[0], flight_id_list[1])
                format_flights(ticket_list)
                return render_template('confirm_trip.html', order=ticket_list, flight_id_string = flight_id_string)

    # format data in returned rows
    format_flights(flights)

    return render_template(
        'display_flights.html', flights=flights, cities=cities, departure_city=departure_city,
        arrival_city=arrival_city, flight_type=flight_type, departure_date=departure_date,
        arrival_date=arrival_date, flight_id_string=flight_id_string
    )

@app.route('/checkout', methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "GET":
        # convert flight id string into list
        flight_id_str = request.args.get('flight-id-string')
        flight_id_list = flight_id_str.split(',')[:-1]
        flights = []

        if len(flight_id_list) == 1:
            flights = get_order_from_one_id(flight_id_list[0])
        elif len(flight_id_list) == 2:
            flights = get_order_from_two_id(flight_id_list[0], flight_id_list[1])
            
        for flight in flights:
            flight['seats_table'] = 'test'
            flight['seats_table'] = get_seats_available(flight['flight_id'])

        return render_template('checkout.html', flights=flights, flight_id_str=flight_id_str)
    else:
        # get personal info
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone')
        user_id = session["user_id"]

        # get seat and fare info
        first_seat, first_fare, second_seat, second_fare, flight_id_str = "", "", "", "", ""
        flight_id_list, seat_fare_list, seat_list, price_list = [], [], [], []
        if request.form.get('seat-fare-0'):
            seat_fare_list = eval(request.form.get('seat-fare-0'))
            seat_list.append(seat_fare_list[0])
            first_fare = seat_fare_list[1]
            if first_fare == "Economy":
                price_list.append(250)
            else:
                price_list.append(800)
        if request.form.get('seat-fare-1'):
            seat_fare_list = eval(request.form.get('seat-fare-1'))
            seat_list.append(seat_fare_list[0])
            second_fare = seat_fare_list[1]
            if second_fare == "Economy":
                price_list.append(250)
            else:
                price_list.append(800)
        if request.form.get('flight-id-string'):
            flight_id_str = request.form.get('flight-id-string')
            flight_id_list = flight_id_str.split(',')[:-1]

        # get num bags
        num_bags = request.form.get('num-bags')
        
        # insert info for each ticket into ticket and boarding passes tables
        for i in range(len(flight_id_list)):
            add_ticket(user_id, name, email, phone_num, flight_id_list[i], seat_list[i], price_list[i], num_bags)

        # determine total cost
        return redirect('/my_flights')


@app.route('/my_flights')
@login_required
def my_flights():
    my_tickets = get_personal_flights(session["user_id"])
    
    # add flight details to tickets dict
    for ticket in my_tickets:
        #ticket['flight_code'] = get_flight_code(ticket['flight_id'])
        ticket['flight_details'] = get_flight_details(ticket['flight_id'])
        format_flight(ticket['flight_details'])

    return render_template('my_flights.html', tickets=my_tickets)