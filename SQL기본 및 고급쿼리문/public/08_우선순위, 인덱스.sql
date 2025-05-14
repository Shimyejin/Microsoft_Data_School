SELECT 
    s.destination,
    SUM(p.raw_weight) AS prod_sum
FROM prod_result p
JOIN ship_result s ON p.chick_no = s.chick_no
GROUP BY s.destination
HAVING SUM(p.raw_weight) > 5000
ORDER BY prod_sum DESC
LIMIT 3;
