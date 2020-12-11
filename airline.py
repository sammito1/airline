from cs50 import SQL
import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

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
            return render_template('purchase_ticket.html', order=ticket_list)
        elif flight_type == "one-way-connection":
            if len(flight_id_list) == 1:
                # next, we must find the flight for the second leg of the trip
                flights = get_second_leg(request.args.get('arrival-airport'), request.args.get('form-arrival-city'), request.args.get('chosen-arrival-date'))
            elif len(flight_id_list) == 2:
                # it's now time to render ticket checkout
                ticket_list = get_order_from_two_id(flight_id_list[0], flight_id_list[1])
                format_flights(ticket_list)
                return render_template('purchase_ticket.html', order=ticket_list)
        elif flight_type == "round-trip":
            if len(flight_id_list) == 1:
                # we must find the return flight for the arrival leg of the trip
                flights = get_roundtrip_arrivals(request.args.get('departure-airport'), request.args.get('arrival-airport'),
                request.args.get('chosen-arrival-date'), arrival_date)
            elif len(flight_id_list) == 2:
                # it's now time to render ticket checkout
                ticket_list = get_order_from_two_id(flight_id_list[0], flight_id_list[1])
                format_flights(ticket_list)
                return render_template('purchase_ticket.html', order=ticket_list)

    # format data in returned rows
    format_flights(flights)

    return render_template(
        'display_flights.html', flights=flights, cities=cities, departure_city=departure_city,
        arrival_city=arrival_city, flight_type=flight_type, departure_date=departure_date,
        arrival_date=arrival_date, flight_id_string=flight_id_string
    )

# for each flight, query for available seats
# for row in flights_query:
#
#     row["seats_available"] = db.execute("""
#         SELECT * FROM (
#         SELECT * FROM app_seats WHERE
#         aircraft_code = (
#             SELECT aircraft_code from app_flights
#             WHERE app_flights.flight_id = :flight_id
#         ) ORDER BY seat_no DESC
#         ) as q1
#         WHERE q1.seat_no NOT IN (
#             SELECT seat_no FROM app_boarding_passes
#             WHERE flight_id = :flight_id
#             ORDER BY ticket_id
#         ) 
#     """, flight_id = row["flight_id"])

def format_flights(flights):
    for flight in flights:
            departure_dt = flight["scheduled_departure"]
            arrival_dt = flight["scheduled_arrival"]
            flight["departure_formatted"] = departure_dt.strftime("%B %d, %Y %-I:%M %p")
            flight["arrival_formatted"] = arrival_dt.strftime("%B %d, %Y %-I:%M %p")

def get_order_from_one_id(flight_id):
    return db.execute(
        """
        SELECT * FROM (
            SELECT
                flight_id,
                flight_code,
                scheduled_departure,
                scheduled_arrival,
                departure_airport_id,
                departure_city,
                arrival_airport_id,
                city as arrival_city
            FROM (
                SELECT
                    flight_id,
                    flight_code,
                    scheduled_departure,
                    scheduled_arrival,
                    departure_airport_id,
                    city as departure_city,
                    arrival_airport_id
                FROM app_flights
                INNER JOIN app_airports
                ON app_flights.departure_airport_id=app_airports.airport_code
            ) as q1
            INNER JOIN app_airports
            ON q1.arrival_airport_id=app_airports.airport_code
        ) as q2
        WHERE
            flight_id =:id
        """,
        id = flight_id
    )

def get_order_from_two_id(flight_id_1, flight_id_2):
    return db.execute(
        """
        SELECT * FROM (
            SELECT
                flight_id,
                flight_code,
                scheduled_departure,
                scheduled_arrival,
                departure_airport_id,
                departure_city,
                arrival_airport_id,
                city as arrival_city
            FROM (
                SELECT
                    flight_id,
                    flight_code,
                    scheduled_departure,
                    scheduled_arrival,
                    departure_airport_id,
                    city as departure_city,
                    arrival_airport_id
                FROM app_flights
                INNER JOIN app_airports
                ON app_flights.departure_airport_id=app_airports.airport_code
            ) as q1
            INNER JOIN app_airports
            ON q1.arrival_airport_id=app_airports.airport_code
        ) as q2
        WHERE
            flight_id =:id1 OR
            flight_id =:id2
        """,
        id1 = flight_id_1,
        id2 = flight_id_2
    )
