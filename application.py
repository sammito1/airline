import datetime, os, helpers
from helpers import *
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

db = SQL(os.environ.get("DATABASE_URL"))
helpers.db = SQL(os.environ.get("DATABASE_URL"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SECRET_KEY"] = '33f82044d3d0d13c6e0bb0cb7ac827c42668aa29c34f2bec'

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    if 'url' not in session:
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
        if 'url' in session:
            return redirect(session['url'])
        else:
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
    if 'url' not in session:
        session.clear()

    if request.method == 'POST':
        if request.form.get("username") == '':
            return apology("Missing username.")
        if request.form.get("password") == '':
            return apology("Missing password.")
        if request.form.get("confirmation") == '':
            return apology("Please confirm password.")
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

        if 'url' in session:
            return redirect(session['url'])
        else:
            return redirect("/")

    else:
        return render_template("register.html")

# display available flights
@app.route('/')
#@login_required
def display_flights():
    """ Display available departures """ 
    cities = db.execute(""" SELECT DISTINCT city FROM app_airports ORDER BY city """)
    # if no args have been passed, show default blank results page
    if not request.args:
        session['display-form-parameters'] = {
            'departure-city': "Moscow",
            'arrival-city': "St. Petersburg",
            'departure-date': "2020-12-16",
            'arrival-date': "2020-12-17",
            'flight-type': "one-way-nonstop",
        }
        session['flights-cart'] = []
        form_parameters = session['display-form-parameters']
        return render_template('display_flights.html', flights=[], cities=cities, form_parameters=form_parameters)
    # else, args came from either search form or the selection of a flight
    form_parameters = session['display-form-parameters']
    # if from search form, store args and display relevant flights
    if request.args.get('flight-type'):
        session['flights-cart'].clear()
        form_parameters['departure-city'] = request.args.get('departure-city')
        form_parameters['arrival-city'] = request.args.get('arrival-city')
        form_parameters['departure-date'] = request.args.get('departure-date')
        form_parameters['arrival-date'] = request.args.get('arrival-date')
        form_parameters['flight-type'] = request.args.get('flight-type')
        session['flights-cart'] = [] # empty cart
        if form_parameters['flight-type'] == "one-way-nonstop" or form_parameters['flight-type'] == "round-trip":
            flights = get_nonstop_departures(
                form_parameters['departure-city'], form_parameters['arrival-city'], form_parameters['departure-date'])
        elif form_parameters['flight-type'] == "one-way-connection":
            flights = get_first_leg(
                form_parameters['departure-city'], form_parameters['arrival-city'], form_parameters['departure-date'])
        format_flights(flights)
        return render_template('display_flights.html', flights=flights, cities=cities, form_parameters=form_parameters)
    # otherwise, a flight must have been selected from table
    else:
        new_id = request.args.get('chosen-departure-flight-id')
        session['flights-cart'].append(new_id)
        # three data processing possibilities, one for each type of flight
        if form_parameters['flight-type'] == "one-way-nonstop" and len(session['flights-cart']) == 1:
            # one-way nonstop trips need max one flight, show trip confirmation
            ticket_list = get_order_from_one_id(session['flights-cart'][0])
            session['url'] = url_for('checkout')
            format_flights(ticket_list)
            return render_template('confirm_trip.html', order=ticket_list)
        elif form_parameters['flight-type'] == "one-way-connection":
            if len(session['flights-cart']) == 1:
                # first part of connection has been found, must move on to next leg
                flights = get_second_leg(
                    request.args.get('chosen-arrival-airport'), form_parameters['arrival-city'],
                    request.args.get('chosen-arrival-date'))
                # display second leg flights
                return render_template('display_flights.html', flights=flights, cities=cities, form_parameters=form_parameters)
            elif len(session['flights-cart']) == 2:
                # second part of connection found, show trip confirmation
                ticket_list = get_order_from_two_id(session['flights-cart'][0], session['flights-cart'][1])
                session['url'] = url_for('checkout')
                format_flights(ticket_list)
                return render_template('confirm_trip.html', order=ticket_list)
        elif form_parameters['flight-type'] == "round-trip":
            if len(session['flights-cart']) == 1:
                # departure selected, must show arrivals
                flights = get_roundtrip_arrivals(
                    request.args.get('chosen-departure-airport'), request.args.get('chosen-arrival-airport'),
                    request.args.get('chosen-arrival-date'), form_parameters['arrival-date'])
                return render_template('display_flights.html', flights=flights, cities=cities, form_parameters=form_parameters)
            elif len(session['flights-cart']) == 2:
                # arrival selected, show trip confirmation 
                ticket_list = get_order_from_two_id(session['flights-cart'][0], session['flights-cart'][1])
                session['url'] = url_for('checkout')
                format_flights(ticket_list)
                return render_template('confirm_trip.html', order=ticket_list)

@app.route('/checkout', methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "GET":
        flight_id_list = session['flights-cart']

        if not flight_id_list:
            return redirect(url_for('display_flights'))
        if len(flight_id_list) == 1:
            flights = get_order_from_one_id(flight_id_list[0])
        elif len(flight_id_list) == 2:
            flights = get_order_from_two_id(flight_id_list[0], flight_id_list[1])

        for flight in flights:
            flight['seats_table'] = get_seats_available(flight['flight_id'])

        return render_template('checkout.html', flights=flights)

    else:
        # get personal info
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone')
        user_id = session["user_id"]

        # get seat and fare info
        flight_id_list = session['flights-cart']
        first_seat, first_fare, second_seat, second_fare = "", "", "", ""
        seat_fare_list, seat_list, price_list = [], [], []
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

        # get num bags
        num_bags = request.form.get('num-bags')
        
        # insert info for each ticket into ticket and boarding passes tables
        for i in range(len(flight_id_list)):
            add_ticket(user_id, name, email, phone_num, flight_id_list[i], seat_list[i], price_list[i], num_bags)

        return redirect('/my_flights')

@app.route('/my_flights')
@login_required
def my_flights():
    my_tickets = get_personal_flights(session["user_id"])

    # add flight details to tickets dict
    for ticket in my_tickets:
        ticket['flight_details'] = get_flight_details(ticket['flight_id'])
        format_flight(ticket['flight_details'])
    return render_template('my_flights.html', tickets=my_tickets)

if __name__ =="__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)