SELECT 
	bucket_name AS name, 
	id 
FROM dim_bucket 
WHERE 
	bucket_type IN ('Expense', 'Saving', 'Investing') 
ORDER BY id;