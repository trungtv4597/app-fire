import streamlit as st
from psycopg2 import Error
from datetime import datetime

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
    
# Get categories from dim_category
def get_categories(bucket_id):
    """"""
    conn = get_db_connection(db_pool)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                            SELECT category_name as name, id 
                            FROM dim_category 
                            WHERE bucket_id = %s
                            ORDER BY 1
                            """, (bucket_id,))
                categories = cur.fetchall()
                return {name: id for name, id in categories}
        except Error as e:
            st.error(f"Failed to fetch categories: {e}")
            return {}
        finally:
            release_connection(db_pool, conn)
    return {}

def get_locations():
    conn = get_db_connection(db_pool)
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT location_name as name, id FROM dim_location ORDER BY 1")
                locations = cur.fetchall()
                return {name: id for name, id in locations}
        except Error as e:
            st.error(f"Failed to fetch locations: {e}")
            return {}
        finally:
            release_connection(db_pool, conn)
    return {}
    
# Insert expense into Postgres
def insert_expense(transaction_date, description, amount, category_id, user_id, location_id):
    conn = get_db_connection(db_pool)
    cash_out_action_id = 4
    if conn:
        try:
            with conn.cursor() as cur:
                # Store amount as negative
                # negative_amount = -abs(float(amount))
                cur.execute(
                    """
                    INSERT INTO fact_transaction (transaction_date, description, amount, category_id, updated_time, action_id, user_id, location_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (transaction_date, str(description), float(amount), int(category_id), datetime.now(), int(cash_out_action_id), int(user_id), int(location_id))
                )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to record expense: {e}")
            return False
        finally:
            release_connection(db_pool, conn)
    return False

# Streamlit UI
def main():
    check_login()

    st.title("Expense Noting Application")

    # Initialize session state
    if "bucket_id" not in st.session_state:
        st.session_state.bucket_id = None
    if "category_dict" not in st.session_state:
        st.session_state.category_dict = {}

    # Get buckets and locations
    bucket_dict = get_buckets()
    if not bucket_dict:
        st.error("No buckets available. Please add buckets to the database.")
        return
    location_dict = get_locations()

    # Expense submission form
    with st.form("Expense Form", clear_on_submit=True):
        st.header("Record New Expense")

        # Select the bucket
        bucket_col, button_col = st.columns([3, 3])
        with bucket_col:
            bucket_name = st.selectbox("Bucket", list(bucket_dict.keys()), key="bucket_select")
        with button_col:
            selected_bucket = st.form_submit_button("Select Bucket")

        # Update categories when bucket is selected
        if selected_bucket:
            st.session_state.bucket_id = bucket_dict[bucket_name]
            st.session_state.category_dict = get_categories(st.session_state.bucket_id)

        # Get categories for selected bucket
        if not st.session_state.category_dict:
            st.error("No categories available. Please select a bucket")
            category_name = st.selectbox("Category", ["None"])
            category_id = None
        else:
            category_name = st.selectbox("Category", list(st.session_state.category_dict.keys()), key="category_select")
            category_id = st.session_state.category_dict[category_name]

        # Select location
        if not location_dict:
            st.error("No locations available.")
            location_name = st.selectbox("Location", ["None"], key="location_select")
            location_id = None
        else:
            location_name = st.selectbox("Location", list(location_dict.keys()), key="location_select")
            location_id = location_dict[location_name]

        # Basic form fields
        transaction_date = st.date_input("Transaction Date", value=datetime.now())
        description = st.text_input("Description", placeholder="Enter expense description")
        amount = st.number_input("Amount", min_value=0.0, format="%0.0f", step=1000.0)

        # Submit button
        submitted = st.form_submit_button("Record")

        if submitted:
            if not description:
                st.error("Description is required")
            elif amount <= 0:
                st.error("Amount must be greater than 0")
            elif not category_id:
                st.error("Please select a valid category")
            elif not location_id:
                st.error("Please select a valid location")
            else:
                user_id = st.session_state.user_id
                result = insert_expense(transaction_date, description, amount, category_id, user_id, location_id)
                if result:
                    st.success(f"Successfully recorded <{amount}> for <{category_name}>: {description}")

if __name__ == "__main__":
    main()