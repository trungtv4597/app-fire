SELECT MAX(t.transaction_date) AS latest_transaction_date
FROM fact_transaction AS t
WHERE
	t.user_id = %s