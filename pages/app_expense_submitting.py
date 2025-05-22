import streamlit as st
from datetime import datetime

from postgres_operator import PostgresOperator
from utils import init_connection, check_login

# Initialize database connection pool and operator
db_pool = init_connection()
db_operator = PostgresOperator(db_pool)

def select_buckets():
    results, error = db_operator.execute_select('queries/select_buckets_spendable.sql')
    if error:
        st.error(f"Failed to fetch buckets: {error}")
        return {}
    return {row["name"]: row["id"] for row in results} if results else {}

def select_categories(bucket_id, user_id):
    results, error = db_operator.execute_select('queries/select_categories.sql', (bucket_id, user_id,))
    if error:
        st.error(f"Failed to fetch categories: {error}")
        return {}
    return {row['name']: row['id'] for row in results} if results else {}

def select_locations(user_id):
    results, error = db_operator.execute_select('queries/select_locations.sql', (user_id,))
    if error:
        st.error(f"Failed to fetch locations: {error}")
        return {}
    return {row['name']: row['id'] for row in results} if results else {}

def select_latest_transaction_date(user_id):
    results, error = db_operator.execute_select(
        'queries/select_latest_transaction_date.sql', 
        (user_id,)
    )
    if error:
        st.error(f"Failed to fetch data: {error}")
        return None
    return results[0]["latest_transaction_date"] if results else None

def insert_expenses(transaction_date, description, amount, category_id, user_id, location_id):
    cash_out_action_id = 4
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_expenses.sql",
        (transaction_date, description, amount, category_id, cash_out_action_id, user_id, location_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to record expenses: {error}")
        return False
    return True
    
# Initialize session state
def initialize_session_state():
    if "bucket_id" not in st.session_state:
        st.session_state.bucket_id = None
    if "categories" not in st.session_state:
        st.session_state.categories = {}

# Streamlit UI
def main():
    check_login()
    user_id = st.session_state.user_id
    
    # Init session state
    initialize_session_state()

    # Fetch data
    buckets = select_buckets()
    locations = select_locations(user_id)
    default_date = select_latest_transaction_date(user_id)

    st.title("Expense Tracker")

    # Bucket selection (outside the form)   
    # st.header("Select Bucket")
    bucket_col, button_col = st.columns([3, 3])
    with bucket_col:
        bucket_name = st.selectbox("Bucket", options=list(buckets.keys()))
    with button_col:
        if st.button("Select Bucket", key="select_bucket_button"):
            st.session_state.bucket_id = buckets.get(bucket_name)
            st.session_state.categories = select_categories(st.session_state.bucket_id, user_id)

    # Form
    with st.form("expense_form", clear_on_submit=True):
        st.header("Record New Expense")
        
        # Get categories for selected bucket
        if not st.session_state.categories:
            st.warning("Please select the bucket first!")
            category_name = st.selectbox("Category", ["None"])
            category_id = None
        else:
            category_name = st.selectbox("Category", options=list(st.session_state.categories.keys()))
            category_id = st.session_state.categories.get(category_name)

        location_name = st.selectbox("Location", options=list(locations.keys()))
        location_id = locations.get(location_name)
        
        transaction_date = st.date_input("Date", value=default_date)
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=1000, step=1000)

        submitted = st.form_submit_button("Record")
        if submitted:
            if insert_expenses(transaction_date, description, amount, category_id, user_id, location_id):
                st.success(f"Successfully recorded: {amount:,.0f} from {category_name} to {location_name} for {description}.")
            else:
                pass

if __name__ == "__main__":
    main()

