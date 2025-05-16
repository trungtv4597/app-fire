SELECT location_name AS name, id 
FROM dim_location 
WHERE user_id = %s 
ORDER BY location_name;