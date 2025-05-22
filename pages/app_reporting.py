import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from postgres_operator import PostgresOperator
from utils import init_connection, check_login

# Initialize database connection pool and operator
db_pool = init_connection()
db_operator = PostgresOperator(db_pool)

# Fetch budget and expense data for the pivot table
def fetch_expense_data(user_id, selected_month):
    results, error = db_operator.execute_select(
        "queries/select_expense_data_by_period.sql",
        (user_id, selected_month, selected_month,)
    )
    if error:
        st.error(f"Database error: {error}")
        return []
    return [(row['bucket_name'], row['category_name'], row['action_name'], float(row['amount'])) for row in results]

def select_latest_transaction_date(user_id):
    results, error = db_operator.execute_select(
        'queries/select_latest_transaction_date.sql', 
        (user_id,)
    )
    if error:
        st.error(f"Failed to fetch data: {error}")
        return None
    return results[0]["latest_transaction_date"] if results else None

# Main Streamlit app
def main():
    check_login()

    user_id = st.session_state.user_id

    # Date selection for report filtering
    default_date = select_latest_transaction_date(user_id)
    selected_date = st.date_input("Select Report Month", value=default_date)
    selected_month = selected_date.replace(day=1)  # First day of the month
    month_str = selected_month.strftime('%B %Y')

    st.title(f"Budget Overview for {month_str}")

    # Create tabs for Expense and other placeholders
    expense_tab, _, _ = st.tabs(["Expense", "Balance Sheet", "FIRE"])

    # Expense Tab with Pivot Table
    with expense_tab:
        st.header("Expense Tracking")
        results = fetch_expense_data(user_id, selected_month)
        
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
            
            # Rename columns based on action names
            pivot_df.columns.name = None
            action_map = {name: name for name in pivot_df.columns[2:]}
            for col in pivot_df.columns[2:]:
                if 'cash-in' in col.lower():
                    action_map[col] = 'Budget'
                elif 'cash-out' in col.lower():
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
                (abs(pivot_df['Expenses']) / pivot_df['Budget']) * 100
            ).where(pivot_df['Budget'] > 0, 0)
            
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
            percentage_spent = (abs(total_expenses) / total_budget * 100) if total_budget > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Budget", f"{total_budget:,.0f}")
            col2.metric("Total Expenses", f"{total_expenses:,.0f}")
            col3.metric("Total Remaining", f"{total_remaining:,.0f}")
            col4.metric("Percentage Spent", f"{percentage_spent:.2f}%")
        else:
            st.info(f"No expense data found for {month_str}.")

if __name__ == "__main__":
    main()