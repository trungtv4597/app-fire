import streamlit as st
from utils import init_connection, get_db_connection, release_connection

db_pool = init_connection()

def verify_user(username, password):
    conn = get_db_connection(db_pool)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id as user_id, password FROM dim_user WHERE username = %s", (username,))
                result = cur.fetchone()
                if result:
                    user_id, comapring_password = result
                    if password == comapring_password:
                        return {"user_id": user_id, "username": username}
    finally:
        release_connection(db_pool, conn)
    return None

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None

# Set page title
st.title("Login Portal")

# Handle logged-in state
if st.session_state.logged_in:
    st.success(f"Welcome, {st.session_state.username}! Select an app from the sidebar.")
    
    # Logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = None
        st.rerun()

# Handle login form for non-logged-in users
else:
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")

        if submit:
            try:
                user_data = verify_user(username, password)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data["username"]
                    st.session_state.user_id = user_data["user_id"]
                    st.success("Login successful! Select an app from the sidebar.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception as e:
                st.error(f"Login failed: {str(e)}")