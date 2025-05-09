# utils.py
import streamlit as st
from psycopg2 import pool
from psycopg2 import Error

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

def get_db_connection(db_pool):
    if db_pool is None:
        st.error("Connection pool not initialized!")
        return None
    return db_pool.getconn()

def release_connection(db_pool, conn):
    if db_pool is not None and conn is not None:
        db_pool.putconn(conn)


def check_login():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.error("Please log in to access this page.")
        st.switch_page("app.py")