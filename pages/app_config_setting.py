import streamlit as st

from postgres_operator import PostgresOperator
from utils import init_connection, check_login

db_pool = init_connection()
db_operator = PostgresOperator(db_pool)

def select_buckets():
    results, error = db_operator.execute_select('queries/select_buckets_all.sql')
    if error:
        st.error(f"Failed to fetch buckets: {error}")
        return {}
    return {row["name"]: row["id"] for row in results} if results else {}

# Postgres operations
def insert_categorys(category_name, bucket_id, user_id):
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_categories.sql",
        (category_name, bucket_id, user_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to record expenses: {error}")
        return False
    else:
        return True
    
def insert_locations(location_name, user_id):
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_locations.sql",
        (location_name, user_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to record expenses: {error}")
        return False
    else:
        return True

# Streamlit UI
def main():
    check_login()

    user_id = st.session_state.user_id

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
                if insert_locations(location_name=location_name, user_id=user_id):
                    st.success(f"Location <{location_name}> added successfully!")
                else:
                    pass

    st.header("Add New Category")
    # Get buckets
    buckets = select_buckets()
    if not buckets:
        st.warning("No buckets available. Please add buckets to the database.")
        return
    # Create a form for input and submission
    with st.form(key="category_form", clear_on_submit=True):
        selected_bucket = st.selectbox("Select Bucket", options=list(buckets.keys()))
        category_name = st.text_input("New Category Name")
        bucket_id=buckets.get(selected_bucket)
        
        submit_button = st.form_submit_button("Add Category")
        if submit_button:
            if not category_name:
                st.error("Please enter a category name.")
            else:
                if insert_categorys(category_name=category_name, bucket_id=bucket_id, user_id=user_id):
                    st.success(f"Category <{category_name}> of Bucket <{selected_bucket}> added successfully!")
                else:
                    pass

if __name__ == "__main__":
    main()