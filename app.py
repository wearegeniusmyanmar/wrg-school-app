import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import os

st.set_page_config(
    page_title="We Are Genius - Basic Science School",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Bright, Clean & Luxury Light Theme (Emerald + Pearl White) -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Padauk:wght@400;700&display=swap');

    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1350px;
    }
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Padauk', sans-serif;
    }

    /* Crisp, Bright, Clean Emerald-White Background (No Blues) */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #ecfdf5 50%, #f0fdf4 100%);
        color: #0f172a;
    }

    /* Minimalist Login Card without unnecessary surrounding boxes 
    .login-container-clean {
       # background: #ffffff;
       # border: 1.5px solid rgba(16, 185, 129, 0.3);
        border-radius: 28px;
        padding: 30px 40px 40px 40px;
        box-shadow: 0 20px 45px -10px rgba(16, 185, 129, 0.15), 0 4px 15px rgba(0, 0, 0, 0.05);
        margin: 20px auto;
        max-width: 480px;
        text-align: center;
    }*/

    /* Clean Bright Typography */
    .brand-title-large {
        font-family: 'Cinzel', serif;
        font-size: 2.5rem;
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(120deg, #059669 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 10px;
        margin-bottom: 2px;
        line-height: 1.15;
    }

    .brand-subtitle-large {
        font-size: 1.25rem;
        font-weight: 800;
        color: #1e293b;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .app-badge-large {
        display: inline-block;
        background: #d1fae5;
        color: #065f46;
        font-size: 0.88rem;
        font-weight: 700;
        padding: 6px 18px;
        border-radius: 20px;
        border: 1px solid rgba(16, 185, 129, 0.4);
        letter-spacing: 0.5px;
        margin-bottom: 20px;
    }

    /* Clean Bright Header Bar */
    .app-top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #ffffff;
        border: 1.5px solid rgba(16, 185, 129, 0.25);
        border-radius: 20px;
        padding: 16px 28px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
    }

    /* Light Theme Metric Cards */
    .stat-card {
        background: #ffffff;
        border: 1.5px solid rgba(16, 185, 129, 0.25);
        border-radius: 18px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.08);
        transition: all 0.3s ease;
    }
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: #10b981;
        box-shadow: 0 12px 25px rgba(16, 185, 129, 0.18);
    }
    .stat-val {
        font-size: 2.5rem;
        font-weight: 900;
        color: #059669;
        margin: 6px 0;
    }
    .stat-label {
        font-size: 0.95rem;
        font-weight: 700;
        color: #64748b;
    }

    /* Bright Clean Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(16, 185, 129, 0.2);
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #64748b;
        font-weight: 600;
        padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #10b981 !important;
        color: #ffffff !important;
        font-weight: 700;
    }

    /* Forms & Tables Enhancement for Light Mode */
    .stTextInput input, .stSelectbox select, .stDateInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
    }
    div[data-testid="stExpander"] {
        border-radius: 14px;
        border: 1px solid rgba(16, 185, 129, 0.2);
        background-color: #ffffff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "wrg_school_system.db"

# ----------------- Database Setup -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Teacher_Name TEXT NOT NULL UNIQUE,
            Phone TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Level TEXT NOT NULL,
            Lesson_Topic TEXT NOT NULL,
            UNIQUE(Level, Lesson_Topic)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Student_Name TEXT NOT NULL,
            Age INTEGER,
            Class_Type TEXT NOT NULL,
            Class_Name TEXT NOT NULL,
            Parent_Name TEXT,
            Phone TEXT,
            Social_Account TEXT,
            Address TEXT,
            UNIQUE(Student_Name, Class_Type, Class_Name)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT NOT NULL,
            Class_Type TEXT NOT NULL,
            Class_Name TEXT NOT NULL,
            Period TEXT NOT NULL,
            Zoom_ID TEXT,
            Teacher_Name TEXT NOT NULL,
            Assistant_1 TEXT,
            Assistant_2 TEXT,
            Lesson_Level TEXT NOT NULL,
            Lesson_Topic TEXT NOT NULL,
            UNIQUE(Date, Class_Type, Class_Name, Period)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT NOT NULL,
            Class_Type TEXT NOT NULL,
            Class_Name TEXT NOT NULL,
            Student_Name TEXT NOT NULL,
            Phone TEXT,
            Status TEXT NOT NULL,
            UNIQUE(Date, Class_Type, Class_Name, Student_Name)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ----------------- DB Helpers -----------------
def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

@st.dialog("🔔 အသိပေးချက် (Notification)")
def show_popup(message, details=""):
    st.success(message)
    if details:
        st.info(details)
    if st.button("အိုကေ (OK)", type="primary", use_container_width=True):
        st.rerun()

# ----------------- EDIT DIALOG MODALS -----------------
@st.dialog("✏️ အချိန်ဇယား ပြင်ဆင်ရန်")
def edit_timetable_dialog(row_id):
    row = run_query("SELECT * FROM timetable WHERE id = ?", (row_id,)).iloc[0]
    teachers = run_query("SELECT Teacher_Name FROM teachers")["Teacher_Name"].tolist()
    levels = run_query("SELECT DISTINCT Level FROM lessons")["Level"].tolist()
    
    e_date = st.text_input("ရက်စွဲ (YYYY-MM-DD)", value=str(row['Date']))
    e_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, index=CLASS_TYPES.index(row['Class_Type']) if row['Class_Type'] in CLASS_TYPES else 0)
    e_class = st.text_input("တန်းခွဲ", value=str(row['Class_Name']))
    e_period = st.text_input("စာသင်ချိန်", value=str(row['Period']))
    e_zoom = st.text_input("Zoom ID / Link", value=str(row['Zoom_ID']) if pd.notna(row['Zoom_ID']) else "")
    
    t_idx = teachers.index(row['Teacher_Name']) if row['Teacher_Name'] in teachers else 0
    e_t = st.selectbox("Lead Teacher", teachers, index=t_idx) if teachers else st.text_input("Lead Teacher", value=row['Teacher_Name'])
    
    asst_opts = ["မရှိပါ"] + teachers
    a1_idx = asst_opts.index(row['Assistant_1']) if row['Assistant_1'] in asst_opts else 0
    a2_idx = asst_opts.index(row['Assistant_2']) if row['Assistant_2'] in asst_opts else 0
    e_a1 = st.selectbox("Assistant 1", asst_opts, index=a1_idx)
    e_a2 = st.selectbox("Assistant 2", asst_opts, index=a2_idx)
    
    l_idx = levels.index(row['Lesson_Level']) if row['Lesson_Level'] in levels else 0
    e_lvl = st.selectbox("Level ရွေးပါ", levels, index=l_idx) if levels else None
    
    if e_lvl:
        lessons = run_query("SELECT Lesson_Topic FROM lessons WHERE Level = ?", (e_lvl,))["Lesson_Topic"].tolist()
        lsn_idx = lessons.index(row['Lesson_Topic']) if row['Lesson_Topic'] in lessons else 0
        e_top = st.selectbox("Lesson ရွေးပါ", lessons, index=lsn_idx) if lessons else None
    else:
        e_top = None
    
    if st.button("💾 ပြင်ဆင်မှု သိမ်းဆည်းမည်", type="primary", use_container_width=True):
        if e_lvl and e_top:
            execute_query('''
                UPDATE timetable 
                SET Date=?, Class_Type=?, Class_Name=?, Period=?, Zoom_ID=?, Teacher_Name=?, Assistant_1=?, Assistant_2=?, Lesson_Level=?, Lesson_Topic=?
                WHERE id=?
            ''', (e_date, e_type, e_class, e_period, e_zoom, e_t, 
                  None if e_a1 == "မရှိပါ" else e_a1, 
                  None if e_a2 == "မရှိပါ" else e_a2, 
                  e_lvl, e_top, row_id))
            st.rerun()
        else:
            st.error("Level နှင့် Lesson အချက်အလက်များ မပြည့်စုံပါ။")

