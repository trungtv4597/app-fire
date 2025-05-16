SELECT c.id
FROM dim_category AS c
WHERE c.category_name =%s  AND c.user_id = %s
ORDER BY id;