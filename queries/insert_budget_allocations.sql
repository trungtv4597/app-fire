INSERT INTO fact_transaction (
    updated_time, transaction_date, description, amount, 
    category_id, action_id, user_id
) VALUES (NOW(), %s, %s, %s, %s, %s, %s);