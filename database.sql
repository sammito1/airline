/** Setting up the database for airline.py application **/

BEGIN;

DROP TABLE IF EXISTS app_bookings CASCADE;
DROP TABLE IF EXISTS app_tickets CASCADE;
DROP TABLE IF EXISTS app_boarding_passes CASCADE;
DROP TABLE IF EXISTS app_airports CASCADE;
DROP TABLE IF EXISTS app_aircraft CASCADE;
DROP TABLE IF EXISTS app_gates CASCADE;
DROP TABLE IF EXISTS app_flights CASCADE;

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

CREATE TABLE app_gates (
    gate_id varchar(3) PRIMARY KEY
);

CREATE TABLE app_flights (
    flight_id SERIAL PRIMARY KEY,
    flight_code char(6),
    scheduled_departure timestamptz,
    scheduled_arrival timestamptz,
    actual_departure timestamptz,
    actual_arrival timestamptz,
    departure_airport_id char(3),
    arrival_airport_id char(3),
    flight_status varchar(20),
    aircraft_code char(3),
    arrival_gate varchar(3),
    movie boolean,
    meal boolean,
    seats_remaining integer DEFAULT 100,
    price numeric(10, 2) DEFAULT 1000,

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
            ON DELETE SET NULL,

    CONSTRAINT fk_arrival_gate
        FOREIGN KEY (arrival_gate)
            REFERENCES app_gates(gate_id)
                ON DELETE SET NULL
);

CREATE TABLE app_boarding_passes (
    ticket_id integer,
    flight_id integer,
    boarding_num integer,
    seat_num varchar(4),
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

/** Add data to tables **/
/**

MAKE SURE hw4 directory has a folder called `data` that contains `aircraft.csv`, `airports.csv`,
and `flights.csv`.


RUN THESE COMMANDS IN PSQL SHELL

\copy app_airports(airport_code, airport_name, city) FROM '~/hw4/data/airports.csv' DELIMITER ',' CSV HEADER
\copy app_aircraft(aircraft_code, model, range) FROM '~/hw4/data/aircraft.csv' DELIMITER ',' CSV HEADER
\copy app_flights(flight_code, scheduled_departure,scheduled_arrival,departure_airport_id, arrival_airport_id,flight_status,aircraft_code,actual_departure,actual_arrival) FROM '~/hw4/data/flights.csv' DELIMITER ',' CSV HEADER

**/