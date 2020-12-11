/** Setting up the database for airline.py application **/

BEGIN;

DROP TABLE IF EXISTS app_bookings CASCADE;
DROP TABLE IF EXISTS app_tickets CASCADE;
DROP TABLE IF EXISTS app_boarding_passes CASCADE;
DROP TABLE IF EXISTS app_airports CASCADE;
DROP TABLE IF EXISTS app_aircraft CASCADE;
DROP TABLE IF EXISTS app_flights CASCADE;
DROP TABLE IF EXISTS app_seats CASCADE;
DROP TABLE IF EXISTS app_users CASCADE;

/** Manually create tables **/
CREATE TABLE app_bookings (
    booking_id SERIAL PRIMARY KEY,
    book_date timestamptz,
    card_number char(16),
    tax_amount numeric(10, 2),
    total_amount numeric (10, 2)
);

CREATE TABLE app_tickets (
    ticket_id SERIAL PRIMARY KEY,
    booking_id integer,
    passenger_id varchar(20),
    passenger_name text,
    passenger_email text,
    passenger_phone char(15),
    price numeric(10, 2),
    CONSTRAINT fk_booking_id
        FOREIGN KEY (booking_id)
            REFERENCES app_bookings(booking_id)
            ON DELETE SET NULL
);

CREATE TABLE app_airports (
    airport_code char(3) PRIMARY KEY,
    airport_name text,
    city text
);

CREATE TABLE app_aircraft (
    aircraft_code char(3) PRIMARY KEY,
    model text,
    range integer
);

CREATE TABLE app_seats (
    aircraft_code char(3),
    seat_no varchar(3),
    fare_conditions text,
    PRIMARY KEY(aircraft_code, seat_no)
);

CREATE TABLE app_flights (
    flight_id SERIAL PRIMARY KEY,
    flight_code char(6),
    scheduled_departure timestamptz,
    scheduled_arrival timestamptz,
    departure_airport_id char(3),
    arrival_airport_id char(3),
    flight_status varchar(20),
    aircraft_code char(3),
    arrival_gate varchar(3),
    movie boolean DEFAULT 'Yes',
    meal boolean DEFAULT 'Yes',
    /**
    max_seats_econ integer,
    max_seats_bus integer,
    price numeric(10, 2) DEFAULT 1000,
    **/
    price_econ numeric(10, 2) DEFAULT 350,
    price_bus numeric(10, 2) DEFAULT 750,

    CONSTRAINT fk_departure_airport_id
        FOREIGN KEY (departure_airport_id)
            REFERENCES app_airports(airport_code)
            ON DELETE SET NULL,

    CONSTRAINT fk_arrival_airport_id
        FOREIGN KEY (arrival_airport_id)
            REFERENCES app_airports(airport_code)
            ON DELETE SET NULL,

    CONSTRAINT fk_aircraft_code
        FOREIGN KEY (aircraft_code)
            REFERENCES app_aircraft(aircraft_code)
            ON DELETE SET NULL
);

CREATE TABLE app_boarding_passes (
    ticket_id integer,
    flight_id integer,
    boarding_num integer,
    seat_no varchar(4),
    boarding_time timestamptz,
    gate_id varchar(3),

    CONSTRAINT fk_ticket_id
        FOREIGN KEY (ticket_id)
            REFERENCES app_tickets(ticket_id)
                ON DELETE SET NULL,

    CONSTRAINT fk_flight_id
        FOREIGN KEY (flight_id)
            REFERENCES app_flights(flight_id)
                ON DELETE SET NULL,

    PRIMARY KEY(ticket_id, flight_id)
);

CREATE TABLE app_users (
    id SERIAL PRIMARY KEY,
    username text UNIQUE,
    hash text
);

COMMIT;