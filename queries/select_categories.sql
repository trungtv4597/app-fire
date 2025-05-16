SELECT category_name AS name, id
FROM dim_category 
WHERE bucket_id = %s AND user_id = %s 
ORDER BY id;