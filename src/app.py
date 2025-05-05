import streamlit as st
import psycopg2
from psycopg2 import Error
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variable
load_dotenv()

# PostgreSQL connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Error as e:
        st.error(f"Error connecting to database: {e}")
        return None
    
# Get categories from dim_category
def get_categories():
    """"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT category_name as name, id FROM dim_category ORDER BY 1")
                categories = cur.fetchall()
                return {name: id for name, id in categories}
        except Error as e:
            st.error(f"Failed to fetch categories: {e}")
        finally:
            conn.close()
    return {}
    
# Insert expense into Postgres
def insert_expense(transaction_date, description, amount, category_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Store amount as negative
                negative_amount = -abs(float(amount))
                cur.execute(
                    """
                    INSERT INTO fact_transaction (transaction_date, description, amount, category_id)
                    VALUES (%s, %s, %s, %s)
                    """, (transaction_date, str(description), float(negative_amount), int(category_id))
                )
                conn.commit()
                st.success(f"Successfully recorded {negative_amount} for {description} in {category_id}")
        except Error as e:
            st.error(f"Failed to record expense: {e}")
        except Exception as e:
            st.error(f"Failed to record expense: {e}")
        finally:
            conn.close()

# Streamlit UI
def main():
    st.title("Expense Noting Application")

    # Get categories
    category_dict = get_categories()
    if not category_dict:
        st.error("No categories available. Please add categories to the database.")
        return

    # Expense submission form
    with st.form("Expense Form"):
        st.header("Record New Expense")

        # Form fields
        category_name = st.selectbox("Category", list(category_dict.keys()))
        transaction_date = st.date_input("Transaction Date", value=datetime.now())
        description = st.text_input("Description", placeholder="Enter expense description")
        amount = st.number_input("Amount", min_value=0.0, format="%0.1f", step=1000.0)

        # Submit button
        submitted = st.form_submit_button("Record")

        if submitted:
            if not description:
                st.error("Description is required")
            elif amount <= 0:
                st.error("Amount must be greater than 0")
            else:
                category_id = category_dict[category_name]
                insert_expense(transaction_date, description, amount, category_id)

if __name__ == "__main__":
    main()