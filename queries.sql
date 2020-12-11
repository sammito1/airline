/**
Each flight has max_seats_econ equivalent to the below statement:
 */
SELECT COUNT(*) FROM app_seats
WHERE app_seats.aircraft_code = 'CR2' AND app_seats.fare_conditions = 'Economy';

/**
Each flight has a max_seats_bus equivalent to the below statement:
 */
 SELECT COUNT(*) FROM app_seats
 WHERE app_seats.aircraft_code = 'CR2' AND app_seats.fare_conditions = 'Business';

 /**
 Get available seats

 In other words:
 - For each flight, which seats are NOT present in the boarding pass table?
 - For example, let's search for econ seats in flight number 20
  */

/** Returns all possible seats for a given flight_id **/
SELECT * FROM app_seats WHERE
aircraft_code = (
    SELECT aircraft_code from app_flights
    WHERE app_flights.flight_id = 20
) ORDER BY seat_no DESC; /** Originally returns 116 rows **/

/** Returns seat_no that are taken in app_boarding_passes for a given flight_id **/
SELECT ticket_id, seat_no FROM app_boarding_passes
WHERE flight_id = 20
ORDER BY ticket_id;

/** Returns values of seat_no that are IN app_seats but NOT IN app_boarding_passes for flight_id=20**/
SELECT * FROM (
    SELECT * FROM app_seats WHERE
    aircraft_code = (
        SELECT aircraft_code from app_flights
        WHERE app_flights.flight_id = 20
    ) ORDER BY seat_no DESC /** Originally returns 116 rows **/
) as q1
WHERE q1.seat_no NOT IN (
    SELECT seat_no FROM app_boarding_passes
    WHERE flight_id = 20
    ORDER BY ticket_id
);