import streamlit as st
import re
import os

from utils import init_connection, get_db_connection, release_connection
# Import main functions from other apps
from pages.app_budget_allocating import main as budget_main
from pages.app_config_setting import main as config_main
from pages.app_reporting import main as reporting_main
from pages.app_expense_submitting import main as expense_main

db_pool = init_connection()

def verify_user(username, password):
    conn = get_db_connection(db_pool)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id as user_id, password FROM dim_user WHERE username = %s", (username,))
                result = cur.fetchone()
                if result:
                    user_id, comparing_password = result
                    if password == comparing_password:
                        return {"user_id": user_id, "username": username}
    finally:
        release_connection(db_pool, conn)
    return None

def get_log_from_readme(readme_path="README.md"):
    """
    Read the README.md file and extract the Changelog section.
    Returns the changelog content as a string or None if not found.
    """
    if not os.path.exists(readme_path):
        return None
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Regular expression to match version headers and their content
        # Matches '## vX.Y.Z: Title' or '## vX.Y: Title' followed by content until next '##' or '#'
        pattern = r'(##\s*v\d+\.\d+(?:\.\d+)?(?::\s*[^\n]*?\d{2}/\d{2}/\d{4})?\n)(.*?)(?=(##\s*v|#|\Z))'
        
        # Find all matches
        matches = re.finditer(pattern, content, re.DOTALL)
        
        # Store extracted logs
        upgrade_logs = []
        
        for match in matches:
            version_header = match.group(1).strip()
            content = match.group(2).strip()
            # Clean content: remove inline code backticks for cleaner display
            # content = re.sub(r'`([^`]+)`', r'\1', content)
            upgrade_logs.append({
                'version': version_header,
                'content': content
            })
        
        return upgrade_logs
    except Exception as e:
        st.error(f"Failed to read README.md: {str(e)}")
        return None


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"  # Default to login page

# Set page title
st.title("Personal Finance App")

# Navigation function to switch pages
def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()

def render_log_page():
    st.header("Upgrade Logs")
    logs = get_log_from_readme()
    if logs:
        # Use an expander for each version
        for log in logs:
            # Extract version number and title from header (e.g., "## v0.2: Upgrade" -> "v0.2: Upgrade")
            version_title = log['version'].replace('## ', '')
            with st.expander(version_title):
                if log['content']:
                    # Render content as markdown to preserve bullet points and formatting
                    st.markdown(log['content'])
                else:
                    st.write("No changes listed.")
    else:
        st.info("No changelog found in README.md !")

# Handle logged-in state
if st.session_state.logged_in:
    # Navigation buttons at the top
    st.subheader(f"Welcome, {st.session_state.username.upper()}!")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("Log"):
            navigate_to("log")
    with col2:
        if st.button("Expense"):
            navigate_to("expense")
    with col3:
        if st.button("Configs"):
            navigate_to("config")
    with col4:
        if st.button("Reporting"):
            navigate_to("reporting")
    with col5:
        if st.button("Budget"):
            navigate_to("budget")
    with col6:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = None
            st.session_state.current_page = "login"
            st.rerun()

    # Render the appropriate page based on current_page
    page_functions = {
    "log": render_log_page,
    "expense": expense_main,
    "config": config_main,
    "reporting": reporting_main,
    "budget": budget_main
    }

    # Call the function or show default message
    page_functions.get(st.session_state.current_page, lambda: st.write("Select an app to proceed."))()

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
                    st.session_state.current_page = "log"  # Default page after login
                    st.success("Login successful! Use the buttons above to navigate.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            except Exception as e:
                st.error(f"Login failed: {str(e)}")