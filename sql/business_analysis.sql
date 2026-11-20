-- OLA Ride Insights: SQLite business analysis queries.
-- Run after: python src/run_pipeline.py
-- Note: queries are designed to tolerate optional fields by using common project columns.
-- Check PRAGMA table_info(bookings); if your workbook has different headers, update aliases.

-- 1. Successful bookings
SELECT * FROM bookings
WHERE LOWER(COALESCE(booking_status,'')) LIKE '%success%'
   OR LOWER(COALESCE(booking_status,'')) LIKE '%complete%';

-- 2. Average ride distance by vehicle type
SELECT vehicle_type, ROUND(AVG(ride_distance),2) AS avg_ride_distance
FROM bookings GROUP BY vehicle_type ORDER BY avg_ride_distance DESC;

-- 3. Customer-cancelled rides
SELECT COUNT(*) AS customer_cancelled_bookings
FROM bookings
WHERE LOWER(COALESCE(booking_status,'')) LIKE '%customer%cancel%';

-- 4. Top five customers by number of bookings
SELECT customer_id, COUNT(*) AS total_bookings
FROM bookings WHERE customer_id IS NOT NULL
GROUP BY customer_id ORDER BY total_bookings DESC LIMIT 5;

-- 5. Driver cancellation reasons
SELECT driver_cancellation_reason, COUNT(*) AS cancellations
FROM bookings
WHERE driver_cancellation_reason IS NOT NULL
GROUP BY driver_cancellation_reason ORDER BY cancellations DESC;

-- 6. Maximum and minimum driver ratings for Prime Sedan
SELECT MAX(driver_ratings) AS max_driver_rating,
       MIN(driver_ratings) AS min_driver_rating
FROM bookings
WHERE LOWER(COALESCE(vehicle_type,'')) LIKE '%prime sedan%';

-- 7. UPI bookings
SELECT * FROM bookings
WHERE LOWER(COALESCE(payment_method,'')) = 'upi';

-- 8. Average customer rating by vehicle type
SELECT vehicle_type, ROUND(AVG(customer_rating),2) AS avg_customer_rating
FROM bookings GROUP BY vehicle_type ORDER BY avg_customer_rating DESC;

-- 9. Successful booking value
SELECT ROUND(SUM(COALESCE(booking_value,0)),2) AS successful_booking_value
FROM bookings WHERE COALESCE(is_successful,0)=1;

-- 10. Incomplete rides and reasons
SELECT * FROM bookings
WHERE LOWER(COALESCE(booking_status,'')) LIKE '%incomplete%'
   OR COALESCE(incomplete_rides, '') IN ('1','Yes','YES');

-- Advanced 11. Hourly booking demand
SELECT booking_hour, COUNT(*) AS bookings
FROM bookings WHERE booking_hour IS NOT NULL
GROUP BY booking_hour ORDER BY booking_hour;

-- Advanced 12. Cancellation rate by vehicle
SELECT vehicle_type, COUNT(*) AS total_bookings,
       SUM(COALESCE(is_cancelled,0)) AS cancelled_bookings,
       ROUND(100.0*SUM(COALESCE(is_cancelled,0))/NULLIF(COUNT(*),0),2) AS cancellation_pct
FROM bookings GROUP BY vehicle_type ORDER BY cancellation_pct DESC;

-- Advanced 13. Revenue by payment method (successful bookings only)
SELECT payment_method,
       ROUND(SUM(CASE WHEN COALESCE(is_successful,0)=1 THEN COALESCE(booking_value,0) ELSE 0 END),2)
           AS successful_revenue
FROM bookings GROUP BY payment_method ORDER BY successful_revenue DESC;

-- Advanced 14. Top five customers by successful booking value
SELECT customer_id, ROUND(SUM(booking_value),2) AS total_successful_value
FROM bookings
WHERE customer_id IS NOT NULL AND COALESCE(is_successful,0)=1
GROUP BY customer_id ORDER BY total_successful_value DESC LIMIT 5;

-- Advanced 15. Daily ride distance
SELECT date, ROUND(SUM(COALESCE(ride_distance,0)),2) AS total_distance,
       ROUND(AVG(ride_distance),2) AS avg_distance
FROM bookings WHERE date IS NOT NULL
GROUP BY date ORDER BY date;
