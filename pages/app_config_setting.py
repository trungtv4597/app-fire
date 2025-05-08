import streamlit as st
import psycopg2
from psycopg2 import Error, pool

# PostgreSQL connection
@st.cache_resource
def init_connection():
    secrets = st.secrets["postgres"]
    try:
        return psycopg2.pool.SimpleConnectionPool(
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
    
# Initialize connection pool
db_pool = init_connection()

# Get databse connection from pool
def get_db_connection():
    if db_pool is None:
        st.error("Connection pool not initialized!")
        return None
    return db_pool.getconn()

# Return connection to pool
def release_connection(conn):
    if db_pool is not None and conn is not None:
        db_pool.putconn(conn)

# Get buckets from dim_bucket
def get_buckets():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT bucket_name as name, id FROM dim_bucket ORDER BY 1")
                buckets = cur.fetchall()
                return {name: id for name, id in buckets}
        except Error as e:
            st.error(f"Failed to fetch buckets: {e}")
            return {}
        finally:
            release_connection(conn=conn)
    return {}

# Postgres operations
def insert_category(category_name, bucket_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dim_category (category_name, bucket_id)
                    VALUES (%s, %s)
                    """, (str(category_name), int(bucket_id))
                )
                conn.commit()
                return True
        except Error as e:
            st.error(f"Failed to insert category: {e}")
            conn.rollback()
            return False
        finally:
            release_connection(conn=conn)
    return False

# Streamlit UI
def main():
    st.title("Configuration Setting")
    st.header("Add New Category")

    # Get buckets
    bucket_dict = get_buckets()
    if not bucket_dict:
        st.warning("No buckets available. Please add buckets to the database.")
        return
    
    # Create aform for input and submission
    with st.form(key="category_form", clear_on_submit=True):
        selected_bucket = st.selectbox("select Bucket", bucket_dict.keys())
        category_name = st.text_input("New Category Name")
        
        submit_button = st.form_submit_button("Add Category")
        if submit_button:
            if not category_name:
                st.error("Please enter a category name.")
            else:
                if insert_category(category_name=category_name, bucket_id=bucket_dict.get(selected_bucket)):
                    st.success(f"Category <{category_name}> added successfully!")
                else:
                    pass

if __name__ == "__main__":
    main()