import streamlit as st
import pandas as pd
from database import fetch_query
from datetime import datetime, timedelta
import json
import os

# Security Checks
if "authenticated" not in st.session_state:
    st.switch_page("pages/Login.py")

if not st.session_state.get("selected_student_id"):
    st.warning("الرجاء اختيار طالب أولاً.")
    if st.button("العودة للرئيسية"):
        st.switch_page("pages/ParentHome.py")
    st.stop()

student_id = st.session_state["selected_student_id"]
activity_info = st.session_state.get("selected_activity", {})

if st.button("← العودة للرئيسية"):
    st.session_state["selected_student_id"] = None
    st.switch_page("pages/ParentHome.py")

schedules = {}
if os.path.exists("schedules.json"):
    try:
        with open("schedules.json", "r", encoding="utf-8") as f:
            schedules = json.load(f)
    except:
        pass

@st.cache_data(ttl=300)
def get_attendance(std_id):
    query = """
        SELECT 
            a.date,
            a.check_in_time,
            a.check_out_time,
            a.rating,
            a.teacher_note,
            a.substitute_note,
            t_orig.full_name AS original_teacher_name,
            t_assig.full_name AS assigned_teacher_name,
            a.original_teacher_id,
            a.assigned_teacher_id
        FROM student_attendance_records a
        LEFT JOIN teachers t_orig ON a.original_teacher_id = t_orig.id
        LEFT JOIN teachers t_assig ON a.assigned_teacher_id = t_assig.id
        WHERE a.student_id = %s
        ORDER BY a.date ASC;
    """
    return fetch_query(query, (std_id,))

attendance_data = get_attendance(student_id)

# ----------------- هيدر صفحة التفاصيل -----------------
real_name = activity_info.get("real_name", "غير متوفر")
act_name = activity_info.get("activity_name", "غير متوفر")
teacher = activity_info.get("teacher", "غير متوفر")
hall = activity_info.get("hall", "غير متوفر")
notes = activity_info.get("notes", "لا توجد ملاحظات")

st.markdown(f"""
    <div style="background-color: #fcfcfc; padding: 20px; border-radius: 12px; border-top: 4px solid #c9a878; margin-bottom: 25px;">
        <h2 style="color: #2e3d38; margin-top: 0;">{real_name} - {act_name}</h2>
        <div style="display: flex; gap: 30px; flex-wrap: wrap; color: #59695e; font-size: 1.1rem;">
            <span>👨‍🏫 <b>المعلم الأساسي:</b> {teacher}</span>
            <span>🏛️ <b>القاعة:</b> {hall}</span>
        </div>
        <p style="margin-top: 10px; color: #6b6b6b; font-size: 1.05rem;">📝 <b>ملاحظات الإدارة:</b> {notes}</p>
    </div>
""", unsafe_allow_html=True)

# ----------------- تلوين التابات -----------------
st.markdown("""
    <style>
        div[data-testid="stTabs"] button[data-baseweb="tab"] p {
            color: #8c8c8c !important; 
            font-size: 1.2rem !important;
            font-weight: bold !important;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {
            color: #59695e !important; 
            font-size: 1.2rem !important;
            font-weight: 900 !important;
        }
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {
            background-color: #c9a878 !important; 
            height: 4px !important;
        }
    </style>
""", unsafe_allow_html=True)

df_data = []
arabic_days = {
    0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 
    4: "الجمعة", 5: "السبت", 6: "الأحد"
}
month_names = {
    "01": "يناير", "02": "فبراير", "03": "مارس", "04": "أبريل",
    "05": "مايو", "06": "يونيو", "07": "يوليو", "08": "أغسطس",
    "09": "سبتمبر", "10": "أكتوبر", "11": "نوفمبر", "12": "ديسمبر"
}
week_names = {
    1: "الأسبوع الأول", 2: "الأسبوع الثاني", 3: "الأسبوع الثالث", 
    4: "الأسبوع الرابع", 5: "الأسبوع الخامس", 6: "الأسبوع السادس"
}

records_by_date = {r['date']: r for r in attendance_data} if attendance_data else {}

if records_by_date:
    min_date = min(records_by_date.keys())
    max_date = max(datetime.today().date(), max(records_by_date.keys()))
else:
    min_date = datetime.today().date()
    max_date = datetime.today().date()

is_scheduled = False
allowed_days = []
for key, val in schedules.items():
    if key in act_name or act_name in key:
        is_scheduled = True
        allowed_days = val.get("allowed_days", [])
        break

