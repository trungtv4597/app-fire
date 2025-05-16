SELECT t.id AS transaction_id, t.category_id, t.amount
FROM fact_transaction t
WHERE 
    t.action_id = 3
    AND t.transaction_date = %s
    AND t.user_id = %s