def get_nonstop_departures(departure_city, arrival_city, departure_date):
        return db.execute(
            """
            SELECT * FROM (
                SELECT
                    flight_id,
                    flight_code,
                    scheduled_departure,
                    scheduled_arrival,
                    departure_airport_id,
                    departure_city,
                    arrival_airport_id,
                    city as arrival_city
                FROM (
                    SELECT
                        flight_id,
                        flight_code,
                        scheduled_departure,
                        scheduled_arrival,
                        departure_airport_id,
                        city as departure_city,
                        arrival_airport_id
                    FROM app_flights
                    INNER JOIN app_airports
                    ON app_flights.departure_airport_id=app_airports.airport_code
                ) as q1
                INNER JOIN app_airports
                ON q1.arrival_airport_id=app_airports.airport_code
            ) as q2
            WHERE
                departure_city=:departing_city AND
                arrival_city=:arriving_city AND
                date(scheduled_departure)=:departing_date
            """
            , departing_city = departure_city, arriving_city = arrival_city,
            departing_date = departure_date)

def get_first_leg(departure_city, arrival_city, departure_date):
    return db.execute(
        """
        SELECT * FROM (
                SELECT
                    flight_id,
                    flight_code,
                    scheduled_departure,
                    scheduled_arrival,
                    departure_airport_id,
                    departure_city,
                    arrival_airport_id,
                    city as arrival_city
                FROM (
                    SELECT
                        flight_id,
                        flight_code,
                        scheduled_departure,
                        scheduled_arrival,
                        departure_airport_id,
                        city as departure_city,
                        arrival_airport_id
                    FROM app_flights
                    INNER JOIN app_airports
                    ON app_flights.departure_airport_id=app_airports.airport_code
                ) as q1
                INNER JOIN app_airports
                ON q1.arrival_airport_id=app_airports.airport_code
            ) as q2
            WHERE
                departure_city = :departing_from AND
                arrival_city != :arriving_to AND
                date(scheduled_departure) = :departing_when
        """,
        departing_from = departure_city,
        arriving_to = arrival_city,
        departing_when = departure_date
    )

def get_second_leg(departure_airport, arrival_city, scheduled_arrival):
    return db.execute(
        """
        SELECT * FROM
        (
            SELECT
                flight_id,
                flight_code,
                scheduled_departure,
                scheduled_arrival,
                departure_airport_id,
                departure_city,
                arrival_airport_id,
                city as arrival_city
            FROM
            (
                SELECT
                    flight_id,
                    flight_code,
                    scheduled_departure,
                    scheduled_arrival,
                    departure_airport_id,
                    city as departure_city,
                    arrival_airport_id
                FROM app_flights
                INNER JOIN app_airports
                ON app_flights.departure_airport_id=app_airports.airport_code
            ) as q1
            INNER JOIN app_airports
            ON q1.arrival_airport_id=app_airports.airport_code
        ) as q2
        WHERE
            departure_airport_id = :departure_airport_id AND
            arrival_city = :arrival_city_name AND
            scheduled_arrival BETWEEN :scheduled_arrival_datetime
            AND :scheduled_arrival_datetime::timestamptz + INTERVAL '24 hours';
        """,
        departure_airport_id=departure_airport,
        arrival_city_name=arrival_city,
        scheduled_arrival_datetime=scheduled_arrival
    )

def get_roundtrip_arrivals(prev_departure_airport, prev_arrival_airport, prev_arrival_datetime, return_date):
    return db.execute(
        """
        SELECT * FROM (
            SELECT
                flight_id,
                flight_code,
                scheduled_departure,
                scheduled_arrival,
                departure_airport_id,
                departure_city,
                arrival_airport_id,
                city as arrival_city
            FROM (
                SELECT
                    flight_id,
                    flight_code,
                    scheduled_departure,
                    scheduled_arrival,
                    departure_airport_id,
                    city as departure_city,
                    arrival_airport_id
                FROM app_flights
                INNER JOIN app_airports
                ON app_flights.departure_airport_id=app_airports.airport_code
            ) as q1
            INNER JOIN app_airports
            ON q1.arrival_airport_id=app_airports.airport_code
        ) as q2
        WHERE
            departure_airport_id=:departure_airport AND
            arrival_airport_id=:arrival_airport AND
            date(scheduled_arrival)=date(:returning_date) AND
            scheduled_departure > :arrival_datetime
        """
        , departure_airport = prev_arrival_airport, arrival_airport = prev_departure_airport,
        arrival_datetime = prev_arrival_datetime, returning_date = return_date)