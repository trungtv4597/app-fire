SELECT SUM(net_income) AS net_income
FROM fact_income
WHERE income_date = %s AND user_id = %s