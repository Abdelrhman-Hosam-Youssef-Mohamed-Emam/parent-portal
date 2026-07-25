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

st.markdown("""
    <div style="background-color: #fdfaf6; border-right: 4px solid #c9a878; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 1.8rem;">🚧</div>
        <div>
            <h4 style="margin: 0; color: #59695e; font-size: 1.1rem; font-weight: bold;">نسخة تجريبية (تحت التطوير)</h4>
            <p style="margin: 5px 0 0 0; color: #6b6b6b; font-size: 0.95rem; line-height: 1.5;">
                بوابة أولياء الأمور حالياً في مرحلة الإطلاق التجريبي. قد تواجه بعض الملاحظات أو الأخطاء التقنية البسيطة أثناء التصفح. نحن نعمل باستمرار على تحسين التجربة، <b>وسيتم حل هذه المشكلات قريباً.</b>
            </p>
        </div>
    </div>
""", unsafe_allow_html=True)

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