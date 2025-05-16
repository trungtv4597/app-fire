INSERT INTO dim_category (
    updated_time, category_name, bucket_id, user_id
)
VALUES (NOW(), %s, %s, %s)