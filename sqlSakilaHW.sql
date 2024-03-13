USE sakila;

#Question 1:

SELECT a.first_name, a.last_name
FROM actor a
JOIN film_actor fa ON a.actor_id = fa.actor_id
JOIN film f ON fa.film_id = f.film_id
WHERE f.title = 'ACADEMY DINOSAUR';

#Question 2: 
SELECT c.name AS CategoryName, COUNT(f.film_id) AS NumberOfFilms
FROM category c
JOIN film_category fc ON c.category_id = fc.category_id
JOIN film f ON fc.film_id = f.film_id
GROUP BY c.name;

#Question 3:
SELECT f.rating, AVG(f.rental_duration) AS AverageRentalDuration
FROM film f
GROUP BY f.rating;

#Question 4:
SELECT cu.first_name, cu.last_name, COUNT(r.rental_id) AS TotalRentals
FROM customer cu
JOIN rental r ON cu.customer_id = r.customer_id
GROUP BY cu.first_name, cu.last_name;

#Question 5:
SELECT s.store_id, COUNT(r.rental_id) AS NumberOfRentals
FROM store s
JOIN inventory i ON s.store_id = i.store_id
JOIN rental r ON i.inventory_id = r.inventory_id
GROUP BY s.store_id
ORDER BY NumberOfRentals DESC
LIMIT 1;

#Question 6:
SELECT c.name AS CategoryName, COUNT(r.rental_id) AS CountOfRentals
FROM category c
JOIN film_category fc ON c.category_id = fc.category_id
JOIN film f ON fc.film_id = f.film_id
JOIN inventory i ON f.film_id = i.film_id
JOIN rental r ON i.inventory_id = r.inventory_id
GROUP BY c.name
ORDER BY CountOfRentals DESC
LIMIT 1;

#Question 7:
SELECT c.name AS CategoryName, AVG(f.rental_rate) AS AverageRentalRate
FROM category c
JOIN film_category fc ON c.category_id = fc.category_id
JOIN film f ON fc.film_id = f.film_id
GROUP BY c.name;

#Question 8:
SELECT f.title, MAX(r.rental_date) AS LastRentalDate
FROM film f
LEFT JOIN inventory i ON f.film_id = i.film_id
LEFT JOIN rental r ON i.inventory_id = r.inventory_id
GROUP BY f.title
HAVING MAX(r.rental_date) < DATE_SUB(NOW(), INTERVAL 1 MONTH) OR LastRentalDate IS NULL;

#Question 9:
SELECT cu.first_name, cu.last_name, SUM(p.amount) AS TotalSpending
FROM customer cu
JOIN rental r ON cu.customer_id = r.customer_id
JOIN payment p ON r.rental_id = p.rental_id
GROUP BY cu.first_name, cu.last_name;

#Question 10:
SELECT l.name AS Language, AVG(f.length) AS AverageLength
FROM film f
JOIN language l ON f.language_id = l.language_id
GROUP BY l.name;