INSERT INTO 
dim_category (category_name) 
VALUES 
	('Standard Meals'), 
	('Home Support'), 
	('Rent'), 
	('Apps')
ON CONFLICT (category_name) DO NOTHING