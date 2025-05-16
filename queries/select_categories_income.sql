SELECT c.category_name AS name, c.id
FROM dim_category AS c
LEFT JOIN dim_bucket AS b ON c.bucket_id = b.id
WHERE b.bucket_name IN ('Income')  AND c.user_id = %s
ORDER BY id;