@st.dialog("✏️ ကျောင်းသား အချက်အလက် ပြင်ဆင်ရန်")
def edit_student_dialog(row_id):
    row = run_query("SELECT * FROM students WHERE id = ?", (row_id,)).iloc[0]
    with st.form("edit_stu_form"):
        e_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, index=CLASS_TYPES.index(row['Class_Type']) if row['Class_Type'] in CLASS_TYPES else 0)
        e_class = st.text_input("တန်းခွဲ", value=str(row['Class_Name']))
        e_name = st.text_input("ကျောင်းသား အမည်", value=str(row['Student_Name']))
        e_age = st.number_input("အသက်", min_value=3, max_value=80, value=int(row['Age']) if pd.notna(row['Age']) else 15)
        e_parent = st.text_input("မိဘ အမည်", value=str(row['Parent_Name']) if pd.notna(row['Parent_Name']) else "")
        e_phone = st.text_input("ဖုန်းနံပါတ်", value=str(row['Phone']) if pd.notna(row['Phone']) else "")
        e_social = st.text_input("မိဘ Social အကောင့်", value=str(row['Social_Account']) if pd.notna(row['Social_Account']) else "")
        e_address = st.text_area("လိပ်စာ", value=str(row['Address']) if pd.notna(row['Address']) else "")
        
        if st.form_submit_button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
            execute_query('''
                UPDATE students 
                SET Class_Type=?, Class_Name=?, Student_Name=?, Age=?, Parent_Name=?, Phone=?, Social_Account=?, Address=?
                WHERE id=?
            ''', (e_type, e_class, e_name, e_age, e_parent, e_phone, e_social, e_address, row_id))
            st.rerun()

@st.dialog("✏️ ဆရာ/မ အချက်အလက် ပြင်ဆင်ရန်")
def edit_teacher_dialog(row_id):
    row = run_query("SELECT * FROM teachers WHERE id = ?", (row_id,)).iloc[0]
    with st.form("edit_teach_form"):
        e_name = st.text_input("ဆရာ/မ အမည်", value=str(row['Teacher_Name']))
        e_phone = st.text_input("ဖုန်းနံပါတ်", value=str(row['Phone']) if pd.notna(row['Phone']) else "")
        if st.form_submit_button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
            execute_query("UPDATE teachers SET Teacher_Name=?, Phone=? WHERE id=?", (e_name, e_phone, row_id))
            st.rerun()

@st.dialog("✏️ သင်ခန်းစာ ပြင်ဆင်ရန်")
def edit_lesson_dialog(row_id):
    row = run_query("SELECT * FROM lessons WHERE id = ?", (row_id,)).iloc[0]
    with st.form("edit_lsn_form"):
        e_lvl = st.text_input("Level", value=str(row['Level']))
        e_top = st.text_input("Lesson Topic", value=str(row['Lesson_Topic']))
        if st.form_submit_button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
            execute_query("UPDATE lessons SET Level=?, Lesson_Topic=? WHERE id=?", (e_lvl, e_top, row_id))
            st.rerun()

