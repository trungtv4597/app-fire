INSERT INTO fact_income (
    updated_time, income_date, category_id, user_id, gross_income, paid_debt, net_income
)
VALUES (NOW(), %s, %s, %s, %s, %s, %s);