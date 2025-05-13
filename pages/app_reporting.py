import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from psycopg2 import Error

from utils import init_connection, get_db_connection, release_connection, check_login

db_pool = init_connection()

# Fetch budget and expense data for the pivot table
def fetch_expense_data(user_id):
    conn = get_db_connection(db_pool)
    if conn:
        try:
            cur = conn.cursor()
            sql_query = """
            SELECT 
                b.bucket_name,
                c.category_name,
                a.action_name,
                SUM(t.amount * a.multiply_factor) AS amount
            FROM fact_transaction AS t
            LEFT JOIN dim_category AS c ON c.id = t.category_id
            LEFT JOIN dim_bucket AS b ON b.id = c.bucket_id
            LEFT JOIN dim_user AS u ON u.id = t.user_id
            LEFT JOIN dim_action AS a ON a.id = t.action_id
            WHERE 
                b.bucket_type = 'Expense'
                AND u.id = %s
                AND t.transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
                AND t.transaction_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            GROUP BY 1, 2, 3
            """
            cur.execute(sql_query, (user_id,))
            results = cur.fetchall()
            cur.close()
            return [(row[0], row[1], row[2], float(row[3])) for row in results]
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            release_connection(db_pool, conn)
    return []

# Main Streamlit app
def main():
    check_login()

    st.title(f"Budget Overview for {datetime.now().strftime('%B %Y')}")

    # Create tabs for Expense and Gauge Charts
    expense_tab, _, _ = st.tabs(["Expense", "Balance Sheet", "FIRE"])

    # Expense Tab with Pivot Table
    with expense_tab:
        st.header("Expense Tracking")
        results = fetch_expense_data(user_id=st.session_state.user_id)
        
        if results:
            # Create DataFrame
            df = pd.DataFrame(results, columns=['Bucket', 'Category', 'Action', 'Amount'])
            
            # Pivot the data
            pivot_df = df.pivot_table(
                index=['Bucket', 'Category'],
                columns='Action',
                values='Amount',
                fill_value=0
            ).reset_index()
            
            # Rename columns based on action names (assuming action_id 3 is Budget, 4 is Expense)
            pivot_df.columns.name = None
            action_map = {name: name for name in pivot_df.columns[2:]}  # Keep original names
            for col in pivot_df.columns[2:]:
                if 'cash-in' in col.lower():  # Flexible matching for 'Cash In'
                    action_map[col] = 'Budget'
                elif 'cash-out' in col.lower():  # Flexible matching for 'Cash Out'
                    action_map[col] = 'Expenses'
            pivot_df = pivot_df.rename(columns=action_map)
            
            # Ensure Budget and Expenses columns exist
            if 'Budget' not in pivot_df.columns:
                pivot_df['Budget'] = 0.0
            if 'Expenses' not in pivot_df.columns:
                pivot_df['Expenses'] = 0.0
            
            # Calculate Remaining and Percentage Spent
            pivot_df['Remaining'] = pivot_df['Budget'] + pivot_df['Expenses']
            pivot_df['Percentage Spent'] = (
                (abs(pivot_df['Expenses']) / pivot_df['Budget'] ) * 100
            )
            # .where(pivot_df['Budget'] > 0, 1)
            
            # Format numbers for display
            display_df = pivot_df.copy()
            display_df['Budget'] = display_df['Budget'].apply(lambda x: f"{x:,.0f}")
            display_df['Expenses'] = display_df['Expenses'].apply(lambda x: f"{x:,.0f}")
            display_df['Remaining'] = display_df['Remaining'].apply(lambda x: f"{x:,.0f}")
            display_df['Percentage Spent'] = display_df['Percentage Spent'].apply(lambda x: f"{x:.2f}%")
            
            # Display pivot table
            st.dataframe(
                display_df,
                use_container_width=True
            )
            
            # Add summary metrics
            total_budget = pivot_df['Budget'].sum()
            total_expenses = pivot_df['Expenses'].sum()
            total_remaining = total_budget + total_expenses
            percentage_spent = (total_expenses / total_budget * 100) if total_budget > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Budget", f"{total_budget:,.0f}")
            col2.metric("Total Expenses", f"{total_expenses:,.0f}")
            col3.metric("Total Remaining", f"{total_remaining:,.0f}")
            col4.metric("Percentage Spent", f"{percentage_spent:.2f}%")
        else:
            st.info("No expense data found for the current month.")

if __name__ == "__main__":
    main()