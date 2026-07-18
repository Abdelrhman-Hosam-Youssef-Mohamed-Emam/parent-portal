import streamlit as st
from auth import authenticate_user, login_user
from utils import image_to_base64
import os

st.markdown("<br><br>", unsafe_allow_html=True)

# تقسيم الصفحة لتوسيط محتوى تسجيل الدخول في المنتصف
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # عرض وتوسيط الشعار (اللوجو)
    if os.path.exists("assets/logo.png"):
        img_str = image_to_base64("assets/logo.png")
        st.markdown(
            f'<div style="text-align: center;"><img src="data:image/png;base64,{img_str}" width="120" style="margin-bottom: 20px;"></div>', 
            unsafe_allow_html=True
        )
    
    # نصوص الترحيب محاذاة في المنتصف بشكل آمن تماماً وبألوان الهوية المحددة
    st.markdown("<h3 style='text-align: center; color: #59695e; margin-bottom: 0;'>أهلًا بك في واحة الرضوان التعليمية</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6b6b6b; margin-top: 5px; margin-bottom: 25px;'>تسجيل الدخول لبوابة أولياء الأمور</p>", unsafe_allow_html=True)

    # نموذج تسجيل الدخول المنسق عبر الـ CSS المحدث
    with st.form("login_form"):
        phone_number = st.text_input("رقم الهاتف", placeholder="01XXXXXXXXX")
        password = st.text_input("كلمة المرور", type="password")
        
        submitted = st.form_submit_button("تسجيل الدخول", use_container_width=True)
        
        if submitted:
            if phone_number and password:
                user = authenticate_user(phone_number, password)
                if user:
                    login_user(user)
                    st.rerun()
                else:
                    st.error("رقم الهاتف أو كلمة المرور غير صحيحة.")
            else:
                st.warning("الرجاء إدخال رقم الهاتف وكلمة المرور.")