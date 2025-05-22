SELECT 
    b.bucket_name,
    c.category_name,
    a.action_name,
    SUM(t.amount * a.multiply_factor) AS amount
FROM fact_transaction AS t
LEFT JOIN dim_category AS c ON c.id = t.category_id
LEFT JOIN dim_bucket AS b ON b.id = c.bucket_id
LEFT JOIN dim_user AS u ON u.id = t.user_id
LEFT JOIN dim_action AS a ON a.id = t.action_id
WHERE 
    b.bucket_type = 'Expense'
    AND u.id = %s
    AND t.transaction_date >= %s
    AND t.transaction_date < %s + INTERVAL '1 month'
GROUP BY 1, 2, 3