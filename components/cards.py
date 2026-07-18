import streamlit as st

def render_student_card(student):
    """
    تصميم بطاقة الطالب باستخدام HTML متصل لتجنب كسر Streamlit للتصميم،
    مع وضع زر التفاصيل بشكل أنيق تحت الكارت.
    """
    
    # 1. رسم البطاقة بالـ HTML ككتلة واحدة
    html_card = f"""
    <div style="
        background-color: white; 
        border-radius: 16px; 
        padding: 24px; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025); 
        border-top: 5px solid #c9a878; 
        border-right: 1px solid #efefef;
        border-left: 1px solid #efefef;
        border-bottom: 1px solid #efefef;
        display: flex; 
        align-items: center; 
        gap: 25px;
        margin-bottom: 10px;
    ">
        <div style="flex-shrink: 0;">
            <div style="width: 75px; height: 75px; border-radius: 50%; background-color: #fbfbfb; border: 2px solid #59695e; display: flex; align-items: center; justify-content: center; font-size: 32px; color: #59695e;">
                🎓
            </div>
        </div>
        <div style="flex-grow: 1;">
            <h3 style="margin: 0; color: #2e3d38; font-size: 1.5rem; font-weight: 700;">{student['name']}</h3>
            <div style="color: #6b6b6b; font-size: 1.05rem; margin-top: 10px; display: flex; flex-wrap: wrap; gap: 20px;">
                <span>📚 <b>الصف:</b> {student.get('grade_name') or 'غير محدد'}</span>
                <span>👨‍🏫 <b>المعلم:</b> {student.get('teacher_name') or 'غير محدد'}</span>
            </div>
        </div>
    </div>
    """
    
    # 2. تجميع البطاقة والزرار في Container واحد عشان يفضلوا ماسكين في بعض
    with st.container():
        st.markdown(html_card, unsafe_allow_html=True)
        
        # استخدمنا الأعمدة عشان الزرار ميبقاش واخد عرض الشاشة كلها ويبقى شكله غبي
        # كده الزرار هياخد الثلث اللي في النص بس ويبقى أشيك بكتير
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("عرض التفاصيل", key=f"view_{student['id']}", use_container_width=True):
                st.session_state["selected_student_id"] = student['id']
                st.switch_page("pages/StudentDetails.py")
        
        # مسافة أمان قبل الكارت اللي بعده
        st.markdown("<br>", unsafe_allow_html=True)