from database import fetch_one
import streamlit as st

def authenticate_user(phone_number, password):
    """التحقق من بيانات ولي الأمر من الجدول الجديد"""
    query = """
        SELECT id, phone_number, password 
        FROM portal_auth.parents_login 
        WHERE phone_number = %s 
        LIMIT 1;
    """
    user = fetch_one(query, (phone_number,))
    
    # مقارنة الباسورد الذي أدخله المستخدم بالباسورد الموجود في الداتا بيز
    if user and user['password'] == password:
        return user
    return None

def login_user(user_data):
    st.session_state["authenticated"] = True
    st.session_state["user_phone"] = user_data["phone_number"] # حفظنا رقم التليفون هنا
    st.session_state["user_name"] = "ولي أمر"
    st.session_state["selected_student_id"] = None

def logout_user():
    st.session_state.clear()
    st.rerun()