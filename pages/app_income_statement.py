import streamlit as st
from datetime import datetime

from postgres_operator import PostgresOperator
from utils import init_connection, check_login

# Initialize database connection pool and operator
db_pool = init_connection()
db_operator = PostgresOperator(db_pool)

def select_categories_income(user_id):
    results, error = db_operator.execute_select(
        'queries/select_categories_income.sql', 
        (user_id,)
        )
    if error:
        st.error(f"Failed to fetch income categories: {error}")
        return {}
    return [(row['id'], row['name']) for row in results]

def select_category_id_by_name(category_name, user_id):
    results, error = db_operator.execute_select(
        'queries/select_category_id_by_name.sql', 
        (category_name, user_id,)
        )
    if error:
        st.error(f"Failed to fetch category_id: {error}")
        return None
    return results[0]["id"] if results else None

# Insert debt transaction into fact_transaction
def insert_debt_payments(transaction_date, amount, category_id, user_id):
    cash_out_action_id = 5
    description = "Maturity Debt Payment"
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_debt_payments.sql",
        (transaction_date, description, amount, category_id, cash_out_action_id, user_id)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to insert debt payments: {error}")
        return False
    return True

# Insert income record into fact_income
def insert_income_record(income_date, category_id, user_id, gross_income, paid_debt, net_income):
    inserted_rows, error = db_operator.execute_insert(
        "queries/insert_incomes.sql",
        (income_date, category_id, user_id, gross_income, paid_debt, net_income)
    )
    if inserted_rows <= 0:
        st.error(f"Failed to insert debt payments: {error}")
        return False
    return True

# Initialize session state
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

    st.title("Income Statement")

    # Init session state
    initialize_session_state()

    # Fetch data
    income_categories = select_categories_income(user_id)
    if not income_categories:
        st.error("No categories found under the Income bucket.")
        return
    emergency_category_id = select_category_id_by_name(category_name="Emergency", user_id=user_id)


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
                min_value=0,
                step=100000,
                value=0,
                key=f"gross_{cat_id}"
            )

        # Maturity debt input
        st.subheader("Maturity Debt")
        total_debt = st.number_input(
            "Total Maturity Debt for the Month",
            min_value=0,
            step=1000,
            value=0
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
            confirmed = st.form_submit_button("Confirm the Income Statement")

            if confirmed:
                # Store debt transaction
                if st.session_state.total_debt > 0:
                    if insert_debt_payments(
                        st.session_state.income_date,
                        st.session_state.total_debt,
                        emergency_category_id,
                        user_id
                    ):
                        pass
                    else:
                        return
            
                # Store income records
                for cat_id, gross_income, paid_debt, net_income in st.session_state.income_records:
                    if insert_income_record(
                        st.session_state.income_date,
                        cat_id,
                        user_id,
                        gross_income,
                        paid_debt,
                        net_income
                    ):
                        pass
                    else:
                        return
                
                st.success("Income statement saved successfully!")

                # Clear session state after saving
                st.session_state.income_records = []
                st.session_state.total_debt = 0.0
                st.session_state.income_date = None

if __name__ == "__main__":
    main()