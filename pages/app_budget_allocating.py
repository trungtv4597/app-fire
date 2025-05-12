import streamlit as st
from psycopg2 import Error
from datetime import datetime
import pandas as pd
import plotly.express as px

from utils import init_connection, get_db_connection, release_connection, check_login

db_pool = init_connection()

# Get buckets and their categories from dim_bucket and dim_category
def get_buckets_and_categories(user_id):
    conn = get_db_connection(db_pool)
    if conn:
        try:
            with conn.cursor() as cur:
                # Fetch buckets
                cur.execute("SELECT id, bucket_name FROM dim_bucket ORDER BY bucket_name")
                buckets = cur.fetchall()
                bucket_dict = {name: id for id, name in buckets}
                
                # Fetch categories with bucket IDs
                cur.execute("""
                    SELECT c.id, c.category_name, b.bucket_name
                    FROM dim_category c
                    JOIN dim_bucket b ON c.bucket_id = b.id
                    WHERE c.user_id = %s
                    ORDER BY b.bucket_name, c.category_name
                """, (user_id,))
                categories = cur.fetchall()
                
                # Organize categories by bucket
                buckets_categories = {name: [] for name in bucket_dict}
                for cat_id, cat_name, bucket_name in categories:
                    buckets_categories[bucket_name].append((cat_name, cat_id))
                
                return bucket_dict, buckets_categories
        except Error as e:
            st.error(f"Failed to fetch buckets and categories: {e}")
            return {}, {}
        finally:
            release_connection(db_pool, conn)
    return {}, {}

# Delete existing budget allocations for the current month
def delete_existing_allocations(transaction_date, user_id):
    conn = get_db_connection(db_pool)
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
                    AND user_id = %s
                    """,
                    (year, month, 'Budget allocation for%', user_id)
                )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to delete existing allocations: {e}")
            return False
        finally:
            release_connection(db_pool, conn)
    return False

# Insert budget allocations into fact_transaction
def insert_budget_allocations(allocations, transaction_date, user_id):
    conn = get_db_connection(db_pool)
    cash_in_action_id = 3
    if conn:
        try:
            with conn.cursor() as cur:
                if not delete_existing_allocations(transaction_date, user_id):
                    return False
                for category_name, (category_id, price, quantity, amount) in allocations.items():
                    description = f"Budget allocation for {category_name} (Price: {price:,.0f}, Qty: {quantity})"
                    cur.execute(
                        """
                        INSERT INTO fact_transaction (transaction_date, description, amount, category_id, updated_time, action_id, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (transaction_date, str(description), float(amount), int(category_id), datetime.now(), int(cash_in_action_id), int(user_id))
                    )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to save budget allocations: {e}")
            return False
        finally:
            release_connection(db_pool, conn)
    return False

