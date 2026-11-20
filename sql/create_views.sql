DROP VIEW IF EXISTS vw_booking_status;
CREATE VIEW vw_booking_status AS
SELECT booking_status, COUNT(*) AS booking_count
FROM bookings
GROUP BY booking_status;

DROP VIEW IF EXISTS vw_daily_booking_trend;
CREATE VIEW vw_daily_booking_trend AS
SELECT date, COUNT(*) AS total_bookings,
       SUM(COALESCE(is_successful, 0)) AS successful_bookings,
       SUM(COALESCE(is_cancelled, 0)) AS cancelled_bookings
FROM bookings
WHERE date IS NOT NULL
GROUP BY date
ORDER BY date;

DROP VIEW IF EXISTS vw_vehicle_performance;
CREATE VIEW vw_vehicle_performance AS
SELECT vehicle_type, COUNT(*) AS total_bookings,
       AVG(ride_distance) AS avg_ride_distance,
       AVG(customer_rating) AS avg_customer_rating,
       AVG(driver_ratings) AS avg_driver_rating,
       SUM(CASE WHEN COALESCE(is_successful,0)=1 THEN COALESCE(booking_value,0) ELSE 0 END)
           AS successful_booking_value
FROM bookings
GROUP BY vehicle_type;

DROP VIEW IF EXISTS vw_payment_revenue;
CREATE VIEW vw_payment_revenue AS
SELECT payment_method, COUNT(*) AS booking_count,
       SUM(CASE WHEN COALESCE(is_successful,0)=1 THEN COALESCE(booking_value,0) ELSE 0 END)
           AS successful_revenue
FROM bookings
GROUP BY payment_method;

DROP VIEW IF EXISTS vw_cancellation_reasons;
CREATE VIEW vw_cancellation_reasons AS
SELECT 'Customer' AS cancelled_by, customer_cancellation_reason AS reason,
       COUNT(*) AS booking_count
FROM bookings
WHERE customer_cancellation_reason IS NOT NULL
GROUP BY customer_cancellation_reason
UNION ALL
SELECT 'Driver' AS cancelled_by, driver_cancellation_reason AS reason,
       COUNT(*) AS booking_count
FROM bookings
WHERE driver_cancellation_reason IS NOT NULL
GROUP BY driver_cancellation_reason;
