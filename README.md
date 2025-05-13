# Introduction
* The Personal Finance App is designed to help users manage their monthly finances by providing tools to list income, pay debts, allocate budgets, record spending, and track balance.
* The app integrates with a [PostgreSQL](https://www.postgresql.org/) database to store and manage data, using [Streamlit](https://streamlit.io/) for an intuitive user interface.

# Core Features
1. **Income Statement (Under Development)**  
   Users input their total monthly income through an income statement form. This serves as the starting point for financial planning, capturing all sources of income for the month.

2. **Maturity Debt Payment**  
   The app automatically deducts monthly debt obligations from the total income. These debts originate from loans taken from the *Emergency Fund* bucket, a designated reserve for unexpected expenses. The app ensures that maturing debts are prioritized and paid before further budget allocation.

3. **Net Income Calculation**  
   After settling the maturing debt, the remaining amount is calculated as the *Net Income*. This represents the funds available for allocation to various budgets and expenses.

4. **Budget Allocation**  
   Through `app_budget_allocating.py`, users can distribute their *Net Income* across different budget categories organized under buckets (e.g., Living Expenses, Savings, Entertainment). The app provides a user-friendly interface with expanders, tabs, and a pie chart to visualize allocations, ensuring users stay within their net income limits.

5. **Expense Tracking**  
   The `app_expense_submitting.py` module allows users to record every expense against the allocated budgets. Expenses are categorized by bucket, category, and location, and stored in the database with details such as transaction date, description, and amount. This helps users monitor spending and stay aligned with their budget plans.

The app also includes configuration settings (`app_config_setting.py`) to add categories and locations, and a reporting module (`app_reporting.py`) to provide insights through pivot tables and summary metrics. Together, these features empower users to take control of their personal finances with clarity and precision.

# Upgrade Logs

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