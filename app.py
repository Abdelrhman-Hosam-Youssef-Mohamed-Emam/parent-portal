import streamlit as st
from utils import apply_global_styles
import config

st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles()

# Authentication Routing
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    # Unauthenticated: Only show login
    pages = [st.Page("pages/Login.py", title="تسجيل الدخول", url_path="login")]
    nav = st.navigation(pages)
    nav.run()
else:
    # Authenticated: Show Portal pages
    pages = [
        st.Page("pages/ParentHome.py", title="الرئيسية", url_path="home"),
        st.Page("pages/StudentDetails.py", title="تفاصيل الطالب", url_path="details")
    ]
    
    # Optional Sidebar for logout
    with st.sidebar:
        st.image("assets/logo.png", width=150)
        st.markdown(f"مرحباً بك، **{st.session_state['user_name']}**")
        if st.button("تسجيل الخروج"):
            from auth import logout_user
            logout_user()

    nav = st.navigation(pages)
    nav.run()