# Streamlit UI
def main():
    check_login()

    user_id = st.session_state.user_id
    user_name = st.session_state.username

    st.title(f"Hi {user_name}, Let's allocate budgets in this month")

    # Initialize session state
    if "allocations" not in st.session_state:
        st.session_state.allocations = {}
    if "net_income" not in st.session_state:
        st.session_state.net_income = 0.0
    if "total_amount" not in st.session_state:
        st.session_state.total_amount = 0.0

    # Get buckets and categories
    buckets, buckets_categories = get_buckets_and_categories(user_id=user_id)
    if not buckets or not buckets_categories:
        st.error("No buckets or categories available. Please add them to the database.")
        return

    # Input net income at the top. Net income = total income - monthly debt
    net_income = st.number_input(
        "Total Monthly Income (VND)",
        min_value=0.0,
        format="%0.0f",
        step=100.0,
        key="net_income_input"
    )

    # Update total income in session state
    st.session_state.net_income = net_income

    # Initialize allocations if categories changed
    current_categories = {(bucket, cat_name): cat_id for bucket in buckets_categories for cat_name, cat_id in buckets_categories[bucket]}
    if set(current_categories.keys()) != set((b, c) for b, c, _ in st.session_state.allocations.keys()):
        st.session_state.allocations = {
            (bucket, cat_name, cat_id): (cat_id, 0.0, 0, 0.0)
            for bucket in buckets_categories
            for cat_name, cat_id in buckets_categories[bucket]
        }

    # Create tabs for input and summary
    input_tab, summary_tab = st.tabs(["Budget Input", "Budget Summary"])

    # Input tab
    with input_tab:
        st.header("Allocate Budget by Category")
        total_amount = 0.0
        for bucket_name in buckets_categories:
            with st.expander(bucket_name, expanded=False):
                for cat_name, cat_id in buckets_categories[bucket_name]:
                    st.subheader(cat_name)
                    # Use columns for price and quantity to save vertical space
                    col1, col2 = st.columns(2)
                    with col1:
                        price = st.number_input(
                            "Price (VND)",
                            min_value=0.0,
                            format="%0.0f",
                            step=10000.0,
                            key=f"price_{bucket_name}_{cat_name}_{cat_id}"
                        )
                    with col2:
                        quantity = st.number_input(
                            "Quantity",
                            min_value=0,
                            format="%d",
                            step=1,
                            key=f"quantity_{bucket_name}_{cat_name}_{cat_id}"
                        )
                    amount = price * quantity
                    st.session_state.allocations[(bucket_name, cat_name, cat_id)] = (cat_id, price, quantity, amount)
                    total_amount += amount

    # Summary tab
    with summary_tab:
        st.header("Allocated Budgets")
        
        # Section 1: Aggregated by Category
        st.subheader("by Category")
        # Create a DataFrame from allocations
        data = {
            "Bucket": [],
            "Category": [],
            "Price (VND)": [],
            "Quantity": [],
            "Amount (VND)": []
        }
        for (bucket_name, cat_name, _), (_, price, quantity, amount) in sorted(st.session_state.allocations.items()):
            data["Bucket"].append(bucket_name)
            data["Category"].append(cat_name)
            data["Price (VND)"].append(f"{price:,.0f}")
            data["Quantity"].append(f"{quantity}")
            data["Amount (VND)"].append(f"{amount:,.0f}")

        # Add summary row
        data["Bucket"].append("Total")
        data["Category"].append("")
        data["Price (VND)"].append("")
        data["Quantity"].append("")
        data["Amount (VND)"].append(f"{total_amount:,.0f}")

        df = pd.DataFrame(data)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Amount (VND)": st.column_config.NumberColumn(format="%d")
            }
        )

        # Section 2: by Bucket
        st.subheader("by Bucket")
        # Aggreate amounts by bucket
        bucket_data = {
            "Bucket": [],
            "Amount (VND)": [],
            "Percentage (%)": []
        }
        for bucket_name in buckets_categories:
            bucket_total = sum(
                amount
                for (b, _, _), (_, _, _, amount) in st.session_state.allocations.items() 
                if b == bucket_name
            )
            if bucket_total >0: 
                bucket_data["Bucket"].append(bucket_name)
                bucket_data["Amount (VND)"].append(bucket_total)
                percentage = (bucket_total / net_income * 100) if net_income > 0 else 0
                bucket_data["Percentage (%)"].append(percentage)

        bucket_df = pd.DataFrame(bucket_data)
        if not bucket_df.empty:
            # Create pie chart
            fig = px.pie(
                bucket_df,
                values="Amount (VND)",
                names="Bucket",
                title="Bucket Allocation Distribution",
                hover_data=["Percentage (%)"],
                labels={"Percentage (%)": "Percentage of Total Income"}
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

            # Display bucket summary table below pie chart
            bucket_df["Amount (VND)"] = bucket_df["Amount (VND)"].apply(lambda x: f"{x:,.0f}")
            bucket_df["Percentage (%)"] = bucket_df["Percentage (%)"].apply(lambda x: f"{x:.1f}")
            st.dataframe(
                bucket_df,
                use_container_width=True,
                column_config={
                    "Amount (VND)": st.column_config.NumberColumn(format="%d"),
                    "Percentage (%)": st.column_config.NumberColumn(format="%.1f")
                }
            )
        else:
            st.info("No allocations made yet. Please add allocations in the Budget Input tab.")

    # Update total amount in session state
    st.session_state.total_amount = total_amount

    # Display total amount below tabs
    if total_amount > net_income:
        st.warning(f"Total allocated: {total_amount:,.0f} VND. Please adjust to be below income: {net_income:,.0f} VND.")
    else:
        percentage_used = (total_amount / net_income * 100) if net_income > 0 else 0
        st.success(f"Total allocated: {total_amount:,.0f} VND of {net_income:,.0f} VND ({percentage_used:.1f}%)")

    # Submit button below tabs
    if st.button("Save Budget Allocations"):
        if net_income <= 0:
            st.error("Please enter a valid total income greater than 0.")
        elif total_amount > net_income:
            st.error("Total allocated amount exceeds the income.")
        else:
            # Transform allocations for database insertion
            db_allocations = {
                cat_name: (cat_id, price, quantity, amount)
                for (bucket_name, cat_name, cat_id), (cat_id, price, quantity, amount) in st.session_state.allocations.items()
            }
            transaction_date = datetime.now().date()
            success = insert_budget_allocations(
                db_allocations,
                transaction_date,
                st.session_state.user_id
            )
            if success:
                st.success("Budget allocations saved successfully!")
                # Reset session state
                st.session_state.allocations = {
                    (bucket, cat_name, cat_id): (cat_id, 0.0, 0, 0.0)
                    for bucket in buckets_categories
                    for cat_name, cat_id in buckets_categories[bucket]
                }
                st.session_state.net_income = 0.0
                st.session_state.total_amount = 0.0

if __name__ == "__main__":
    main()