# ----------------- SESSION AUTHENTICATION -----------------
CLASS_TYPES = ["ကိုယ်ပိုင်ကျောင်းများ", "On Campus", "Zoom Online"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

# ================= CLEAN BRIGHT LOGIN PAGE =================
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.4, 1])
    
    with center_col:
        st.markdown('<div class="login-container-clean">', unsafe_allow_html=True)
        
        # 1. Direct Clean Logo (No boxes/shapes above or around it)
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            l_col1, l_col2, l_col3 = st.columns([1, 1.4, 1])
            with l_col2:
                st.image(logo_path, use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; margin:0;'>🔬</h1>", unsafe_allow_html=True)
            
        # 2. Prominent Emerald Typography
        st.markdown("""
            <div class="brand-title-large">WE ARE GENIUS</div>
            <div class="brand-subtitle-large">Basic Science School</div>
            <div class="app-badge-large">School Management Application</div>
        """, unsafe_allow_html=True)
        
        # 3. Clean White Form
        with st.form("clean_login_form"):
            role_choice = st.selectbox("အသုံးပြုသူ အမျိုးအစား (Role)", ["Teacher (ဆရာ/မ)", "Admin (စီမံခန့်ခွဲသူ)"])
            password = st.text_input("စကားဝှက် (Password)", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("🚀 စနစ်သို့ ဝင်ရောက်မည် (Sign In)", type="primary", use_container_width=True)

            if submit_btn:
                if role_choice == "Admin (စီမံခန့်ခွဲသူ)" and password == "693039996":
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.rerun()
                elif role_choice == "Teacher (ဆရာ/မ)" and password == "Wrg7799332211":
                    st.session_state.logged_in = True
                    st.session_state.role = "Teacher"
                    st.rerun()
                else:
                    st.error("စကားဝှက် မှားယွင်းနေပါသည်။")
                    
        st.markdown('</div>', unsafe_allow_html=True)
        #st.caption("<p style='text-align: center; color: #64748b; font-weight:600;'>Admin: admin123 | Teacher: teacher123</p>", unsafe_allow_html=True)
    st.stop()

# ================= SIDEBAR PROFILE =================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    st.markdown("### **We Are Genius**")
    st.caption("Basic Science School")
    st.success(f"👤 Role: **{st.session_state.role}**")

# ================= TOP HEADER WITH SINGLE LOGOUT BUTTON =================
h_col1, h_col2, h_col3 = st.columns([1, 6.5, 1.8])
with h_col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=75)
with h_col2:
    st.markdown("""
        <h2 style='margin:0; font-family:Cinzel, serif; font-weight:900; color:#059669; letter-spacing:1px;'>WE ARE GENIUS - BASIC SCIENCE SCHOOL</h2>
        <p style='margin:0; font-weight:700; color:#0d9488; font-size:1.02rem;'>School Management & Academic Timetable System</p>
    """, unsafe_allow_html=True)
with h_col3:
    st.write("")
    if st.button("🚪 Logout (ထွက်မည်)", key="single_header_logout_btn", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

st.markdown("---")

# Dynamic Tabs based on Role
if st.session_state.role == "Admin":
    tab_names = [
        "📅 အပတ်စဉ် အချိန်ဇယား ရှာဖွေရန်",
        "➕ အချိန်ဇယား ရေးဆွဲ/စီမံရန်",
        "👥 ကျောင်းသား စီမံခန့်ခွဲမှု",
        "📋 နေ့စဉ် ကျောင်းခေါ်ချိန် မှတ်တမ်း",
        "📊 အင်အားနှင့် တက်/ပျက် စာရင်းချုပ်",
        "👨‍🏫 ဆရာ/မ စာရင်း စီမံရန်",
        "📖 သင်ခန်းစာများ စီမံရန်",
        "📈 Analytics Dashboard"
    ]
else:
    tab_names = [
        "📅 အပတ်စဉ် အချိန်ဇယား ရှာဖွေရန်",
        "📋 နေ့စဉ် ကျောင်းခေါ်ချိန် မှတ်တမ်း",
        "📊 အင်အားနှင့် တက်/ပျက် စာရင်းချုပ်"
    ]

tabs = st.tabs(tab_names)

# ================= TAB 1: VIEW TIMETABLE =================
with tabs[0]:
    st.subheader("🔍 အပတ်စဉ် အချိန်ဇယား ရှာဖွေကြည့်ရှုရန်")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        view_type = st.selectbox("ကျောင်းအမျိုးအစား", ["အားလုံး"] + CLASS_TYPES, key="v_t_filter")
    with c2:
        t_list = ["အားလုံး"] + sorted(run_query("SELECT DISTINCT Teacher_Name FROM teachers")["Teacher_Name"].tolist())
        view_t = st.selectbox("ဆရာ/မ အမည်", t_list, key="v_t_name")
    with c3:
        start_w = st.date_input("စတင်မည့်ရက်", date.today() - timedelta(days=date.today().weekday()), key="v_s_date")
    with c4:
        end_w = st.date_input("ပြီးဆုံးမည့်ရက်", start_w + timedelta(days=6), key="v_e_date")

    q = "SELECT Date, Class_Type, Class_Name, Period, Zoom_ID, Teacher_Name, Assistant_1, Assistant_2, Lesson_Level, Lesson_Topic FROM timetable WHERE Date BETWEEN ? AND ?"
    p = [start_w.strftime("%Y-%m-%d"), end_w.strftime("%Y-%m-%d")]
    
    if view_type != "အားလုံး":
        q += " AND Class_Type = ?"
        p.append(view_type)
    if view_t != "အားလုံး":
        q += " AND (Teacher_Name = ? OR Assistant_1 = ? OR Assistant_2 = ?)"
        p.extend([view_t, view_t, view_t])
        
    q += " ORDER BY Date ASC, Period ASC"
    res = run_query(q, tuple(p))
    
    if not res.empty:
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.info("ရွေးချယ်ထားသော ရက်အတွင်း အချိန်ဇယား မရှိသေးပါ။")

# ================= ADMIN SECTIONS =================
if st.session_state.role == "Admin":
    
    # --- MANAGE TIMETABLE ---
    with tabs[1]:
        st.subheader("➕ အချိန်ဇယား အသစ်ထည့်သွင်းရန်")
        
        teachers = run_query("SELECT Teacher_Name FROM teachers")["Teacher_Name"].tolist()
        levels_df = run_query("SELECT DISTINCT Level FROM lessons ORDER BY Level")
        levels_avail = levels_df["Level"].tolist() if not levels_df.empty else []

        if not levels_avail:
            st.warning("⚠️ သင်ခန်းစာ Level များ မရှိသေးပါ။ ဦးစွာ 'သင်ခန်းစာများ စီမံရန်' Tab တွင် သင်ခန်းစာများ ထည့်သွင်းပေးပါ။")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                in_date = st.date_input("ရက်စွဲ (Date)", date.today(), key="adm_in_date").strftime("%Y-%m-%d")
                in_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, key="adm_in_type")
                in_class = st.text_input("တန်းခွဲ (ဥပမာ - WRG 26_01 (Tue_Wed:6-7)", key="adm_in_class")
                in_period = st.text_input("စာသင်ချိန် (ဥပမာ - 9:00 AM - 10:30 AM)", key="adm_in_period")
            with c2:
                in_zoom = st.text_input("Zoom ID / Link", key="adm_in_zoom")
                in_t = st.selectbox("Lead Teacher", ["ရွေးချယ်ပါ"] + teachers, key="adm_in_t")
                in_a1 = st.selectbox("Assistant 1", ["မရှိပါ"] + teachers, key="adm_in_a1")
                in_a2 = st.selectbox("Assistant 2", ["မရှိပါ"] + teachers, key="adm_in_a2")
            with c3:
                in_lvl = st.selectbox("Level ရွေးချယ်ပါ", levels_avail, key="adm_in_lvl")
                lessons_under_level = run_query("SELECT Lesson_Topic FROM lessons WHERE Level = ? ORDER BY id", (in_lvl,))["Lesson_Topic"].tolist()
                in_top = st.selectbox("သင်ကြားရမည့် သင်ခန်းစာ (Lesson)", lessons_under_level if lessons_under_level else ["သင်ခန်းစာမရှိပါ"], key="adm_in_top")

            if st.button("💾 အချိန်ဇယား သိမ်းဆည်းမည်", type="primary", key="adm_save_tt"):
                if in_class and in_t != "ရွေးချယ်ပါ" and in_period and in_top != "သင်ခန်းစာမရှိပါ":
                    try:
                        execute_query('''
                            INSERT INTO timetable 
                            (Date, Class_Type, Class_Name, Period, Zoom_ID, Teacher_Name, Assistant_1, Assistant_2, Lesson_Level, Lesson_Topic) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (in_date, in_type, in_class, in_period, in_zoom, in_t, 
                              None if in_a1 == "မရှိပါ" else in_a1, 
                              None if in_a2 == "မရှိပါ" else in_a2, 
                              in_lvl, in_top))
                        show_popup("အချိန်ဇယား အသစ် ထည့်သွင်းပြီးပါပြီ!")
                    except sqlite3.IntegrityError:
                        st.error("ယခု ရက်စွဲ၊ အတန်းနှင့် စာသင်ချိန်အတွက် ရှိပြီးသား ဖြစ်နေပါသည်။")
                else:
                    st.warning("အချက်အလက်များကို ပြည့်စုံစွာ ဖြည့်ပေးပါ။")

        st.markdown("---")
        st.subheader("📂 အချိန်ဇယား Excel မှ Import ပြုလုပ်ရန်")
        up_tt = st.file_uploader("Excel တင်ရန် (Columns: Date, Class_Type, Class_Name, Period, Zoom_ID, Teacher_Name, Assistant_1, Assistant_2, Lesson_Level, Lesson_Topic)", type=["xlsx", "xls"], key="adm_up_tt")
        if up_tt and st.button("📥 အချိန်ဇယား Import စတင်မည်"):
            try:
                imp_df = pd.read_excel(up_tt)
                req = {"Date", "Class_Type", "Class_Name", "Period", "Teacher_Name", "Lesson_Level", "Lesson_Topic"}
                if req.issubset(set(imp_df.columns)):
                    imp_df['Date'] = imp_df['Date'].astype(str)
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    ins, skp = 0, 0
                    for _, r in imp_df.iterrows():
                        try:
                            c.execute('''INSERT INTO timetable 
                                         (Date, Class_Type, Class_Name, Period, Zoom_ID, Teacher_Name, Assistant_1, Assistant_2, Lesson_Level, Lesson_Topic) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                      (str(r['Date']), str(r['Class_Type']), str(r['Class_Name']), str(r['Period']),
                                       str(r['Zoom_ID']) if pd.notna(r.get('Zoom_ID')) else None,
                                       str(r['Teacher_Name']),
                                       str(r['Assistant_1']) if pd.notna(r.get('Assistant_1')) else None,
                                       str(r['Assistant_2']) if pd.notna(r.get('Assistant_2')) else None,
                                       str(r['Lesson_Level']), str(r['Lesson_Topic'])))
                            ins += 1
                        except sqlite3.IntegrityError:
                            skp += 1
                    conn.commit()
                    conn.close()
                    show_popup("အချိန်ဇယားများ Import ပြီးပါပြီ!", f"အသစ်ထည့်သွင်းမှု: {ins} ခု | ထပ်နေ၍ ကျော်ခဲ့သည်: {skp} ခု")
                else:
                    st.error("Excel ကော်လံများ မမှန်ပါ။")
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 အချိန်ဇယားများ ပြင်ဆင်/ဖျက်ခြင်း (Edit / Delete)")
        tt_data = run_query("SELECT id, Date, Class_Type, Class_Name, Period, Zoom_ID, Teacher_Name, Assistant_1, Assistant_2, Lesson_Level, Lesson_Topic FROM timetable ORDER BY Date DESC")
        
        if not tt_data.empty:
            col_sa1, _ = st.columns([2, 8])
            with col_sa1:
                sel_all_tt = st.checkbox("☑️ အားလုံးရွေးမည် (Select All)", key="chk_all_tt")
            
            tt_data.insert(0, "Select", sel_all_tt)
            edited_table = st.data_editor(tt_data, use_container_width=True, hide_index=True, key="tt_batch_edit", disabled=[col for col in tt_data.columns if col != "Select"])
            
            selected_ids = edited_table[edited_table["Select"] == True]["id"].tolist()
            
            if st.button("🗑️ ရွေးချယ်ထားသည်များကို ဖျက်မည်", type="secondary", disabled=len(selected_ids)==0):
                conn = sqlite3.connect(DB_FILE)
                conn.cursor().execute(f"DELETE FROM timetable WHERE id IN ({','.join(['?']*len(selected_ids))})", selected_ids)
                conn.commit()
                conn.close()
                show_popup(f"ရွေးချယ်ထားသော အချိန်ဇယား {len(selected_ids)} ခုကို ဖျက်ပြီးပါပြီ!")
            
            st.write("---")
            ed_id = st.selectbox("ပြင်ဆင်လိုသည့် အချိန်ဇယား ID ရွေးပါ", tt_data["id"].tolist(), key="adm_ed_tt_id")
            if st.button("✏️ ရွေးထားသည့် အချိန်ဇယား ပြင်မည်"):
                edit_timetable_dialog(ed_id)

    # --- STUDENT MANAGEMENT ---
    with tabs[2]:
        st.subheader("👥 ကျောင်းသားများ စီမံခန့်ခွဲမှု")
        
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            with st.expander("➕ ကျောင်းသားအသစ် တစ်ဦးချင်း ထည့်ရန်"):
                with st.form("stu_single_form", clear_on_submit=True):
                    st_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, key="adm_st_type")
                    st_class = st.text_input("တန်းခွဲ အမည်", key="adm_st_class")
                    st_name = st.text_input("ကျောင်းသား အမည်", key="adm_st_name")
                    st_age = st.number_input("အသက် (Age)", min_value=3, max_value=80, value=15, key="adm_st_age")
                    st_parent = st.text_input("မိဘ အမည်", key="adm_st_parent")
                    st_phone = st.text_input("ဖုန်းနံပါတ်", key="adm_st_phone")
                    st_social = st.text_input("မိဘ Social အကောင့် (Viber/Facebook)", key="adm_st_social")
                    st_address = st.text_area("လိပ်စာ", key="adm_st_address")
                    
                    if st.form_submit_button("သိမ်းဆည်းမည်"):
                        if st_name and st_class:
                            try:
                                execute_query(
                                    "INSERT INTO students (Student_Name, Age, Class_Type, Class_Name, Parent_Name, Phone, Social_Account, Address) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (st_name, st_age, st_type, st_class, st_parent, st_phone, st_social, st_address)
                                )
                                show_popup("ကျောင်းသားစာရင်း သိမ်းဆည်းပြီးပါပြီ!")
                            except sqlite3.IntegrityError:
                                st.error("ဤအတန်းတွင် ယခုအမည်ဖြင့် ကျောင်းသား ရှိပြီးသား ဖြစ်နေပါသည်။")
                        else:
                            st.warning("ကျောင်းသားအမည်နှင့် အတန်း ဖြည့်သွင်းပါ။")

        with s_c2:
            with st.expander("📂 ကျောင်းသားစာရင်း Excel မှ Import ပြုလုပ်ရန်"):
                up_stu = st.file_uploader("Excel ဖိုင်တင်ရန် (Columns: Student_Name, Age, Class_Type, Class_Name, Parent_Name, Phone, Social_Account, Address)", type=["xlsx", "xls"], key="adm_up_stu")
                if up_stu and st.button("📥 ကျောင်းသား Import စတင်မည်"):
                    try:
                        imp_s = pd.read_excel(up_stu)
                        if {"Student_Name", "Class_Type", "Class_Name"}.issubset(set(imp_s.columns)):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            ins, skp = 0, 0
                            for _, r in imp_s.iterrows():
                                try:
                                    c.execute('''INSERT INTO students (Student_Name, Age, Class_Type, Class_Name, Parent_Name, Phone, Social_Account, Address) 
                                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                              (str(r['Student_Name']),
                                               int(r['Age']) if pd.notna(r.get('Age')) else None,
                                               str(r['Class_Type']), str(r['Class_Name']),
                                               str(r['Parent_Name']) if pd.notna(r.get('Parent_Name')) else None,
                                               str(r['Phone']) if pd.notna(r.get('Phone')) else None,
                                               str(r['Social_Account']) if pd.notna(r.get('Social_Account')) else None,
                                               str(r['Address']) if pd.notna(r.get('Address')) else None))
                                    ins += 1
                                except sqlite3.IntegrityError:
                                    skp += 1
                            conn.commit()
                            conn.close()
                            show_popup("ကျောင်းသားစာရင်း Import ပြီးပါပြီ!", f"အသစ်ထည့်သွင်းမှု: {ins} ဦး | ထပ်နေ၍ ကျော်ခဲ့သည်: {skp} ဦး")
                        else:
                            st.error("Excel တွင် Student_Name, Class_Type, Class_Name ကော်လံများ ပါဝင်ရပါမည်။")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 ကျောင်းသားစာရင်း ပြင်ဆင်/ဖျက်ခြင်း (Edit / Delete)")
        stu_df = run_query("SELECT id, Student_Name, Age, Class_Type, Class_Name, Parent_Name, Phone, Social_Account, Address FROM students ORDER BY Class_Type, Class_Name, Student_Name")
        
        if not stu_df.empty:
            col_sa_stu, _ = st.columns([2, 8])
            with col_sa_stu:
                sel_all_stu = st.checkbox("☑️ အားလုံးရွေးမည် (Select All)", key="chk_all_stu")
                
            stu_df.insert(0, "Select", sel_all_stu)
            edited_stu = st.data_editor(stu_df, use_container_width=True, hide_index=True, key="adm_stu_batch_edit", disabled=[col for col in stu_df.columns if col != "Select"])
            
            sel_stu_ids = edited_stu[edited_stu["Select"] == True]["id"].tolist()
            
            if st.button("🗑️ ရွေးထားသော ကျောင်းသားများ ဖျက်မည်", type="secondary", disabled=len(sel_stu_ids)==0):
                conn = sqlite3.connect(DB_FILE)
                conn.cursor().execute(f"DELETE FROM students WHERE id IN ({','.join(['?']*len(sel_stu_ids))})", sel_stu_ids)
                conn.commit()
                conn.close()
                show_popup(f"ရွေးချယ်ထားသော ကျောင်းသား {len(sel_stu_ids)} ဦးကို ဖျက်ပြီးပါပြီ!")
                    
            st.write("---")
            ed_stu_id = st.selectbox("ပြင်ဆင်လိုသည့် ကျောင်းသား ID ရွေးပါ", stu_df["id"].tolist(), key="adm_ed_stu_id")
            if st.button("✏️ ရွေးထားသည့် ကျောင်းသား အချက်အလက် ပြင်မည်"):
                edit_student_dialog(ed_stu_id)

    att_tab = tabs[3]
    rep_tab = tabs[4]
    
    # --- TEACHER MANAGEMENT ---
    with tabs[5]:
        st.subheader("👨‍🏫 ဆရာ/ဆရာမ စာရင်း စီမံခန့်ခွဲမှု")
        
        tc1, tc2 = st.columns(2)
        with tc1:
            with st.expander("➕ ဆရာ/မ အသစ် တစ်ဦးချင်း ထည့်ရန်"):
                with st.form("teach_single_form", clear_on_submit=True):
                    t_name = st.text_input("ဆရာ/မ အမည်")
                    t_phone = st.text_input("ဖုန်းနံပါတ်")
                    if st.form_submit_button("သိမ်းဆည်းမည်"):
                        if t_name:
                            try:
                                execute_query("INSERT INTO teachers (Teacher_Name, Phone) VALUES (?, ?)", (t_name, t_phone))
                                show_popup("ဆရာ/မ အချက်အလက် သိမ်းဆည်းပြီးပါပြီ!")
                            except sqlite3.IntegrityError:
                                st.error("ဤဆရာ/မ အမည် ရှိပြီးသား ဖြစ်နေပါသည်။")
                        else:
                            st.warning("အမည် ဖြည့်သွင်းပါ။")
                            
        with tc2:
            with st.expander("📂 ဆရာ/မ စာရင်း Excel မှ Import ပြုလုပ်ရန်"):
                up_teach = st.file_uploader("Excel တင်ရန် (Columns: Teacher_Name, Phone)", type=["xlsx", "xls"], key="adm_up_teach")
                if up_teach and st.button("📥 ဆရာ/မ Import စတင်မည်"):
                    try:
                        imp_t = pd.read_excel(up_teach)
                        if "Teacher_Name" in imp_t.columns:
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            ins, skp = 0, 0
                            for _, r in imp_t.iterrows():
                                try:
                                    c.execute("INSERT INTO teachers (Teacher_Name, Phone) VALUES (?, ?)", 
                                              (str(r['Teacher_Name']), str(r['Phone']) if pd.notna(r.get('Phone')) else None))
                                    ins += 1
                                except sqlite3.IntegrityError:
                                    skp += 1
                            conn.commit()
                            conn.close()
                            show_popup("ဆရာ/မ စာရင်း Import ပြီးပါပြီ!", f"အသစ်ထည့်သွင်းမှု: {ins} ဦး | ထပ်နေ၍ ကျော်ခဲ့သည်: {skp} ဦး")
                        else:
                            st.error("Excel တွင် Teacher_Name ကော်လံ ပါဝင်ရပါမည်။")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 ဆရာ/မ စာရင်း ပြင်ဆင်/ဖျက်ခြင်း (Edit / Delete)")
        teach_df = run_query("SELECT id, Teacher_Name, Phone FROM teachers ORDER BY Teacher_Name")
        
        if not teach_df.empty:
            col_sa_t, _ = st.columns([2, 8])
            with col_sa_t:
                sel_all_t = st.checkbox("☑️ အားလုံးရွေးမည် (Select All)", key="chk_all_t")
                
            teach_df.insert(0, "Select", sel_all_t)
            edited_t = st.data_editor(teach_df, use_container_width=True, hide_index=True, key="adm_teach_batch_edit", disabled=[col for col in teach_df.columns if col != "Select"])
            
            sel_t_ids = edited_t[edited_t["Select"] == True]["id"].tolist()
            
            if st.button("🗑️ ရွေးထားသော ဆရာ/မများ ဖျက်မည်", type="secondary", disabled=len(sel_t_ids)==0):
                conn = sqlite3.connect(DB_FILE)
                conn.cursor().execute(f"DELETE FROM teachers WHERE id IN ({','.join(['?']*len(sel_t_ids))})", sel_t_ids)
                conn.commit()
                conn.close()
                show_popup(f"ရွေးချယ်ထားသော ဆရာ/မ {len(sel_t_ids)} ဦးကို ဖျက်ပြီးပါပြီ!")
                    
            st.write("---")
            ed_t_id = st.selectbox("ပြင်ဆင်လိုသည့် ဆရာ/မ ID ရွေးပါ", teach_df["id"].tolist(), key="adm_ed_t_id")
            if st.button("✏️ ရွေးထားသည့် ဆရာ/မ အချက်အလက် ပြင်မည်"):
                edit_teacher_dialog(ed_t_id)

    # --- LESSON MANAGEMENT ---
    with tabs[6]:
        st.subheader("📖 သင်ခန်းစာများ စီမံခန့်ခွဲမှု (User Upload Only)")
        
        lc1, lc2 = st.columns(2)
        with lc1:
            with st.expander("➕ သင်ခန်းစာ အသစ်တစ်ခုချင်း ထည့်ရန်"):
                with st.form("lsn_single_form", clear_on_submit=True):
                    l_lvl = st.text_input("Level (ဥပမာ - Level 1, Level 2)")
                    l_topic = st.text_input("သင်ခန်းစာ အမည် (Lesson Topic)")
                    if st.form_submit_button("သိမ်းဆည်းမည်"):
                        if l_lvl and l_topic:
                            try:
                                execute_query("INSERT INTO lessons (Level, Lesson_Topic) VALUES (?, ?)", (l_lvl.strip(), l_topic.strip()))
                                show_popup("သင်ခန်းစာ အသစ် ထည့်သွင်းပြီးပါပြီ!")
                            except sqlite3.IntegrityError:
                                st.error("ဤ Level တွင် ယခုသင်ခန်းစာ ရှိပြီးသား ဖြစ်နေပါသည်။")
                        else:
                            st.warning("Level နှင့် သင်ခန်းစာအမည် ဖြည့်သွင်းပါ။")
        with lc2:
            with st.expander("📂 သင်ခန်းစာများ Excel မှ Import ပြုလုပ်ရန်"):
                up_lsn = st.file_uploader("Excel တင်ရန် (Columns: Level, Lesson_Topic)", type=["xlsx", "xls"], key="adm_up_lsn")
                if up_lsn and st.button("📥 သင်ခန်းစာ Import စတင်မည်"):
                    try:
                        imp_l = pd.read_excel(up_lsn)
                        if {"Level", "Lesson_Topic"}.issubset(set(imp_l.columns)):
                            conn = sqlite3.connect(DB_FILE)
                            c = conn.cursor()
                            ins, skp = 0, 0
                            for _, r in imp_l.iterrows():
                                try:
                                    c.execute("INSERT INTO lessons (Level, Lesson_Topic) VALUES (?, ?)", (str(r['Level']).strip(), str(r['Lesson_Topic']).strip()))
                                    ins += 1
                                except sqlite3.IntegrityError:
                                    skp += 1
                            conn.commit()
                            conn.close()
                            show_popup("သင်ခန်းစာများ Import ပြီးပါပြီ!", f"အသစ်ထည့်သွင်းမှု: {ins} ခု | ထပ်နေ၍ ကျော်ခဲ့သည်: {skp} ခု")
                        else:
                            st.error("Excel တွင် Level နှင့် Lesson_Topic ကော်လံများ ပါဝင်ရပါမည်။")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 သင်ခန်းစာများ ပြင်ဆင်/ဖျက်ခြင်း (Edit / Delete)")
        lsn_df = run_query("SELECT id, Level, Lesson_Topic FROM lessons ORDER BY Level, id")
        
        if not lsn_df.empty:
            col_sa_l, _ = st.columns([2, 8])
            with col_sa_l:
                sel_all_l = st.checkbox("☑️ အားလုံးရွေးမည် (Select All)", key="chk_all_l")
                
            lsn_df.insert(0, "Select", sel_all_l)
            edited_l = st.data_editor(lsn_df, use_container_width=True, hide_index=True, key="adm_lsn_batch_edit", disabled=[col for col in lsn_df.columns if col != "Select"])
            
            sel_l_ids = edited_l[edited_l["Select"] == True]["id"].tolist()
            
            if st.button("🗑️ ရွေးထားသော သင်ခန်းစာများ ဖျက်မည်", type="secondary", disabled=len(sel_l_ids)==0):
                conn = sqlite3.connect(DB_FILE)
                conn.cursor().execute(f"DELETE FROM lessons WHERE id IN ({','.join(['?']*len(sel_l_ids))})", sel_l_ids)
                conn.commit()
                conn.close()
                show_popup(f"ရွေးချယ်ထားသော သင်ခန်းစာ {len(sel_l_ids)} ခုကို ဖျက်ပြီးပါပြီ!")
                    
            st.write("---")
            ed_l_id = st.selectbox("ပြင်ဆင်လိုသည့် သင်ခန်းစာ ID ရွေးပါ", lsn_df["id"].tolist(), key="adm_ed_l_id")
            if st.button("✏️ ရွေးထားသည့် သင်ခန်းစာ ပြင်မည်"):
                edit_lesson_dialog(ed_l_id)
        else:
            st.info("သင်ခန်းစာ အချက်အလက်များ မရှိသေးပါ။")

    # --- ANALYTICS DASHBOARD ---
    with tabs[7]:
        st.subheader("📈 We Are Genius - Academic Analytics Dashboard")
        
        total_students = run_query("SELECT COUNT(*) as c FROM students").iloc[0]['c']
        total_teachers = run_query("SELECT COUNT(*) as c FROM teachers").iloc[0]['c']
        total_schedules = run_query("SELECT COUNT(*) as c FROM timetable").iloc[0]['c']
        total_lessons = run_query("SELECT COUNT(*) as c FROM lessons").iloc[0]['c']
        
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f'''
                <div class="stat-card">
                    <div class="stat-label">👨‍🎓 Total Students</div>
                    <div class="stat-val">{total_students}</div>
                </div>
            ''', unsafe_allow_html=True)
        with k2:
            st.markdown(f'''
                <div class="stat-card">
                    <div class="stat-label">👨‍🏫 Faculty Teachers</div>
                    <div class="stat-val">{total_teachers}</div>
                </div>
            ''', unsafe_allow_html=True)
        with k3:
            st.markdown(f'''
                <div class="stat-card">
                    <div class="stat-label">📅 Scheduled Classes</div>
                    <div class="stat-val">{total_schedules}</div>
                </div>
            ''', unsafe_allow_html=True)
        with k4:
            st.markdown(f'''
                <div class="stat-card">
                    <div class="stat-label">📖 Active Lessons</div>
                    <div class="stat-val">{total_lessons}</div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")

        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            st.markdown("##### 📊 အတန်းတက် / ပျက် / ခွင့် နှုန်းထား နှိုင်းယှဉ်ချက်")
            att_stat_df = run_query('SELECT Status as "အခြေအနေ", COUNT(*) as "ဦးရေ" FROM attendance GROUP BY Status')
            if not att_stat_df.empty:
                st.bar_chart(data=att_stat_df.set_index("အခြေအနေ"), use_container_width=True)
            else:
                st.info("ကျောင်းခေါ်ချိန် မှတ်တမ်းများ မရှိသေးပါ။")

        with chart_c2:
            st.markdown("##### 👨‍🏫 ဆရာ/မ တစ်ဦးချင်း သင်ကြားချိန် အင်အား (Lead + Assistants)")
            teach_hours_q = '''
                SELECT Teacher, COUNT(*) as "စာသင်ချိန်_အရေအတွက်" FROM (
                    SELECT Teacher_Name as Teacher FROM timetable WHERE Teacher_Name IS NOT NULL
                    UNION ALL
                    SELECT Assistant_1 as Teacher FROM timetable WHERE Assistant_1 IS NOT NULL
                    UNION ALL
                    SELECT Assistant_2 as Teacher FROM timetable WHERE Assistant_2 IS NOT NULL
                ) GROUP BY Teacher ORDER BY "စာသင်ချိန်_အရေအတွက်" DESC
            '''
            teach_stat_df = run_query(teach_hours_q)
            if not teach_stat_df.empty:
                st.bar_chart(data=teach_stat_df.set_index("Teacher"), use_container_width=True)
            else:
                st.info("အချိန်ဇယား အချက်အလက်များ မရှိသေးပါ။")

        st.markdown("---")
        chart_c3, chart_c4 = st.columns(2)
        with chart_c3:
            st.markdown("##### 🏫 သင်ကြားမှု စနစ်အလိုက် ကျောင်းသား အင်အား")
            class_dist_df = run_query("SELECT Class_Type, COUNT(*) as 'ကျောင်းသားဦးရေ' FROM students GROUP BY Class_Type")
            if not class_dist_df.empty:
                st.bar_chart(data=class_dist_df.set_index("Class_Type"), use_container_width=True)
            else:
                st.info("ကျောင်းသားစာရင်း မရှိသေးပါ။")

        with chart_c4:
            st.markdown("##### 📖 Level အလိုက် သင်ခန်းစာ အရေအတွက် ဖြန့်ကြက်မှု")
            lsn_dist_df = run_query("SELECT Level, COUNT(*) as 'သင်ခန်းစာ အရေအတွက်' FROM lessons GROUP BY Level")
            if not lsn_dist_df.empty:
                st.bar_chart(data=lsn_dist_df.set_index("Level"), use_container_width=True)
            else:
                st.info("သင်ခန်းစာ စာရင်း မရှိသေးပါ။")

else:
    att_tab = tabs[1]
    rep_tab = tabs[2]

# ================= TAB: DAILY ATTENDANCE (Both) =================
with att_tab:
    st.subheader("📋 နေ့စဉ် ကျောင်းခေါ်ချိန် မှတ်တမ်း")
    
    st_classes = run_query("SELECT DISTINCT Class_Type, Class_Name FROM students")
    
    if not st_classes.empty:
        a1, a2, a3 = st.columns(3)
        with a1:
            att_date = st.date_input("ရက်စွဲ ရွေးချယ်ပါ", date.today(), key="att_d_pick").strftime("%Y-%m-%d")
        with a2:
            sel_at_type = st.selectbox("ကျောင်းအမျိုးအစား", sorted(st_classes["Class_Type"].unique().tolist()), key="at_tp_sel")
        with a3:
            filtered_cn = st_classes[st_classes["Class_Type"] == sel_at_type]["Class_Name"].unique().tolist()
            sel_at_cls = st.selectbox("တန်းခွဲ", filtered_cn, key="at_cls_sel")

        stu_in_c = run_query("SELECT Student_Name, Phone FROM students WHERE Class_Type = ? AND Class_Name = ? ORDER BY Student_Name", (sel_at_type, sel_at_cls))
        
        if not stu_in_c.empty:
            existing_att = run_query("SELECT Student_Name, Status FROM attendance WHERE Date = ? AND Class_Type = ? AND Class_Name = ?", (att_date, sel_at_type, sel_at_cls))
            status_map = dict(zip(existing_att["Student_Name"], existing_att["Status"])) if not existing_att.empty else {}

            st.write(f"**{sel_at_type} - {sel_at_cls}** ({att_date} ရက်စွဲ)")
            
            with st.form("daily_att_form"):
                saved_att = []
                for _, srow in stu_in_c.iterrows():
                    sname = srow["Student_Name"]
                    sphone = str(srow["Phone"]) if pd.notna(srow["Phone"]) else "-"
                    curr_st = status_map.get(sname, "တက်ရောက်")
                    idx = ["တက်ရောက်", "ပျက်ကွက်", "ခွင့်"].index(curr_st) if curr_st in ["တက်ရောက်", "ပျက်ကွက်", "ခွင့်"] else 0
                    
                    col_info, col_radio = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"**{sname}** | 📞 `{sphone}`")
                    with col_radio:
                        st_choice = st.radio(f"status_{sname}", ["တက်ရောက်", "ပျက်ကွက်", "ခွင့်"], index=idx, horizontal=True, label_visibility="collapsed")
                    saved_att.append((att_date, sel_at_type, sel_at_cls, sname, sphone, st_choice))
                
                if st.form_submit_button("💾 ကျောင်းခေါ်ချိန် သိမ်းဆည်းမည်", type="primary"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("DELETE FROM attendance WHERE Date = ? AND Class_Type = ? AND Class_Name = ?", (att_date, sel_at_type, sel_at_cls))
                    c.executemany("INSERT INTO attendance (Date, Class_Type, Class_Name, Student_Name, Phone, Status) VALUES (?, ?, ?, ?, ?, ?)", saved_att)
                    conn.commit()
                    conn.close()
                    show_popup("ကျောင်းခေါ်ချိန် အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!")
        else:
            st.warning("ဤအတန်းအတွက် ကျောင်းသား မရှိသေးပါ။")
    else:
        st.info("ကျောင်းခေါ်ချိန်စစ်ရန် ကျောင်းသားစာရင်း ဦးစွာ ထည့်သွင်းပါ။")

# ================= TAB: ATTENDANCE & STRENGTH REPORT (Both) =================
with rep_tab:
    st.subheader("📊 ကျောင်းသားအင်အားနှင့် တက်/ပျက် စာရင်းချုပ်")
    rep_date = st.date_input("စစ်ဆေးလိုသည့် ရက်စွဲ", date.today(), key="sum_d_pick").strftime("%Y-%m-%d")
    
    summary_q = '''
        SELECT 
            s.Class_Type as "ကျောင်းအမျိုးအစား",
            s.Class_Name as "တန်းခွဲ",
            COUNT(s.Student_Name) as "ကျောင်းသားအင်အား",
            SUM(CASE WHEN a.Status = 'တက်ရောက်' THEN 1 ELSE 0 END) as "တက်ရောက်",
            SUM(CASE WHEN a.Status = 'ပျက်ကွက်' THEN 1 ELSE 0 END) as "ပျက်ကွက်",
            SUM(CASE WHEN a.Status = 'ခွင့်' THEN 1 ELSE 0 END) as "ခွင့်",
            SUM(CASE WHEN a.Status IS NULL THEN 1 ELSE 0 END) as "စာရင်းမသွင်းရသေး"
        FROM students s
        LEFT JOIN attendance a ON s.Student_Name = a.Student_Name AND s.Class_Type = a.Class_Type AND s.Class_Name = a.Class_Name AND a.Date = ?
        GROUP BY s.Class_Type, s.Class_Name
    '''
    rep_df = run_query(summary_q, (rep_date,))
    if not rep_df.empty:
        st.dataframe(rep_df, use_container_width=True, hide_index=True)
    else:
        st.info("အချက်အလက်များ မရှိသေးပါ။")
