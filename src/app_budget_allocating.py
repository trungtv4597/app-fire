import streamlit as st
from psycopg2 import Error, pool
from datetime import datetime
import pandas as pd

# Initialize connection pool
@st.cache_resource
def init_connection():
    secrets = st.secrets["postgres"]
    try:
        return pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            dbname=secrets["DB_NAME"],
            user=secrets["DB_USER"],
            password=secrets["DB_PASSWORD"],
            host=secrets["DB_HOST"],
            port=secrets["DB_PORT"]
        )
    except Error as e:
        st.error(f"Error initializing connection pool: {e}")
        return None

db_pool = init_connection()

# Get database connection from pool
def get_db_connection():
    if db_pool is None:
        st.error("Connection pool not initialized!")
        return None
    return db_pool.getconn()

# Return connection to pool
def release_connection(conn):
    if db_pool is not None and conn is not None:
        db_pool.putconn(conn)

# Get categories from dim_category
def get_categories():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, category_name FROM dim_category ORDER BY category_name")
                categories = cur.fetchall()
                return {name: id for id, name in categories}
        except Error as e:
            st.error(f"Failed to fetch categories: {e}")
            return {}
        finally:
            release_connection(conn)
    return {}

# Delete existing budget allocations for the current month
def delete_existing_allocations(transaction_date):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                year = transaction_date.year
                month = transaction_date.month
                cur.execute(
                    """
                    DELETE FROM fact_transaction
                    WHERE EXTRACT(YEAR FROM transaction_date) = %s
                    AND EXTRACT(MONTH FROM transaction_date) = %s
                    AND description LIKE %s
                    """,
                    (year, month, 'Budget allocation for%')
                )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to delete existing allocations: {e}")
            return False
        finally:
            release_connection(conn)
    return False

# Insert budget allocations into fact_transaction
def insert_budget_allocations(allocations, transaction_date):
    conn = get_db_connection()
    cash_in_action_id = 3
    if conn:
        try:
            with conn.cursor() as cur:
                if not delete_existing_allocations(transaction_date):
                    return False
                for category_name, (category_id, percentage, amount) in allocations.items():
                    description = f"Budget allocation for {category_name} ({percentage:.1f}%)"
                    cur.execute(
                        """
                        INSERT INTO fact_transaction (transaction_date, description, amount, category_id, updated_time, action_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (transaction_date, str(description), float(amount), int(category_id), datetime.now(), int(cash_in_action_id))
                    )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to save budget allocations: {e}")
            return False
        finally:
            release_connection(conn)
    return False

# Streamlit UI
def main():
    st.title("Monthly Budget Allocator")

    # Initialize session state
    if "allocations" not in st.session_state:
        st.session_state.allocations = {}
    if "total_income" not in st.session_state:
        st.session_state.total_income = 0.0
    if "total_percentage" not in st.session_state:
        st.session_state.total_percentage = 0.0

    # Get categories
    categories = get_categories()
    if not categories:
        st.error("No categories available. Please add categories to the database.")
        return

    # Input total income
    total_income = st.number_input(
        "Total Monthly Income",
        min_value=0.0,
        format="%0.0f",
        step=100.0,
        key="total_income_input"
    )

    # Update total income in session state
    st.session_state.total_income = total_income

    # Initialize allocations if categories changed
    if set(categories.keys()) != set(st.session_state.allocations.keys()):
        st.session_state.allocations = {
            name: (id, 0.0, 0.0) for name, id in categories.items()
        }

    # Create two columns
    col1, col2 = st.columns([1, 1])

    # Left column for sliders
    with col1:
        st.header("Allocate Budget Percentages")
        total_percentage = 0.0
        for category_name in categories:
            percentage = st.slider(
                f"Percentage for {category_name}",
                min_value=0.0,
                max_value=100.0,
                # value=st.session_state.allocations[category_name][1],
                step=0.1,
                format="%0.1f%%",
                key=f"slider_{category_name}_{id(categories[category_name])}"
            )
            amount = (percentage / 100) * total_income
            st.session_state.allocations[category_name] = (categories[category_name], percentage, amount)
            total_percentage += percentage

    # Right column for dataframe
    with col2:
        st.header("Allocated Budgets")
        # Create a DataFrame from allocations
        data = {
            "Category": [],
            "Percentage (%)": [],
            "Amount (VND)": []
        }
        for category_name, (category_id, percentage, amount) in st.session_state.allocations.items():
            data["Category"].append(category_name)
            data["Percentage (%)"].append(f"{percentage:.1f}")
            data["Amount (VND)"].append(f"{amount:,.0f}")

        df = pd.DataFrame(data)
        st.dataframe(df)

    # Update total percentage in session state
    st.session_state.total_percentage = total_percentage

    # Display total percentage
    if total_percentage > 100:
        st.warning(f"Total allocation: {total_percentage:.1f}%. Please adjust to be below 100%.")
    else:
        st.success(f"Total allocation: {total_percentage:.1f}%")

    # Submit button
    if st.button("Save Budget Allocations"):
        if total_income <= 0:
            st.error("Please enter a valid total income greater than 0.")
        elif total_percentage > 100:
            st.error("Total percentage exceeds the limit.")
        else:
            transaction_date = datetime.now().date()
            success = insert_budget_allocations(
                st.session_state.allocations,
                transaction_date
            )
            if success:
                st.success("Budget allocations saved successfully!")
                # Reset session state
                st.session_state.allocations = {name: (id, 0.0, 0.0) for name, id in categories.items()}
                st.session_state.total_income = 0.0
                st.session_state.total_percentage = 0.0

if __name__ == "__main__":
    main()