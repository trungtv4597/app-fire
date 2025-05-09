import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from psycopg2 import Error

from utils import init_connection, get_db_connection, release_connection, check_login

db_pool = init_connection()

# Fetch budget and expense data for the current month
def fetch_budget_data(user_id):
    conn = get_db_connection(db_pool)
    if conn:
        try:
            cur = conn.cursor()
            sql_query = """
            SELECT c.id as category_id, c.category_name,
                COALESCE(SUM(CASE WHEN t.action_id = 3 THEN t.amount ELSE 0 END), 0) AS budget,
                COALESCE(SUM(CASE WHEN t.action_id = 4 THEN t.amount ELSE 0 END), 0) AS total_expenses,
                COALESCE(SUM(CASE WHEN t.action_id = 3 THEN t.amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN t.action_id = 4 THEN t.amount ELSE 0 END), 0) AS remaining
            FROM fact_transaction AS t
            LEFT JOIN dim_category AS c ON c.id = t.category_id
            LEFT JOIN dim_user AS u ON u.id = t.user_id
            WHERE
            u.id = %s
            AND t.transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
            AND t.transaction_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            GROUP BY 1, 2
            HAVING SUM(CASE WHEN t.action_id = 3 THEN 1 ELSE 0 END) > 0
            """
            cur.execute(sql_query, (user_id,))
            results = cur.fetchall()
            cur.close()
            # Convert Decimal to float for Plotly compatibility
            return [(row[0], row[1], float(row[2]), float(row[3]), float(row[4])) for row in results]
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
    
    results = fetch_budget_data(user_id=st.session_state.user_id)
    
    if results:
        for _, category_name, budget, total_expenses, remaining in results:
            st.subheader(category_name)
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total_expenses,
                number={'suffix': " spent"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, max(budget, total_expenses)]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, budget * 0.7], 'color': "green"},
                        {'range': [budget * 0.7, budget * 0.9], 'color': "yellow"},
                        {'range': [budget * 0.9, budget], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': budget
                    }
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True, key=f"plotly_chart_{category_name}")
            
            # Display budget status
            if remaining >= 0:
                st.write(f"Budget: {budget:,.0f} | Remaining: {remaining:,.0f}")
            else:
                st.write(f"Budget: {budget:,.0f} | Over by: {-remaining:,.0f}")
    else:
        st.write("No budget categories found for the current month.")

if __name__ == "__main__":
    main()