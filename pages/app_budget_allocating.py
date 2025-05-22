import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px

from postgres_operator import PostgresOperator
from utils import init_connection, check_login

db_pool = init_connection()
db_operator = PostgresOperator(db_pool=db_pool)

def select_total_net_income(budget_som, user_id):
    results, error = db_operator.execute_select(
        'queries/select_total_net_income_by_period.sql', 
        (budget_som, user_id,)
    )
    if error:
        st.error(f"Failed to fetch data: {error}")
        return None
    return results[0]["net_income"] if results else None

def select_latest_transaction_date(user_id):
    results, error = db_operator.execute_select(
        'queries/select_latest_transaction_date.sql', 
        (user_id,)
    )
    if error:
        st.error(f"Failed to fetch data: {error}")
        return None
    return results[0]["latest_transaction_date"] if results else None

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
    description = f"Allocation calculated from Price: {price} and Qty: {quantity}"
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_budget_allocations.sql",
        (transaction_date, description, amount, category_id, cash_out_action_id, user_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to insert budgets: {error}")
        return False
    return True

def update_allocations(transaction_id, price, quantity, amount):
    description = f"Updated the allocation with Price: {price} and Qty: {quantity}"
    inserted_rows, error = db_operator.execute_insert(
        "queries/update_budget_allocations.sql",
        (amount, description, transaction_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to update budgets: {error}")
        return False
    return True

def initialize_session_state():
    if "date" not in st.session_state:
        st.session_state.date = datetime.now()
    if "allocations" not in st.session_state:
        st.session_state.allocations = {}
    if "net_income" not in st.session_state:
        st.session_state.net_income = 0.0
    if "total_amount" not in st.session_state:
        st.session_state.total_amount = 0.0
    if 'data' not in st.session_state:
        st.session_state.data = []
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None

def update_data(bucket_name, category_name, category_id, price, quantity, amount):
    for entry in st.session_state.data:
        if entry['bucket_name'] == bucket_name and entry['category_name'] == category_name:
            entry.update({
                'category_id': category_id,
                'price': price,
                'quantity': quantity,
                'amount': amount
            })
            return
    st.session_state.data.append({
        'bucket_name': bucket_name,
        'category_name': category_name,
        'category_id': category_id, 
        'price': price,
        'quantity': quantity,
        'amount': amount
    })

# def calculate_total_amount():
#     return sum(item['amount'] for item in st.session_state.data)

def main():
    check_login()
    initialize_session_state()
    user_id = st.session_state.user_id

    st.title("Budget Allocator")

    # Select budget month
    st.session_state.date = select_latest_transaction_date(user_id)
    selected_date = st.date_input("Select Budget Month", value=st.session_state.date)
    budget_som = selected_date.replace(day=1)

    # Fetch net income
    net_income = select_total_net_income(budget_som, user_id)
    if net_income is None:
        st.error("Failed to fetch net income due to a database error.")
        return
    elif net_income == 0.0:
        st.error("No net income found for the selected month. Please submit your income statement first.")
        return
    else:
        st.write(f"Net Income for {budget_som.strftime('%B %Y')}: {net_income:,.0f} VND")
        st.session_state.net_income = net_income

    # Fetch existing allocations
    existing_allocations = select_existing_budget_allocations(budget_som, user_id)

    # Tabs for input and summary
    input_tab, summary_tab = st.tabs(["Input", "Summary"])

    with input_tab:
        st.header("Budget Allocation by Bucket")
        buckets = select_buckets()
        if not buckets:
            st.warning("No buckets available.")
            return

        # Create columns for buckets
        cols = st.columns(len(buckets))
        category_emojis = {
            "Rent": "🏠", "Apps": "📱", "Food": "🍽️", "Transport": "🚗", 
            "Entertainment": "🎬", "Savings": "💰", "Utilities": "💡"
        }  # Add more as needed

        for idx, (bucket_name, bucket_id) in enumerate(buckets.items()):
            with cols[idx]:
                st.subheader(bucket_name)
                categories = select_categories(bucket_id, user_id)
                for cat_name, cat_id in categories.items():
                    emoji = category_emojis.get(cat_name, "📌")
                    if st.button(f"{emoji} {cat_name}", key=f"{bucket_name}_{cat_name}"):
                        st.session_state.selected_category = (bucket_name, cat_name, cat_id)

        # Display input form for selected category
        if st.session_state.selected_category:
            bucket_name, cat_name, cat_id = st.session_state.selected_category
            st.write(f"### Input for {cat_name} in {bucket_name}")
            col1, col2 = st.columns(2)
            with col1:
                price = st.number_input("Price (VND)", min_value=0, step=10000, key=f"price_{cat_name}")
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, step=0.1, key=f"qty_{cat_name}")
            if price > 0 and quantity > 0:
                amount = price * quantity
                st.write(f"= {amount:,.0f}")
                if st.button("Save", key=f"save_{cat_name}"):
                    update_data(bucket_name, cat_name, cat_id, price, quantity, amount)
                    st.session_state.selected_category = None
                    st.success(f"Saved {amount:,.0f} VND for {cat_name}")

    with summary_tab:
        st.header("Summary")
        if st.session_state.data:
            df = pd.DataFrame(st.session_state.data)
            st.dataframe(df[["bucket_name", "category_name", "price", "quantity", "amount"]])
            total_amount = df["amount"].sum()
            if total_amount > net_income:
                st.warning(f"Total allocated: {total_amount:,.0f} VND exceeds net income: {net_income:,.0f} VND.")
            else:
                percentage_used = (float(total_amount) / float(net_income) * 100) if net_income > 0 else 0
                st.success(f"Total allocated: {total_amount:,.0f} VND of {net_income:,.0f} VND ({percentage_used:.1f}%)")

            # Pie chart
            pie_data = df.groupby('bucket_name')['amount'].sum().reset_index()
            fig = px.pie(pie_data, values='amount', names='bucket_name', title='Amount by Bucket')
            st.plotly_chart(fig)

            # Debug
            with st.expander('Session Raw Data', expanded=False):
                st.write(f"{st.session_state.data}")
        else:
            st.warning("No allocations entered yet.")

    # Save all allocations
    if st.button("Save All Allocations"):
        current_category_ids = {item['category_id'] for item in existing_allocations} if existing_allocations else set()
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
                update_allocations(
                    transaction_id=transaction_id, 
                    amount=new_amount, 
                    price=new_price, 
                    quantity=new_quantity
                    )
        st.success("All budget allocations saved successfully.")

if __name__ == "__main__":
    main()