import streamlit as st
from database import fetch_query
from datetime import date

# Enforce auth
if "authenticated" not in st.session_state:
    st.switch_page("pages/Login.py")

@st.cache_data(ttl=300)
def get_parent_children(phone_number):
    query = """
        SELECT 
            s.id, 
            s.full_name AS name, 
            s.parent_full_name,
            s.date_of_birth,
            s.nickname,
            s.child_pickup_person,
            s.notes AS admin_notes,
            s.hall_name,
            s.grade AS activity_name, 
            t.full_name AS teacher_name
        FROM students s
        LEFT JOIN student_teacher_links stl ON s.id = stl.student_id AND stl.is_primary = true
        LEFT JOIN teachers t ON stl.teacher_id = t.id
        WHERE s.parent_phone = %s
        ORDER BY s.full_name;
    """
    return fetch_query(query, (phone_number,))

def calculate_age(dob):
    if not dob:
        return "غير مسجل"
    try:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return f"{age} سنة"
    except:
        return "غير مسجل"

children = get_parent_children(st.session_state.get("user_phone", ""))

if children:
    parent_name = children[0].get('parent_full_name') or 'ولي الأمر'
    st.markdown(f"""
        <div style="background-color: #59695e; padding: 15px 20px; border-radius: 12px; margin-bottom: 25px;">
            <h3 style="color: white; margin: 0; font-size: 1.5rem;">👋 أهلاً بالسيد/ة: {parent_name}</h3>
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("لا يوجد أبناء مسجلين بهذا الرقم حالياً.")
    st.stop()

grouped_children = {}
for child in children:
    full_name = child.get('name', '')
    real_name = full_name.replace('-', '_').split('_')[0].strip()
    
    if real_name not in grouped_children:
        grouped_children[real_name] = {
            "fixed_info": {
                "dob": child.get('date_of_birth'),
                "nickname": child.get('nickname') or 'لا يوجد',
                "pickup": child.get('child_pickup_person') or 'غير محدد'
            },
            "activities": []
        }
    grouped_children[real_name]["activities"].append(child)

# رسم الواجهة باستخدام st.container(border=True) لعمل صندوق يجمع الطالب بأنشطته
for real_name, data in grouped_children.items():
    age_str = calculate_age(data["fixed_info"]["dob"])
    nickname = data["fixed_info"]["nickname"]
    pickup = data["fixed_info"]["pickup"]
    
    # هنا تم إضافة حدود للكونتينر ليجمع الاسم مع بطاقات الأنشطة
    with st.container(border=True):
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; border-bottom: 2px solid #c9a878; padding-bottom: 10px;">
                <div style="font-size: 40px;">👦</div>
                <div>
                    <h2 style="margin: 0; color: #2e3d38; font-weight: 800;">{real_name}</h2>
                    <p style="margin: 5px 0 0 0; color: #6b6b6b; font-size: 1.1rem;">
                        <b>العمر:</b> {age_str} &nbsp; | &nbsp; 
                        🏷️ <b>الاسم المستعار:</b> {nickname} &nbsp; | &nbsp; 
                        🚗 <b>مسموح له باستلام الطالب:</b> {pickup}
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # ضفنا enumerate عشان نطلع رقم تسلسلي (idx) لكل نشاط
        for idx, act in enumerate(data["activities"]):
            activity_name = act.get('activity_name') or 'غير محدد'
            teacher = act.get('teacher_name') or 'غير محدد'
            hall = act.get('hall_name') or 'غير محدد'
            admin_notes = act.get('admin_notes') or 'لا توجد ملاحظات'
            
            st.markdown(f"""
            <div style="background-color: #f8fcf9; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-right: 4px solid #59695e;">
                <h4 style="margin: 0 0 10px 0; color: #2e3d38; font-size: 1.2rem;">📚 {activity_name}</h4>
                <div style="color: #555; font-size: 1rem; line-height: 1.6;">
                    <span>👨‍🏫 <b>المعلم الأساسي:</b> {teacher}</span><br>
                    <span>🏛️ <b>القاعة:</b> {hall}</span><br>
                    <span>📝 <b>ملاحظات الإدارة:</b> {admin_notes}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # زر التفاصيل للنشاط
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # ضفنا الـ idx للـ key عشان نضمن إنه مستحيل يتكرر
                if st.button(f"عرض السجل اليومي ({activity_name})", key=f"view_{act['id']}_{idx}", use_container_width=True):
                    st.session_state["selected_student_id"] = act['id']
                    st.session_state["selected_activity"] = {
                        "real_name": real_name,
                        "activity_name": activity_name,
                        "teacher": teacher,
                        "hall": hall,
                        "notes": admin_notes
                    }
                    st.switch_page("pages/StudentDetails.py")