def build_row(d, record):
    day_name = arabic_days[d.weekday()]
    date_str = d.strftime("%Y-%m-%d")
    
    # استخدام دالة التقويم التي تعتبر الأحد هو بداية الأسبوع الفعلي
    week_num = int(d.strftime("%U"))
    
    if record:
        status = "حاضر"
        check_in = record['check_in_time'].strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م") if record.get('check_in_time') else "-"
        check_out = record['check_out_time'].strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م") if record.get('check_out_time') else "-"

        orig_id = record.get('original_teacher_id')
        assig_id = record.get('assigned_teacher_id')
        assig_teacher = record.get('assigned_teacher_name') or "بديل غير معروف"
        
        teacher_status = "حاضر"
        sub_teacher = "-"
        sub_note = "-"
        
        if orig_id and assig_id and str(orig_id) != str(assig_id):
            teacher_status = "غائب"
            sub_teacher = assig_teacher
            sub_note = record.get('substitute_note') or "-"
        
        teacher_note = record.get('teacher_note') or "-"
        rating = str(record.get('rating')) if record.get('rating') is not None else "-"
        
    else:
        status = "غائب"
        check_in = check_out = teacher_status = sub_teacher = sub_note = teacher_note = rating = "-"

    return {
        "اليوم": day_name,
        "التاريخ": date_str,
        "الحالة": status,
        "وقت الدخول": check_in,
        "وقت الخروج": check_out,
        "المعلم الأساسي": teacher_status,
        "المعلم البديل": sub_teacher,
        "ملاحظات الاستبدال": sub_note,
        "ملاحظات المعلم": teacher_note,
        "التقييم": rating,
        "month_sort": d.strftime("%Y-%m"),
        "week_sort": week_num
    }

if is_scheduled and records_by_date:
    current_date = min_date
    while current_date <= max_date:
        if current_date.weekday() in allowed_days:
            record = records_by_date.get(current_date)
            df_data.append(build_row(current_date, record))
        current_date += timedelta(days=1)
else:
    for d in sorted(records_by_date.keys()):
        df_data.append(build_row(d, records_by_date[d]))

# alert
st.markdown("""
    <div style="background-color: #fffaf5; border-right: 4px solid #e6a23c; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="font-size: 1.2rem;">⚠️</span>
            <b style="color: #995e00; font-size: 1.1rem;">ملاحظة هامة حول سجل الحضور</b>
        </div>
        <p style="margin: 0; font-size: 0.95rem; color: #555; line-height: 1.6;">
            نظراً لحدوث بعض المشاكل التقنية المؤقتة أثناء تسجيل حضور الطلاب في واحة الرضوان، قد يظهر الطالب "غائباً" في بعض الأيام التي حضر فيها بالفعل، كما قد تلاحظ نقصاً في بعض بيانات الحضور والانصراف بسبب عدم اكتمال البيانات المركزية. نحن نتابع الأمر عن كثب، <b>وسيتم مراجعة السجلات وحل هذه المشكلة قريباً.</b>
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("### 📅 السجل اليومي الموحد")

if not df_data:
    st.info("لا توجد سجلات متاحة لعرضها حالياً.")
else:
    df = pd.DataFrame(df_data)
    months = sorted(df['month_sort'].unique(), reverse=True)
    tab_titles = [f"{month_names.get(m.split('-')[1], '')} {m.split('-')[0]}" for m in months]
    
    tabs = st.tabs(tab_titles)
    
    for i, tab in enumerate(tabs):
        with tab:
            month_df = df[df['month_sort'] == months[i]].drop(columns=['month_sort'])
            month_df = month_df.sort_values(by="التاريخ", ascending=True)

            def highlight_status(row):
                if row['الحالة'] == 'غائب':
                    return ['background-color: #fee2e2; color: #991b1b'] * len(row)
                return [''] * len(row)

            weeks_in_month = sorted(month_df['week_sort'].unique())
            
            for idx, w in enumerate(weeks_in_month, start=1):
                week_str = week_names.get(idx, f"الأسبوع {idx}")
                st.markdown(f"<h5 style='color: #c9a878; margin-top: 20px;'>🎯 {week_str}</h5>", unsafe_allow_html=True)
                
                week_df = month_df[month_df['week_sort'] == w].drop(columns=['week_sort'])
                
                # إخفاء الـ index وتطبيق الألوان
                styled_df = week_df.style.apply(highlight_status, axis=1).hide(axis="index")
                html_table = styled_df.to_html()
                
                # تجميع الـ HTML ككتلة واحدة بدون مسافات أو أسطر عشان Streamlit ميعتبرهوش نص عادي
                custom_html = (
                    '<div class="custom-table" style="direction: rtl; overflow-x: auto; border: 1px solid #e6e6e6; border-radius: 8px; margin-bottom: 25px; background-color: #ffffff;">'
                    '<style>'
                    '.custom-table table { width: 100%; border-collapse: collapse; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; font-size: 0.95rem; } '
                    '.custom-table th, .custom-table td { padding: 12px 15px; text-align: right !important; border-bottom: 1px solid #eee; white-space: nowrap; } '
                    '.custom-table thead th { background-color: #f8fcf9 !important; color: #59695e !important; font-weight: bold; border-bottom: 2px solid #c9a878 !important; } '
                    '.custom-table tbody tr:hover td { background-color: #f1f5f2 !important; }'
                    '</style>'
                    f'{html_table}'
                    '</div>'
                )
                
                st.markdown(custom_html, unsafe_allow_html=True)