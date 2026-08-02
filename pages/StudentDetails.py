import streamlit as st
import pandas as pd
from database import fetch_query
from datetime import datetime, timedelta
import json
import os
import gspread
from google.oauth2.service_account import Credentials

# ----------------- Fetch Configuration (Server or Local) -----------------
def get_config_value(key_name, is_required=True):
    """Smart function to fetch variables from DigitalOcean first, then from secrets.toml"""
    value = os.getenv(key_name)
    if not value:
        try:
            value = st.secrets[key_name]
        except (FileNotFoundError, KeyError):
            if is_required:
                st.error(f"🚨 المتغير `{key_name}` غير موجود في بيئة التشغيل أو ملف الأسرار.")
                st.stop()
            return None
    return value

# 1. Fetch the Sheet URL using the config function
SHEET_URL = get_config_value("SHEET_URL")

# ----------------- Connect to Google Sheets (Build JSON Dynamically) -----------------
@st.cache_data(ttl=600)
def get_sheet_data(sheet_url):
    """Function to connect to Google Sheets and compile auth data from variables"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Handle the private key (Convert \n strings to actual newlines)
        raw_private_key = get_config_value("GCP_PRIVATE_KEY")
        formatted_private_key = raw_private_key.replace('\\n', '\n')

        # Build the JSON dictionary from variables
        creds_dict = {
            "type": get_config_value("GCP_TYPE"),
            "project_id": get_config_value("GCP_PROJECT_ID"),
            "private_key_id": get_config_value("GCP_PRIVATE_KEY_ID"),
            "private_key": formatted_private_key,
            "client_email": get_config_value("GCP_CLIENT_EMAIL"),
            "client_id": get_config_value("GCP_CLIENT_ID"),
            "auth_uri": get_config_value("GCP_AUTH_URI"),
            "token_uri": get_config_value("GCP_TOKEN_URI"),
            "auth_provider_x509_cert_url": get_config_value("GCP_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": get_config_value("GCP_CLIENT_CERT_URL"),
            "universe_domain": get_config_value("GCP_UNIVERSE_DOMAIN")
        }

        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_url(sheet_url).sheet1
        return sheet.get_all_values()
        
    except Exception as e:
        st.error(f"⚠️ حدث خطأ أثناء الاتصال بجوجل شيت: {e}")
        return []

def extract_student_evaluations(sheet_values, target_code):
    """Updated smart algorithm to support the final weekly evaluation and the final text grade"""
    if not sheet_values or not target_code:
        return {}, {}, {}
    
    # 1. Dynamically find the "Code" column
    code_col_idx = 2
    for r_idx, row in enumerate(sheet_values[:10]):
        for c_idx, cell in enumerate(row):
            if str(cell).strip() == "الكود":
                code_col_idx = c_idx
                break
                
    # 2. Find the targeted student's row
    student_row = None
    for row in sheet_values:
        if len(row) > code_col_idx and str(row[code_col_idx]).strip() == str(target_code).strip():
            student_row = row
            break
            
    if not student_row:
        return {}, {}, {} 
        
    # 3. Extract only the evaluation cells (after the code column)
    evals = student_row[code_col_idx + 1:]
    
    eval_dict = {}
    weekly_eval_dict = {} 
    weekly_grade_dict = {} # New dictionary to store the final text grade
    
    current_date = datetime(2026, 7, 19) 
    col_idx = 0
    
    while col_idx < len(evals):
        # Handle weekends (Skip Friday and Saturday)
        if current_date.weekday() == 4: # Friday
            current_date += timedelta(days=2)
        elif current_date.weekday() == 5: # Saturday
            current_date += timedelta(days=1)
            
        week_num = int(current_date.strftime("%U"))
        
        if current_date.weekday() == 3: # Thursday
            # 1. Extract Thursday's column (Half day and recreation)
            chunk_size = 1
            block = evals[col_idx : col_idx + chunk_size]
            if not block:
                break
            
            val = str(block[0]).strip()
            if val:
                eval_dict[current_date.strftime("%Y-%m-%d")] = ["-", "-", "-", val]
                
            col_idx += chunk_size
            
            # 2. Extract the "Final Weekly Evaluation" (Numeric) column
            if col_idx < len(evals):
                w_eval = str(evals[col_idx]).strip()
                if w_eval:
                    weekly_eval_dict[week_num] = w_eval
                col_idx += 1 
                
            # 3. Extract the "Final Grade" (Text) column immediately after
            if col_idx < len(evals):
                w_grade = str(evals[col_idx]).strip()
                if w_grade:
                    weekly_grade_dict[week_num] = w_grade
                col_idx += 1 # Skip the grade column to proceed to the new week
                
            current_date += timedelta(days=1)
            
        else: # From Sunday to Wednesday
            chunk_size = 4
            block = evals[col_idx : col_idx + chunk_size]
            if not block:
                break 
                
            formatted_block = block + [""] * (4 - len(block))
            if any(str(cell).strip() for cell in formatted_block):
                eval_dict[current_date.strftime("%Y-%m-%d")] = formatted_block
                
            col_idx += chunk_size
            current_date += timedelta(days=1)
            
    return eval_dict, weekly_eval_dict, weekly_grade_dict

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

@st.cache_data(ttl=300)
def get_student_code(std_id):
    query = "SELECT student_code FROM students WHERE id = %s;"
    res = fetch_query(query, (std_id,))
    if res and len(res) > 0:
        if isinstance(res[0], dict):
            return res[0].get('student_code', '')
        elif isinstance(res[0], (tuple, list)):
            return res[0][0]
    return ""

attendance_data = get_attendance(student_id)
student_code = get_student_code(student_id)

# Fetch sheet data passing only the URL
sheet_values = get_sheet_data(SHEET_URL)
# Unpack all three dictionaries now
sheet_eval_dict, weekly_eval_dict, weekly_grade_dict = extract_student_evaluations(sheet_values, student_code)

# ----------------- Details Page Header -----------------
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

# ----------------- Tab Styling -----------------
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

# Merge dates: Combine attendance dates and sheet dates
records_by_date = {r['date']: r for r in attendance_data} if attendance_data else {}
sheet_dates = [datetime.strptime(ds, "%Y-%m-%d").date() for ds in sheet_eval_dict.keys()]

all_unique_dates = set(records_by_date.keys()) | set(sheet_dates)

if all_unique_dates:
    min_date = min(all_unique_dates)
    max_date = max(datetime.today().date(), max(all_unique_dates))
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

def build_row(d, record, sheet_evals):
    day_name = arabic_days[d.weekday()]
    date_str = d.strftime("%Y-%m-%d")
    
    # Use the calendar function considering Sunday as the start of the week
    week_num = int(d.strftime("%U"))
    
    # Extract daily evaluations
    eval_block = sheet_evals.get(date_str, ["", "", "", ""])
    p1 = str(eval_block[0]).strip() if str(eval_block[0]).strip() else "-"
    p2 = str(eval_block[1]).strip() if str(eval_block[1]).strip() else "-"
    p3 = str(eval_block[2]).strip() if str(eval_block[2]).strip() else "-"
    eval_notes = str(eval_block[3]).strip() if str(eval_block[3]).strip() else "-"

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

    # Return structured row data
    return {
        "اليوم": day_name,
        "التاريخ": date_str,
        "الحالة": status,
        "وقت الدخول": check_in,
        "وقت الخروج": check_out,
        "المعلم الأساسي": teacher_status,
        "المعلم البديل": sub_teacher,
        "ملاحظات الاستبدال": sub_note,
        "تقييم المحفظ": rating,
        "ملاحظات المحفظ": teacher_note,
        "تقييم الفترة الأولى": p1,
        "تقييم الفترة الثانية": p2,
        "تقييم الفترة الثالثة": p3,
        "ملاحظات المعلمين أو المشرفين": eval_notes,
        "month_sort": d.strftime("%Y-%m"),
        "week_sort": week_num
    }

if is_scheduled and all_unique_dates:
    current_date = min_date
    while current_date <= max_date:
        if current_date.weekday() in allowed_days or current_date in sheet_dates:
            record = records_by_date.get(current_date)
            df_data.append(build_row(current_date, record, sheet_eval_dict))
        current_date += timedelta(days=1)
else:
    for d in sorted(all_unique_dates):
        df_data.append(build_row(d, records_by_date.get(d), sheet_eval_dict))

# Alert Section
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
                
                # Hide index and apply styles
                styled_df = week_df.style.apply(highlight_status, axis=1).hide(axis="index")
                html_table = styled_df.to_html()
                
                # Render custom HTML table
                custom_html = (
                    '<div class="custom-table" style="direction: rtl; overflow-x: auto; border: 1px solid #e6e6e6; border-radius: 8px; margin-bottom: 20px; background-color: #ffffff;">'
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
                
                # --- Draw the combined weekly evaluation & final grade card ---
                w_eval = weekly_eval_dict.get(w)
                w_grade = weekly_grade_dict.get(w)
                
                # Only render the card if at least one metric exists for the week
                if w_eval or w_grade:
                    
                    # Clean and format the numeric score
                    formatted_score = "-"
                    if w_eval:
                        try:
                            score = float(w_eval)
                            formatted_score = f"{score:.1f}"
                        except ValueError:
                            formatted_score = w_eval
                    
                    final_grade_text = w_grade if w_grade else "-"
                    
                    # Avoid showing Excel calculation errors
                    if formatted_score not in ["!DIV/0!", "#DIV/0!"]:
                        
                        # HTML string with NO indentation to prevent Markdown code block rendering
                        card_html = f"""
<div style="background-color: #f8fcf9; border: 1px solid #c9a878; border-radius: 8px; padding: 20px; margin-bottom: 35px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px dashed #e6e6e6;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5rem;"></span>
            <span style="font-size: 1.15rem; color: #59695e; font-weight: bold;">متوسط التقييم الإسبوعي</span>
        </div>
        <div style="font-size: 1.3rem; color: #c9a878; font-weight: 900; background: #ffffff; padding: 5px 20px; border-radius: 6px; border: 1px solid #eee;">
            {formatted_score} <span style="font-size: 0.9rem; color: #aaa;">/ 10</span>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5rem;"></span>
            <span style="font-size: 1.15rem; color: #59695e; font-weight: bold;">التقدير النهائي</span>
        </div>
        <div style="font-size: 1.2rem; color: #2e3d38; font-weight: bold; background: #ffffff; padding: 5px 20px; border-radius: 6px; border: 1px solid #eee;">
            {final_grade_text}
        </div>
    </div>
</div>
"""
                        st.markdown(card_html, unsafe_allow_html=True)