SELECT c.id AS category_id, c.category_name, b.bucket_name
FROM dim_category c
JOIN dim_bucket b ON c.bucket_id = b.id
WHERE c.user_id = %s AND b.bucket_type IN ('Expense', 'Saving') 
ORDER BY b.id