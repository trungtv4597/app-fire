CREATE TABLE IF NOT EXISTS 
dim_category (
			id SERIAL PRIMARY KEY,
			category_name TEXT NOT NULL UNIQUE
			)