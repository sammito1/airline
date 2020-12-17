import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL

def apology(message, code=400):
    """Render message as an apology to user."""
    return render_template("apology.html", top=code, bottom=message), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def format_flights(flights):
    for flight in flights:
            departure_dt = flight["scheduled_departure"]
            arrival_dt = flight["scheduled_arrival"]
            flight["departure_formatted"] = departure_dt.strftime("%B %d, %Y %-I:%M %p")
            flight["arrival_formatted"] = arrival_dt.strftime("%B %d, %Y %-I:%M %p")

def format_flight(flight):
    departure_dt = flight["scheduled_departure"]
    arrival_dt = flight["scheduled_arrival"]
    flight["departure_formatted"] = departure_dt.strftime("%B %d, %Y %-I:%M %p")
    flight["arrival_formatted"] = arrival_dt.strftime("%B %d, %Y %-I:%M %p")

def get_seats_available(flight_id):
    return db.execute("""
        SELECT * FROM (
        SELECT * FROM app_seats WHERE
            aircraft_code = (
            SELECT aircraft_code from app_flights
            WHERE app_flights.flight_id = :flight_id
        ) ORDER BY seat_no DESC
        ) as q1
        WHERE q1.seat_no NOT IN (
            SELECT seat_no FROM app_tickets
            WHERE flight_id = :flight_id
            ORDER BY ticket_id
        ) 
        ORDER BY fare_conditions DESC
    """, flight_id = flight_id)

def add_ticket(user_id, name, email, phone, flight_id, seat_no, price, num_bags):
    db.execute(
        """
        INSERT INTO app_tickets(user_id, passenger_name, passenger_email, passenger_phone, flight_id, seat_no, price, num_bags)
        VALUES
        (
            :user_id, :passenger_name, :passenger_email, :passenger_phone, :flight_id, :seat_no, :price, :num_bags
        )
        """,
        user_id=user_id, passenger_name=name, passenger_email=email,
        passenger_phone=phone, flight_id=flight_id, seat_no=seat_no, price=price, num_bags=num_bags
    )
    return

def get_order_from_one_id(flight_id):
    return db.execute(
        """
        SELECT * FROM app_flights_modified
        WHERE
            flight_id =:id
        """,
        id = flight_id
    )

def get_order_from_two_id(flight_id_1, flight_id_2):
    return db.execute(
        """
        SELECT * FROM app_flights_modified
        WHERE
            flight_id =:id1 OR
            flight_id =:id2
        ORDER BY scheduled_departure
        """,
        id1 = flight_id_1,
        id2 = flight_id_2
    )

def get_nonstop_departures(departure_city, arrival_city, departure_date):
        return db.execute(
            """
            SELECT * FROM app_flights_modified
            WHERE
                departure_city=:departing_city AND
                arrival_city=:arriving_city AND
                date(scheduled_departure)=:departing_date
            ORDER BY scheduled_departure
            """
            , departing_city = departure_city, arriving_city = arrival_city,
            departing_date = departure_date)

def get_first_leg(departure_city, arrival_city, departure_date):
    return db.execute(
        """
        SELECT * FROM app_flights_modified
        WHERE
            departure_city = :departing_from AND
            arrival_city != :arriving_to AND
            date(scheduled_departure) = :departing_when AND
            arrival_airport_id IN
            (
                SELECT DISTINCT departure_airport_id FROM app_flights_modified
                WHERE
                    arrival_city = :arriving_to
            )
        ORDER BY scheduled_departure
        """,
        departing_from = departure_city,
        arriving_to = arrival_city,
        departing_when = departure_date
    )

def get_second_leg(departure_airport, arrival_city, scheduled_arrival):
    return db.execute(
        """
        SELECT * FROM app_flights_modified
        WHERE
            departure_airport_id = :departure_airport_id AND
            arrival_city = :arrival_city_name AND
            scheduled_arrival BETWEEN :scheduled_arrival_datetime
            AND :scheduled_arrival_datetime::timestamptz + INTERVAL '24 hours'
        ORDER BY scheduled_departure
        """,
        departure_airport_id=departure_airport,
        arrival_city_name=arrival_city,
        scheduled_arrival_datetime=scheduled_arrival
    )

def get_roundtrip_arrivals(prev_departure_airport, prev_arrival_airport, prev_arrival_datetime, return_date):
    return db.execute(
        """
        SELECT * FROM app_flights_modified
        WHERE
            departure_airport_id=:departure_airport AND
            arrival_airport_id=:arrival_airport AND
            date(scheduled_arrival)=date(:returning_date) AND
            scheduled_departure > :arrival_datetime
        ORDER BY scheduled_departure
        """
        , departure_airport = prev_arrival_airport, arrival_airport = prev_departure_airport,
        arrival_datetime = prev_arrival_datetime, returning_date = return_date)

def get_personal_flights(user_id):
    return db.execute(
        """
        SELECT * FROM app_tickets
        WHERE user_id = :user_id
        ORDER BY ticket_id
        """,
        user_id=user_id
    )

def get_flight_code(flight_id):
    return db.execute(
        """
        SELECT flight_code FROM app_flights WHERE flight_id = :flight_id
        """,
        flight_id=flight_id
    )[0]['flight_code']

def get_city(airport_id):
    return db.execute(
        """
        SELECT DISTINCT city FROM app_airports WHERE airport_code=:airport_code
        """,
        airport_code=airport_id
    )[0]['city']

def get_flight_details(flight_id):
    query = db.execute(
        """
        SELECT * FROM app_flights WHERE flight_id = :flight_id
        """,
        flight_id=flight_id
    )[0]
    query['departure_city'] = get_city(query['departure_airport_id'])
    query['arrival_city'] = get_city(query['arrival_airport_id'])
    return query