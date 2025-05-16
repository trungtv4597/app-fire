import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px

from postgres_operator import PostgresOperator
from utils import init_connection, check_login

db_pool = init_connection()
db_operator = PostgresOperator(db_pool=db_pool)

def select_total_net_income(budget_som, user_id):
    """Function to fetch net income for the selected month"""
    results, error = db_operator.execute_select(
        'queries/select_total_net_income_by_period.sql', 
        (budget_som, user_id,)
        )
    if error:
        st.error(f"Failed to fetch data: {error}")
        return None
    return results[0]["net_income"] if results else None

def select_existing_budget_allocations(budget_som, user_id):
    results, error = db_operator.execute_select(
        'queries/select_existing_budget_allocations_by_period.sql', 
        (budget_som, user_id,)
        )
    if error:
        st.error(f"Failed to fetch data: {error}")
        return None
    return results

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

def insert_allocations(transaction_date, price, quantity, amount, category_id, user_id):
    cash_out_action_id = 3
    description = f"Allocation calucated from Price: {price} and Qty: {quantity}"
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_budget_allocations.sql",
        (transaction_date, description, amount, category_id, cash_out_action_id, user_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to insert budgets: {error}")
        return False
    return True

def update_allocations(transaction_id, price, quantity, amount):
    description = f"Updated the alloation with Price: {price} and Qty: {quantity}"
    inserted_rows, error = db_operator.execute_insert(
        "queries/update_budget_allocations.sql",
        (amount, description, transaction_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to update budgets: {error}")
        return False
    return True

# Initialize session state
def initialize_session_state():
    if "allocations" not in st.session_state:
        st.session_state.allocations = {}
    if "net_income" not in st.session_state:
        st.session_state.net_income = 0.0
    if "total_amount" not in st.session_state:
        st.session_state.total_amount = 0.0
    if 'data' not in st.session_state:
        st.session_state.data = []
        
def update_data(bucket_name, category_name, category_id, price, quantity, amount):
    """"""
    # Check if entry exists for this bucket_name and cat_name
    for entry in st.session_state.data:
        if entry['bucket_name'] == bucket_name and entry['category_name'] == category_name:
            # Update existing entry
            entry.update({
                'category_id': category_id,
                'price': price,
                'quantity': quantity,
                'amount': amount
            })
            return
    
    # If no existing entry, append new one
    st.session_state.data.append({
        'bucket_name': bucket_name,
        'category_name': category_name,
        'category_id': category_id, 
        'price': price,
        'quantity': quantity,
        'amount': amount
    })

def highlight_total(row):
    return ['background-color: #f0f0f0; font-weight: bold' if row['bucket_name'] == 'Grand Total' else '' for _ in row]

def calculate_total_amount():
    """Calculate the total allocated amount."""
    return sum(item['amount'] for item in st.session_state.data)

# UI component function
def render_category_input(bucket_name, cat_name, cat_id):
    """Render input fields for a category."""
    st.subheader(cat_name)
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input(
            "Price (VND)",
            min_value=0,
            format="%d",
            step=10000,
            key=f"price_{bucket_name}_{cat_name}"
        )
    with col2:
        quantity = st.number_input(
            "Quantity",
            min_value=0,
            format="%d",
            step=1,
            key=f"quantity_{bucket_name}_{cat_name}"
        )
    amount = price * quantity
    st.write(f"= {amount}")
    if price > 0 or quantity > 0:
        update_data(bucket_name, cat_name, cat_id, price, quantity, amount)

# Streamlit UI
def main():
    check_login()
    initialize_session_state()
    user_id = st.session_state.user_id
    user_name = st.session_state.username

    st.title(f"{user_name}, Budget Allocator")

    # Select budget month
    selected_date = st.date_input("Select Budget Month", value=datetime.now())
    budget_som = selected_date.replace(day=1)  # First day of the month

    # Fetch net income for the selected month
    net_income = select_total_net_income(budget_som, user_id)
    if net_income is None:
        st.error("Failed to fetch net income due to a database error.")
        return
    elif net_income == 0.0:
        st.error("No net income found for the selected month. Please submit your income statement first.")
        return
    else:
        st.write(f"Net Income for {budget_som.strftime('%B %Y')}: {net_income:,.0f} (VND)")
        st.session_state.net_income = net_income

    # Fetch current exisitng allocations
    existing_allocations = select_existing_budget_allocations(budget_som, user_id)

    # Create tabs for input and summary
    input_tab, summary_tab, statement_tab = st.tabs(["Input", "Summary", "Income Statement"])

    # Input tab with search
    with input_tab:
        st.header("by Category")
        search_term = st.text_input("Search Buckets", "")
        buckets = select_buckets()
        filtered_buckets = {k: v for k, v in buckets.items() if search_term.lower() in k.lower()}
        for bucket_name in filtered_buckets.keys():
            with st.expander(bucket_name, expanded=False):
                categories = select_categories(bucket_id=filtered_buckets.get(bucket_name), user_id=user_id)
                for cat_name in categories.keys():
                    cat_id = categories.get(cat_name)
                    render_category_input(bucket_name, cat_name, cat_id)

    # Display total allocated amount
    total_amount = calculate_total_amount()
    if total_amount > st.session_state.net_income:
        st.warning(f"Total allocated: {total_amount:,.0f} VND exceeds net income: {st.session_state.net_income:,.0f} VND.")
    else:
        percentage_used = (total_amount / st.session_state.net_income * 100) if st.session_state.net_income > 0 else 0
        st.success(f"Total allocated: {total_amount:,.0f} VND of {st.session_state.net_income:,.0f} VND ({percentage_used:.1f}%)")
        
    # Summary tab
    with summary_tab:
        st.header("Aggregation")

        if st.session_state.data:
            df = pd.DataFrame(st.session_state.data)
        else:
            st.warning("No data entered yet.")
            return
        
        # Section 1: Spreadsheet
        st.subheader("Overview")
        df_spreadsheet = df[["bucket_name", "category_name", "price", "quantity", "amount"]].copy()
        # Create a Grand Total row
        total_row = {
            'bucket_name': 'Grand Total',
            'category_name': "",
            'price': "",
            'quantity': 0,
            'amount': df_spreadsheet['amount'].sum()
        }
        df_spreadsheet = pd.concat([df_spreadsheet, pd.DataFrame([total_row])], ignore_index=True)
        
        df_spreadsheet['price'] = df_spreadsheet['price'].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
        df_spreadsheet['quantity'] = df_spreadsheet['quantity'].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
        df_spreadsheet['amount'] = df_spreadsheet['amount'].apply(lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x)
        st.dataframe(df_spreadsheet.style.apply(highlight_total, axis=1), use_container_width=True)

        # Section 2: Pie-chart
        st.subheader("Distribution")
        group_by = st.selectbox("Group by:", ['bucket_name', 'category_name'])
        df_pie = df.copy()
        pie_data = df_pie.groupby(group_by)['amount'].sum().reset_index()

        # Create pie chart with Plotly
        fig = px.pie(
            pie_data,
            values='amount',
            names=group_by,
            title=f'Amount by {group_by.replace("_", " ").title()}',
            hover_data=['amount'],
            labels={'amount': 'Total Amount (VND)'}
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True)
        
        # Display pie chart
        st.plotly_chart(fig, use_container_width=True)

    # Income Statement tab
    with statement_tab:
        st.header("Income Statement")

    # Submit button below tabs
    if st.button("Save Budget Allocations"):
        if st.checkbox("Check to Confirm"):
            current_category_ids = {item['category_id'] for item in existing_allocations}
            inserting_allocations = [item for item in st.session_state.data if item['category_id'] not in current_category_ids]
            for i in inserting_allocations:
                insert_allocations(
                    transaction_date=budget_som,
                    category_id=i.get("category_id"),
                    price=i.get("price"),
                    quantity=i.get("quantity"),
                    amount=i.get("amount"),
                    user_id=user_id,
                )

            new_category_ids = {item['category_id'] for item in st.session_state.data}
            updating_allocations = [item for item in existing_allocations if item['category_id'] in new_category_ids]
            for i in updating_allocations:
                transaction_id = i.get("transaction_id")
                category_id_ = i.get("category_id")
                for j in [item for item in st.session_state.data if item["category_id"] == category_id_]:
                    new_amount = j.get("amount")
                    new_price = j.get("price")
                    new_quantity = j.get("quantity")
                    update_allocations(transaction_id=transaction_id, amount=new_amount, price=new_price, quantity=new_quantity)

            st.success("Budget allocations saved successfully.")

if __name__ == "__main__":
    main()