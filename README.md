# Introduction
* The Personal Finance App is designed to help users manage their monthly finances by providing tools to list income, pay debts, allocate budgets, record spending, and track balance.
* The app integrates with a [PostgreSQL](https://www.postgresql.org/) database to store and manage data, using [Streamlit](https://streamlit.io/) for an intuitive user interface.

# Core Features
1. **Income Statement**  
   Users input their *gross monthly income* by category (e.g., Salary, Maturity CDs) under the "Income" bucket through a dedicated form in `app_income_statement.py`. The app allows users to specify the month and input maturity debt, which is distributed proportionally across income streams based on their contribution to total gross income. The resulting *net income* (gross income minus allocated debt) is calculated and displayed for review.

2. **Maturity Debt Payment**  
   The app automatically deducts monthly debt obligations from the total income, as specified in the Income Statement. These debts originate from loans taken from the *Emergency Fund* bucket, a designated reserve for unexpected expenses. The app ensures that maturing debts are prioritized and paid before further budget allocation.

3. **Net Income Calculation**  
   After settling the maturing debt in the Income Statement, the remaining amount is calculated as the *Net Income* for each income stream. This represents the funds available for allocation to various budgets and expenses, stored individually to maintain clarity across multiple income sources.

4. **Budget Allocation**  
   Through `app_budget_allocating.py`, users can distribute their *Net Income* across different budget categories organized under buckets (e.g., Living Expenses, Savings, Entertainment). The app provides a user-friendly interface with expanders, tabs, and a pie chart to visualize allocations, ensuring users stay within their net income limits.

5. **Expense Tracking**  
   The `app_expense_submitting.py` module allows users to record every expense against the allocated budgets. Expenses are categorized by bucket, category, and location, and stored in the database with details such as transaction date, description, and amount. This helps users monitor spending and stay aligned with their budget plans.

The app also includes configuration settings (`app_config_setting.py`) to add categories and locations, and a reporting module (`app_reporting.py`) to provide insights through pivot tables and summary metrics. Together, these features empower users to take control of their personal finances with clarity and precision.

# Upgrade Logs

## v0.3.0: 16/05/2025
* **Introduced Postgres Operator Module**  
  - Implemented a new `PostgresOperator` class in `postgres_operator.py` to centralize all PostgreSQL database operations (SELECT, INSERT, DELETE) across the application.  
  - Moved SQL queries to individual `.sql` files stored in a `queries/` directory, enhancing modularity and making query management easier.  
  - Standardized database interaction by returning results in consistent formats: lists of dictionaries for SELECT queries and affected row counts for INSERT/DELETE operations.  
  - Centralized error handling within `PostgresOperator`, reducing code duplication in scripts like `app_income_statement.py`, `app_expense_submitting.py`, and `app_budget_allocating.py`. 

## v0.2.2: 14/05/2025
* `app_income_statement.py`: Added Income Statement Feature
    - Implemented a new app to manage *gross monthly income* by category under the "Income" bucket.
    - Added form to input income and maturity debt, with proportional debt distribution across income streams.
    - Separated calculation and saving processes, allowing users to review net income before confirming and saving to the database.
    - Stored debt as "CASH-IN" transactions in `fact_transaction` and income details (gross, debt, net) in a new `fact_income` table.

* `app_budget_allocating.py`: Enhanced Net Income Integration
    - Replaced manual `net income input` with automated retrieval from `fact_income` table based on user-selected month (`yyyy-mm`).
    - Added `date picker` for selecting budget month, aligning `transaction_date` with the first day of the selected month.

## v0.2.1: 13/05/2025
* `app.py`: Enhanced Navigation and Changelog
    - Implemented `button-based navigation` to access all app pages without sidebar.
    - Added `log` page to display upgrade logs from *README.md*.
    - Parsed and `rendered Markdown content` for versioned logs with expanders.
    - Adjusted default page after login to configurable setting (e.g., "Log" page).
    
* `app_reporting.py`: Added Pivot Table for Expense Tracking
    - Implemented `pivot table` in "Expense" tab to display budgets, expenses, remaining amounts, and percentage spent by bucket and category.
    - Added `summary metrics` for total budget, expenses, remaining, and percentage spent.

## v0.2.0: 12/05/2025
* `General`:
    - Implement `used-based` information for customized data filtering through all the app.
* `Budget Allocation`
    - Replaced adjustment sliders with `quotation-like input`, compacted input form layout.
    - Implement `expanders`.
    - Implement `tab` to separate input and summary sections.
    - Added bucket-level summary with `pie chart`.
    
## v0.1: Initial on 09/05/2025

#