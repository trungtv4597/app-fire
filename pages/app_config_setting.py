import streamlit as st
from psycopg2 import Error

from utils import init_connection, get_db_connection, release_connection, check_login

db_pool = init_connection()

# Get buckets from dim_bucket
def get_buckets():
    conn = get_db_connection(db_pool)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT bucket_name as name, id FROM dim_bucket ORDER BY 1")
                buckets = cur.fetchall()
                return {name: id for name, id in buckets}
        except Error as e:
            st.error(f"Failed to fetch buckets: {e}")
            return {}
        finally:
            release_connection(db_pool, conn)
    return {}

# Postgres operations
def insert_category(category_name, bucket_id):
    conn = get_db_connection(db_pool)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dim_category (category_name, bucket_id)
                    VALUES (%s, %s)
                    """, (str(category_name), int(bucket_id))
                )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to insert category: {e}")
            conn.rollback()
            return False
        finally:
            release_connection(db_pool, conn)
    return False

def insert_location(location_name, user_id):
    conn = get_db_connection(db_pool)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dim_location (location_name, updated_time, updated_by_id)
                    VALUES (%s, NOW(), %s)
                    """, (str(location_name), int(user_id))
                )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to insert location: {e}")
            conn.rollback()
            return False
        finally:
            release_connection(db_pool, conn)
    return False

# Streamlit UI
def main():
    check_login()

    st.title("Configuration Setting")

    st.header("Add New Location")
    # Create a form for location input and submission
    with st.form(key="location_form", clear_on_submit=True):
        location_name = st.text_input("New Location Name")
        submit_button = st.form_submit_button("Add Location")
        if submit_button:
            if not location_name:
                st.error("Please enter a location name.")
            else:
                user_id = st.session_state.user_id
                if insert_location(location_name, user_id):
                    st.success(f"Location '{location_name}' added successfully!")
                else:
                    pass

    st.header("Add New Category")
    # Get buckets
    bucket_dict = get_buckets()
    if not bucket_dict:
        st.warning("No buckets available. Please add buckets to the database.")
        return
    # Create aform for input and submission
    with st.form(key="category_form", clear_on_submit=True):
        selected_bucket = st.selectbox("select Bucket", bucket_dict.keys())
        category_name = st.text_input("New Category Name")
        
        submit_button = st.form_submit_button("Add Category")
        if submit_button:
            if not category_name:
                st.error("Please enter a category name.")
            else:
                if insert_category(category_name=category_name, bucket_id=bucket_dict.get(selected_bucket)):
                    st.success(f"Category <{category_name}> added successfully!")
                else:
                    pass

if __name__ == "__main__":
    main()