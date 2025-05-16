UPDATE fact_transaction
SET 
    amount = %s,
    updated_time = NOW(),
    description = %s
WHERE id = %s