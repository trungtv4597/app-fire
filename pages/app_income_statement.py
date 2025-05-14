import streamlit as st
from datetime import datetime
from psycopg2 import Error

from utils import init_connection, get_db_connection, release_connection, check_login

# Initialize database connection pool
db_pool = init_connection()

# Fetch the "Income" bucket ID
def get_income_bucket_id():
    conn = get_db_connection(db_pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM dim_bucket WHERE bucket_name = 'Income'")
            result = cur.fetchone()
            return result[0] if result else None
    except Error as e:
        st.error(f"Failed to fetch Income bucket ID: {e}")
        return None
    finally:
        release_connection(db_pool, conn)

# Fetch categories under the "Income" bucket
def get_income_categories(bucket_id, user_id):
    conn = get_db_connection(db_pool)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, category_name FROM dim_category WHERE bucket_id = %s AND user_id = %s ORDER BY category_name",
                (bucket_id, user_id,)
            )
            return cur.fetchall()
    except Error as e:
        st.error(f"Failed to fetch income categories: {e}")
        return []
    finally:
        release_connection(db_pool, conn)

# Fetch action ID by name
def get_action_id(action_name):
    conn = get_db_connection(db_pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM dim_action WHERE action_name = %s", (action_name,))
            result = cur.fetchone()
            return result[0] if result else None
    except Error as e:
        st.error(f"Failed to fetch action ID for {action_name}: {e}")
        return None
    finally:
        release_connection(db_pool, conn)

# Fetch category ID by name
def get_category_id(category_name):
    conn = get_db_connection(db_pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM dim_category WHERE category_name = %s", (category_name,))
            result = cur.fetchone()
            return result[0] if result else None
    except Error as e:
        st.error(f"Failed to fetch category ID for {category_name}: {e}")
        return None
    finally:
        release_connection(db_pool, conn)

# Insert debt transaction into fact_transaction
def insert_debt_transaction(transaction_date, amount, action_id, category_id, user_id):
    conn = get_db_connection(db_pool)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fact_transaction (transaction_date, description, amount, category_id, action_id, user_id, updated_time)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (transaction_date, "Maturity Debt Payment", amount, category_id, action_id, user_id)
            )
            conn.commit()
            return True
    except Error as e:
        st.error(f"Failed to insert debt transaction: {e}")
        return False
    finally:
        release_connection(db_pool, conn)

# Insert income record into fact_income
def insert_income_record(income_date, category_id, gross_income, paid_debt, net_income, user_id):
    conn = get_db_connection(db_pool)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO fact_income (created_time, updated_time, income_date, category_id, gross_income, paid_debt, net_income, user_id)
                VALUES (NOW(), NOW(), %s, %s, %s, %s, %s, %s)
                """,
                (income_date, category_id, gross_income, paid_debt, net_income, user_id)
            )
            conn.commit()
            return True
    except Error as e:
        st.error(f"Failed to insert income record: {e}")
        return False
    finally:
        release_connection(db_pool, conn)

# Initialize session state at the module level
def initialize_session_state():
    if "income_records" not in st.session_state:
        st.session_state.income_records = []
    if "total_debt" not in st.session_state:
        st.session_state.total_debt = 0.0
    if "income_date" not in st.session_state:
        st.session_state.income_date = None

# Streamlit App
def main():
    """"""
    check_login()
    user_id = st.session_state.user_id

    # Init session state
    initialize_session_state()

    st.title("Income Statement")

    # Fetch necessary data
    income_bucket_id = get_income_bucket_id()
    if not income_bucket_id:
        st.error("Income bucket not found in the database.")
        return

    income_categories = get_income_categories(income_bucket_id, user_id)
    if not income_categories:
        st.error("No categories found under the Income bucket.")
        return

    cash_in_action_id = get_action_id("CASH-IN")

    emergency_category_id = get_category_id("Emergency")
    if not cash_in_action_id or not emergency_category_id:
        st.error("Required action 'CASH-IN' or category 'EMERGENCY' not found.")
        return

    # Form for income and debt input
    with st.form("input_form"):
        # Date input (stored as the first of the month)
        selected_date = st.date_input("Select Date", value=datetime.now())
        income_date = selected_date.replace(day=1) # Start of the month

        # Gross income inputs for each category
        st.subheader("Gross Income by Category")
        gross_incomes = {}
        for cat_id, cat_name in income_categories:
            gross_incomes[cat_name] = st.number_input(
                f"{cat_name}",
                min_value=0.0,
                step=100000.0,
                value=0.0,
                key=f"gross_{cat_id}"
            )

        # Maturity debt input
        st.subheader("Maturity Debt")
        total_debt = st.number_input(
            "Total Maturity Debt for the Month",
            min_value=0.0,
            step=1000.0,
            value=0.0
        )

        calculate = st.form_submit_button("Calculate the 'Net Income'")

        if calculate:
            total_gross_income = sum(gross_incomes.values())
            if total_gross_income == 0:
                st.error("Cannot distribute debt with zero gross income.")
            else:
                # Calculate debt distribution
                debt_percentage = total_debt / total_gross_income if total_gross_income > 0 else 0

                income_records = []
                # Process each income category
                for cat_name, gross_income in gross_incomes.items():
                    if gross_income > 0:
                        paid_debt = gross_income * debt_percentage
                        net_income = gross_income - paid_debt
                        cat_id = next(id for id, name in income_categories if name == cat_name)
                        income_records.append((cat_id, gross_income, paid_debt, net_income))

                # Store results in session state
                st.session_state.income_records = income_records
                st.session_state.total_debt = total_debt
                st.session_state.income_date = income_date

                # Display results for review
                st.write(f"### Review Net Income for {str(income_date.year)}-{str(income_date.month)}")
                for cat_id, gross, debt, net in income_records:
                    cat_name = next(name for id, name in income_categories if id == cat_id)
                    st.write(f"**{cat_name}**: Gross: {gross:,.0f} | Paid Debt: {debt:,.0f} | Net: {net:,.0f}")

    # Form for confirming and saving
    if st.session_state.income_records:
        with st.form("confirm_form"):
            st.write("### Confirm and Save")
            confirm = st.form_submit_button("Confirm the Income Statement")

            if confirm:
                # Store debt transaction
                if st.session_state.total_debt > 0:
                    if not insert_debt_transaction(
                        st.session_state.income_date,
                        st.session_state.total_debt,
                        cash_in_action_id,
                        emergency_category_id,
                        user_id
                    ):
                        st.error("Failed to save debt payments.")
                        return
                
                # Store income records
                for cat_id, gross_income, paid_debt, net_income in st.session_state.income_records:
                    if not insert_income_record(
                        st.session_state.income_date,
                        cat_id,
                        gross_income,
                        paid_debt,
                        net_income,
                        user_id
                    ):
                        st.error(f"Failed to save income record for category ID {cat_id}.")
                        return
                
                st.success("Income statement saved successfully!")

                # Clear session state after saving
                st.session_state.income_records = []
                st.session_state.total_debt = 0.0
                st.session_state.income_date = None

if __name__ == "__main__":
    main()