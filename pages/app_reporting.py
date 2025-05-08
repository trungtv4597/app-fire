import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from psycopg2 import Error, pool

# Initialize connection pool
@st.cache_resource
def init_connection():
    secrets = st.secrets["postgres"]
    try:
        return pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            dbname=secrets["DB_NAME"],
            user=secrets["DB_USER"],
            password=secrets["DB_PASSWORD"],
            host=secrets["DB_HOST"],
            port=secrets["DB_PORT"]
        )
    except Error as e:
        st.error(f"Error initializing connection pool: {e}")
        return None

db_pool = init_connection()

# Get database connection from pool
def get_db_connection():
    if db_pool is None:
        st.error("Connection pool not initialized!")
        return None
    return db_pool.getconn()

# Return connection to pool
def release_connection(conn):
    if db_pool is not None and conn is not None:
        db_pool.putconn(conn)

# Fetch budget and expense data for the current month
def fetch_budget_data():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            sql_query = """
            SELECT c.id as category_id, c.category_name,
                COALESCE(SUM(CASE WHEN t.action_id = 3 THEN t.amount ELSE 0 END), 0) AS budget,
                COALESCE(SUM(CASE WHEN t.action_id = 4 THEN t.amount ELSE 0 END), 0) AS total_expenses,
                COALESCE(SUM(CASE WHEN t.action_id = 3 THEN t.amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN t.action_id = 4 THEN t.amount ELSE 0 END), 0) AS remaining
            FROM dim_category c
            LEFT JOIN fact_transaction t ON c.id = t.category_id
            AND t.transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
            AND t.transaction_date < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            GROUP BY 1, 2
            HAVING SUM(CASE WHEN t.action_id = 3 THEN 1 ELSE 0 END) > 0
            """
            cur.execute(sql_query)
            results = cur.fetchall()
            cur.close()
            # Convert Decimal to float for Plotly compatibility
            return [(row[0], row[1], float(row[2]), float(row[3]), float(row[4])) for row in results]
        except Error as e:
            st.error(f"Database error: {e}")
            return []
        finally:
            release_connection(conn)
    return []

# Main Streamlit app
def main():
    st.title(f"Budget Overview for {datetime.now().strftime('%B %Y')}")
    
    results = fetch_budget_data()
    
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
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display budget status
            if remaining >= 0:
                st.write(f"Budget: {budget:,.0f} | Remaining: {remaining:,.0f}")
            else:
                st.write(f"Budget: {budget:,.0f} | Over by: {-remaining:,.0f}")
    else:
        st.write("No budget categories found for the current month.")

if __name__ == "__main__":
    main()