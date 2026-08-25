import os
import hashlib
import hmac
import secrets
from datetime import date, timedelta
import pandas as pd
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
import streamlit as st

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="We Are Genius - Basic Science School",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Padauk:wght@400;700&display=swap');
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    .main .block-container { padding-top: 1.5rem !important; padding-bottom: 2.5rem !important; max-width: 1350px; }
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', 'Padauk', sans-serif; }
    .stApp { background: linear-gradient( 135deg, #f8fafc 0%, #ecfdf5 50%, #f0fdf4 100% ); color: #0f172a; }
    .brand-title-large { font-family: 'Cinzel', serif; font-size: 2.5rem; font-weight: 900; letter-spacing: 2px; background: linear-gradient( 120deg, #059669 0%, #10b981 100% ); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 10px; margin-bottom: 2px; line-height: 1.15; text-align: center; }
    .brand-subtitle-large { font-size: 1.25rem; font-weight: 800; color: #1e293b; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; text-align: center; }
    .app-badge-large { display: inline-block; background: #d1fae5; color: #065f46; font-size: 0.88rem; font-weight: 700; padding: 6px 18px; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.4); letter-spacing: 0.5px; margin-bottom: 20px; }
    .stat-card { background: #ffffff; border: 1.5px solid rgba(16, 185, 129, 0.25); border-radius: 18px; padding: 22px; text-align: center; box-shadow: 0 8px 20px rgba(16, 185, 129, 0.08); transition: all 0.3s ease; }
    .stat-card:hover { transform: translateY(-4px); border-color: #10b981; box-shadow: 0 12px 25px rgba(16, 185, 129, 0.18); }
    .stat-val { font-size: 2.5rem; font-weight: 900; color: #059669; margin: 6px 0; }
    .stat-label { font-size: 0.95rem; font-weight: 700; color: #64748b; }
    .stTextInput input, .stSelectbox select, .stDateInput input { background-color: #ffffff !important; color: #0f172a !important; border-radius: 10px !important; border: 1px solid #cbd5e1 !important; }
    div[data-testid="stExpander"] { border-radius: 14px; border: 1px solid rgba(16, 185, 129, 0.2); background-color: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SETTINGS
# =========================================================
def get_setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value or default)

DATABASE_URL = get_setting("DATABASE_URL").strip()
if not DATABASE_URL:
    st.error("DATABASE_URL မသတ်မှတ်ရသေးပါ။ Streamlit Secrets သို့မဟုတ် Environment Variable တွင် ထည့်သွင်းပါ။")
    st.stop()

CLASS_TYPES = ["ကိုယ်ပိုင်ကျောင်းများ", "On Campus", "Zoom Online"]

# =========================================================
# OPTIMIZATION: CONNECTION POOLING
# =========================================================
@st.cache_resource
def get_db_pool():
    return ThreadedConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

def get_conn():
    return get_db_pool().getconn()

def release_conn(conn):
    get_db_pool().putconn(conn)

# =========================================================
# OPTIMIZATION: CACHED QUERY & DML
# =========================================================
@st.cache_data(ttl=15, show_spinner=False)
def run_query(query, params=()):
    conn = get_conn()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        release_conn(conn)

def execute_query(query, params=()):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_conn(conn)

# =========================================================
# PASSWORD FUNCTIONS
# =========================================================
def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password, stored_hash):
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False

# =========================================================
# OPTIMIZATION: ONE-TIME DB INITIALIZATION
# =========================================================
@st.cache_resource
def initialize_database():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('Admin', 'Teacher')),
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                teacher_name TEXT NOT NULL UNIQUE,
                phone TEXT
            );
            CREATE TABLE IF NOT EXISTS lessons (
                id SERIAL PRIMARY KEY,
                level TEXT NOT NULL,
                lesson_topic TEXT NOT NULL,
                UNIQUE(level, lesson_topic)
            );
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                student_name TEXT NOT NULL,
                age INTEGER,
                class_type TEXT NOT NULL,
                class_name TEXT NOT NULL,
                parent_name TEXT,
                phone TEXT,
                social_account TEXT,
                address TEXT,
                UNIQUE(student_name, class_type, class_name)
            );
            CREATE TABLE IF NOT EXISTS timetable (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                class_type TEXT NOT NULL,
                class_name TEXT NOT NULL,
                period TEXT NOT NULL,
                zoom_id TEXT,
                teacher_name TEXT NOT NULL,
                assistant_1 TEXT,
                assistant_2 TEXT,
                lesson_level TEXT NOT NULL,
                lesson_topic TEXT NOT NULL,
                UNIQUE(date, class_type, class_name, period)
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                class_type TEXT NOT NULL,
                class_name TEXT NOT NULL,
                student_name TEXT NOT NULL,
                phone TEXT,
                status TEXT NOT NULL,
                UNIQUE(date, class_type, class_name, student_name)
            );
        """)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            admin_username = get_setting("ADMIN_USERNAME", "admin").strip()
            admin_password = get_setting("ADMIN_PASSWORD", "admin12345")
            teacher_username = get_setting("TEACHER_USERNAME", "teacher").strip()
            teacher_password = get_setting("TEACHER_PASSWORD", "teacher12345")

            if admin_username and admin_password:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'Admin') ON CONFLICT DO NOTHING",
                    (admin_username, hash_password(admin_password)),
                )
            if teacher_username and teacher_password:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'Teacher') ON CONFLICT DO NOTHING",
                    (teacher_username, hash_password(teacher_password)),
                )
            conn.commit()
    finally:
        cur.close()
        release_conn(conn)
    return True

initialize_database()

# =========================================================
# AUTHENTICATION
# =========================================================
def authenticate_user(username, password, role):
    df = run_query(
        "SELECT username, role, password_hash, active FROM users WHERE username = %s AND role = %s",
        (username.strip(), role),
    )
    if df.empty or not bool(df.iloc[0]["active"]):
        return False
    return verify_password(password, df.iloc[0]["password_hash"])

# =========================================================
# DIALOGS (EDIT ONLY)
# =========================================================
@st.dialog("✏️ အချိန်ဇယား ပြင်ဆင်ရန်")
def edit_timetable_dialog(row_id):
    row_df = run_query("SELECT * FROM timetable WHERE id = %s", (row_id,))
    if row_df.empty:
        st.error("အချိန်ဇယား မတွေ့ပါ။")
        return
    row = row_df.iloc[0]
    teachers = run_query("SELECT teacher_name FROM teachers ORDER BY teacher_name")["teacher_name"].dropna().tolist()
    levels = run_query("SELECT DISTINCT level FROM lessons ORDER BY level")["level"].dropna().tolist()

    e_date = st.text_input("ရက်စွဲ (YYYY-MM-DD)", value=str(row["date"]))
    e_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, index=CLASS_TYPES.index(row["class_type"]) if row["class_type"] in CLASS_TYPES else 0)
    e_class = st.text_input("တန်းခွဲ", value=str(row["class_name"]))
    e_period = st.text_input("စာသင်ချိန်", value=str(row["period"]))
    e_zoom = st.text_input("Zoom ID / Link", value=str(row["zoom_id"]) if pd.notna(row["zoom_id"]) else "")

    e_t = st.selectbox("Lead Teacher", teachers, index=teachers.index(row["teacher_name"]) if row["teacher_name"] in teachers else 0) if teachers else st.text_input("Lead Teacher", value=str(row["teacher_name"]))
    asst_opts = ["မရှိပါ"] + teachers
    e_a1 = st.selectbox("Assistant 1", asst_opts, index=asst_opts.index(row["assistant_1"]) if row["assistant_1"] in asst_opts else 0)
    e_a2 = st.selectbox("Assistant 2", asst_opts, index=asst_opts.index(row["assistant_2"]) if row["assistant_2"] in asst_opts else 0)

    e_lvl = st.selectbox("Level ရွေးပါ", levels, index=levels.index(row["lesson_level"]) if row["lesson_level"] in levels else 0) if levels else None
    e_top = None
    if e_lvl:
        lsns = run_query("SELECT lesson_topic FROM lessons WHERE level = %s ORDER BY id", (e_lvl,))["lesson_topic"].dropna().tolist()
        if lsns:
            e_top = st.selectbox("Lesson ရွေးပါ", lsns, index=lsns.index(row["lesson_topic"]) if row["lesson_topic"] in lsns else 0)

    if st.button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
        if e_lvl and e_top and e_t:
            try:
                execute_query(
                    """UPDATE timetable SET date=%s, class_type=%s, class_name=%s, period=%s, zoom_id=%s,
                       teacher_name=%s, assistant_1=%s, assistant_2=%s, lesson_level=%s, lesson_topic=%s WHERE id=%s""",
                    (e_date, e_type, e_class, e_period, e_zoom, e_t, None if e_a1 == "မရှိပါ" else e_a1, None if e_a2 == "မရှိပါ" else e_a2, e_lvl, e_top, row_id),
                )
                run_query.clear()
                st.toast("✅ ပြင်ဆင်ပြီးပါပြီ!")
                st.rerun()
            except psycopg2.IntegrityError:
                st.error("ယခု အချိန်ဇယား ရှိပြီးသား ဖြစ်နေပါသည်။")

@st.dialog("✏️ ကျောင်းသား အချက်အလက် ပြင်ဆင်ရန်")
def edit_student_dialog(row_id):
    row_df = run_query("SELECT * FROM students WHERE id = %s", (row_id,))
    if row_df.empty:
        st.error("ကျောင်းသား မတွေ့ပါ။")
        return
    row = row_df.iloc[0]
    with st.form("edit_stu_form"):
        e_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, index=CLASS_TYPES.index(row["class_type"]) if row["class_type"] in CLASS_TYPES else 0)
        e_class = st.text_input("တန်းခွဲ", value=str(row["class_name"]))
        e_name = st.text_input("ကျောင်းသား အမည်", value=str(row["student_name"]))
        e_age = st.number_input("အသက်", min_value=3, max_value=80, value=int(row["age"]) if pd.notna(row["age"]) else 15)
        e_parent = st.text_input("မိဘ အမည်", value=str(row["parent_name"]) if pd.notna(row["parent_name"]) else "")
        e_phone = st.text_input("ဖုန်းနံပါတ်", value=str(row["phone"]) if pd.notna(row["phone"]) else "")
        e_social = st.text_input("Social အကောင့်", value=str(row["social_account"]) if pd.notna(row["social_account"]) else "")
        e_address = st.text_area("လိပ်စာ", value=str(row["address"]) if pd.notna(row["address"]) else "")

        if st.form_submit_button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
            try:
                execute_query(
                    """UPDATE students SET class_type=%s, class_name=%s, student_name=%s, age=%s,
                       parent_name=%s, phone=%s, social_account=%s, address=%s WHERE id=%s""",
                    (e_type, e_class, e_name, e_age, e_parent, e_phone, e_social, e_address, row_id),
                )
                run_query.clear()
                st.toast("✅ ကျောင်းသားစာရင်း ပြင်ဆင်ပြီးပါပြီ!")
                st.rerun()
            except psycopg2.IntegrityError:
                st.error("ကျောင်းသား အမည် ထပ်နေပါသည်။")

@st.dialog("✏️ ဆရာ/မ အချက်အလက် ပြင်ဆင်ရန်")
def edit_teacher_dialog(row_id):
    row_df = run_query("SELECT * FROM teachers WHERE id = %s", (row_id,))
    if row_df.empty:
        st.error("ဆရာ/မ မတွေ့ပါ။")
        return
    row = row_df.iloc[0]
    with st.form("edit_teach_form"):
        e_name = st.text_input("ဆရာ/မ အမည်", value=str(row["teacher_name"]))
        e_phone = st.text_input("ဖုန်းနံပါတ်", value=str(row["phone"]) if pd.notna(row["phone"]) else "")
        if st.form_submit_button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
            try:
                execute_query("UPDATE teachers SET teacher_name=%s, phone=%s WHERE id=%s", (e_name, e_phone, row_id))
                run_query.clear()
                st.toast("✅ ဆရာ/မ အချက်အလက် ပြင်ဆင်ပြီးပါပြီ!")
                st.rerun()
            except psycopg2.IntegrityError:
                st.error("ဤဆရာ/မ အမည် ရှိပြီးသားဖြစ်နေပါသည်။")

@st.dialog("✏️ သင်ခန်းစာ ပြင်ဆင်ရန်")
def edit_lesson_dialog(row_id):
    row_df = run_query("SELECT * FROM lessons WHERE id = %s", (row_id,))
    if row_df.empty:
        st.error("သင်ခန်းစာ မတွေ့ပါ။")
        return
    row = row_df.iloc[0]
    with st.form("edit_lsn_form"):
        e_lvl = st.text_input("Level", value=str(row["level"]))
        e_top = st.text_input("Lesson Topic", value=str(row["lesson_topic"]))
        if st.form_submit_button("💾 သိမ်းဆည်းမည်", type="primary", use_container_width=True):
            try:
                execute_query("UPDATE lessons SET level=%s, lesson_topic=%s WHERE id=%s", (e_lvl.strip(), e_top.strip(), row_id))
                run_query.clear()
                st.toast("✅ သင်ခန်းစာ ပြင်ဆင်ပြီးပါပြီ!")
                st.rerun()
            except psycopg2.IntegrityError:
                st.error("ဤ Level တွင် သင်ခန်းစာ ရှိပြီးသားဖြစ်နေပါသည်။")

# =========================================================
# SESSION & LOGIN
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.4, 1])
    with center_col:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=120)
        else:
            st.markdown("<h1 style='text-align:center;'>🔬</h1>", unsafe_allow_html=True)

        st.markdown(
            """<div class="brand-title-large">WE ARE GENIUS</div>
               <div class="brand-subtitle-large">Basic Science School</div>
               <div style="text-align:center;"><span class="app-badge-large">School Management Application</span></div>""",
            unsafe_allow_html=True,
        )

        with st.form("clean_login_form"):
            role_choice = st.selectbox("Role", ["Teacher (ဆရာ/မ)", "Admin (စီမံခန့်ခွဲသူ)"])
            username = st.text_input("Username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("🚀 စနစ်သို့ ဝင်ရောက်မည် (Sign In)", type="primary", use_container_width=True):
                selected_role = "Admin" if role_choice.startswith("Admin") else "Teacher"
                if username and password and authenticate_user(username, password, selected_role):
                    st.session_state.logged_in = True
                    st.session_state.role = selected_role
                    st.session_state.username = username.strip()
                    st.rerun()
                else:
                    st.error("Username သို့မဟုတ် Password မှားယွင်းနေပါသည်။")
    st.stop()

# =========================================================
# SIDEBAR NAVIGATION & TOP HEADER
# =========================================================
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=100)
    st.markdown("### **We Are Genius**")
    st.caption("Basic Science School")
    st.success(f"👤 Role: **{st.session_state.role}** ({st.session_state.username})")

    if st.session_state.role == "Admin":
        nav_options = [
            "📅 အပတ်စဉ် အချိန်ဇယား",
            "➕ အချိန်ဇယား စီမံရန်",
            "👥 ကျောင်းသား စီမံခန့်ခွဲမှု",
            "📋 ကျောင်းခေါ်ချိန် မှတ်တမ်း",
            "📊 တက်/ပျက် စာရင်းချုပ်",
            "👨‍🏫 ဆရာ/မ စာရင်း",
            "📖 သင်ခန်းစာများ စီမံရန်",
            "📈 Analytics Dashboard",
            "🔐 User Accounts",
        ]
    else:
        nav_options = [
            "📅 အပတ်စဉ် အချိန်ဇယား",
            "📋 ကျောင်းခေါ်ချိန် မှတ်တမ်း",
            "📊 တက်/ပျက် စာရင်းချုပ်",
        ]

    selected_page = st.radio("Navigation Menu", nav_options, label_visibility="collapsed")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# Top Title Bar
h_col1, h_col2 = st.columns([8, 2])
with h_col1:
    st.markdown(
        """<h3 style='margin:0; font-family:Cinzel, serif; color:#059669;'>WE ARE GENIUS - BASIC SCIENCE SCHOOL</h3>
           <p style='margin:0; color:#0d9488; font-size:0.95rem;'>School Management & Academic Timetable System</p>""",
        unsafe_allow_html=True,
    )
st.markdown("---")

# =========================================================
# PAGE 1: VIEW TIMETABLE
# =========================================================
if selected_page == "📅 အပတ်စဉ် အချိန်ဇယား":
    st.subheader("🔍 အပတ်စဉ် အချိန်ဇယား ရှာဖွေကြည့်ရှုရန်")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        view_type = st.selectbox("ကျောင်းအမျိုးအစား", ["အားလုံး"] + CLASS_TYPES)
    with c2:
        t_df = run_query("SELECT DISTINCT teacher_name FROM teachers WHERE teacher_name IS NOT NULL ORDER BY teacher_name")
        view_t = st.selectbox("ဆရာ/မ အမည်", ["အားလုံး"] + t_df["teacher_name"].tolist())
    with c3:
        start_w = st.date_input("စတင်မည့်ရက်", date.today() - timedelta(days=date.today().weekday()))
    with c4:
        end_w = st.date_input("ပြီးဆုံးမည့်ရက်", start_w + timedelta(days=6))

    q = "SELECT date AS \"Date\", class_type AS \"Class_Type\", class_name AS \"Class_Name\", period AS \"Period\", zoom_id AS \"Zoom_ID\", teacher_name AS \"Teacher_Name\", assistant_1 AS \"Assistant_1\", assistant_2 AS \"Assistant_2\", lesson_level AS \"Lesson_Level\", lesson_topic AS \"Lesson_Topic\" FROM timetable WHERE date BETWEEN %s AND %s"
    p = [start_w.strftime("%Y-%m-%d"), end_w.strftime("%Y-%m-%d")]
    if view_type != "အားလုံး":
        q += " AND class_type = %s"
        p.append(view_type)
    if view_t != "အားလုံး":
        q += " AND (teacher_name = %s OR assistant_1 = %s OR assistant_2 = %s)"
        p.extend([view_t, view_t, view_t])
    q += " ORDER BY date ASC, period ASC"

    res = run_query(q, tuple(p))
    if not res.empty:
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.info("ရွေးချယ်ထားသော ရက်အတွင်း အချိန်ဇယား မရှိသေးပါ။")

# =========================================================
# PAGE 2: TIMETABLE MANAGEMENT (ADMIN)
# =========================================================
elif selected_page == "➕ အချိန်ဇယား စီမံရန်":
    st.subheader("➕ အချိန်ဇယား အသစ်ထည့်သွင်းရန်")
    teachers = run_query("SELECT teacher_name FROM teachers ORDER BY teacher_name")["teacher_name"].dropna().tolist()
    levels_avail = run_query("SELECT DISTINCT level FROM lessons ORDER BY level")["level"].dropna().tolist()

    if not levels_avail:
        st.warning("⚠️ သင်ခန်းစာ Level များ မရှိသေးပါ။ ဦးစွာ သင်ခန်းစာများ ထည့်သွင်းပါ။")
    else:
        with st.form("adm_tt_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                in_date = st.date_input("ရက်စွဲ", date.today()).strftime("%Y-%m-%d")
                in_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES)
                in_class = st.text_input("တန်းခွဲ")
                in_period = st.text_input("စာသင်ချိန်")
            with c2:
                in_zoom = st.text_input("Zoom ID / Link")
                in_t = st.selectbox("Lead Teacher", ["ရွေးချယ်ပါ"] + teachers)
                in_a1 = st.selectbox("Assistant 1", ["မရှိပါ"] + teachers)
                in_a2 = st.selectbox("Assistant 2", ["မရှိပါ"] + teachers)
            with c3:
                in_lvl = st.selectbox("Level", levels_avail)
                lessons = run_query("SELECT lesson_topic FROM lessons WHERE level = %s ORDER BY id", (in_lvl,))["lesson_topic"].dropna().tolist()
                in_top = st.selectbox("သင်ကြားရမည့် သင်ခန်းစာ", lessons if lessons else ["မရှိပါ"])

            if st.form_submit_button("💾 အချိန်ဇယား သိမ်းဆည်းမည်", type="primary"):
                if in_class and in_t != "ရွေးချယ်ပါ" and in_period and in_top != "မရှိပါ":
                    try:
                        execute_query(
                            """INSERT INTO timetable (date, class_type, class_name, period, zoom_id, teacher_name, assistant_1, assistant_2, lesson_level, lesson_topic)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (in_date, in_type, in_class, in_period, in_zoom, in_t, None if in_a1 == "မရှိပါ" else in_a1, None if in_a2 == "မရှိပါ" else in_a2, in_lvl, in_top),
                        )
                        run_query.clear()
                        st.toast("✅ အချိန်ဇယား အသစ် ထည့်သွင်းပြီးပါပြီ!", icon="🎉")
                    except psycopg2.IntegrityError:
                        st.error("ယခု အချိန်ဇယား ရှိပြီးသားဖြစ်နေပါသည်။")
                else:
                    st.warning("အချက်အလက်များကို ပြည့်စုံစွာ ဖြည့်ပေးပါ။")

    st.markdown("---")
    st.subheader("📋 အချိန်ဇယားများ ပြင်ဆင်/ဖျက်ခြင်း")
    tt_data = run_query("SELECT id, date AS \"Date\", class_type AS \"Class_Type\", class_name AS \"Class_Name\", period AS \"Period\", zoom_id AS \"Zoom_ID\", teacher_name AS \"Teacher_Name\", assistant_1 AS \"Assistant_1\", assistant_2 AS \"Assistant_2\", lesson_level AS \"Lesson_Level\", lesson_topic AS \"Lesson_Topic\" FROM timetable ORDER BY date DESC, period ASC")

    if not tt_data.empty:
        sel_all = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_tt")
        tt_data.insert(0, "Select", sel_all)
        edited_table = st.data_editor(tt_data, use_container_width=True, hide_index=True, disabled=[c for c in tt_data.columns if c != "Select"])
        selected_ids = edited_table[edited_table["Select"] == True]["id"].tolist()

        c_del, c_edit = st.columns([3, 7])
        with c_del:
            if st.button("🗑️ ရွေးချယ်ထားသည်များ ဖျက်မည်", type="secondary", disabled=len(selected_ids) == 0):
                execute_query(f"DELETE FROM timetable WHERE id IN ({','.join(['%s'] * len(selected_ids))})", tuple(selected_ids))
                run_query.clear()
                st.toast(f"🗑️ အချိန်ဇယား {len(selected_ids)} ခု ဖျက်ပြီးပါပြီ!")
                st.rerun()
        with c_edit:
            ed_id = st.selectbox("ပြင်ဆင်လိုသည့် အချိန်ဇယား ID", tt_data["id"].tolist())
            if st.button("✏️ ရွေးထားသည့် အချိန်ဇယား ပြင်မည်"):
                edit_timetable_dialog(ed_id)

# =========================================================
# PAGE 3: STUDENTS MANAGEMENT (ADMIN)
# =========================================================
elif selected_page == "👥 ကျောင်းသား စီမံခန့်ခွဲမှု":
    st.subheader("👥 ကျောင်းသားများ စီမံခန့်ခွဲမှု")
    s_c1, s_c2 = st.columns(2)
    with s_c1:
        with st.expander("➕ ကျောင်းသားအသစ် တစ်ဦးချင်း ထည့်ရန်", expanded=True):
            with st.form("stu_single_form", clear_on_submit=True):
                st_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES)
                st_class = st.text_input("တန်းခွဲ အမည်")
                st_name = st.text_input("ကျောင်းသား အမည်")
                st_age = st.number_input("အသက်", min_value=3, max_value=80, value=15)
                st_parent = st.text_input("မိဘ အမည်")
                st_phone = st.text_input("ဖုန်းနံပါတ်")
                st_social = st.text_input("မိဘ Social အကောင့်")
                st_address = st.text_area("လိပ်စာ")
                if st.form_submit_button("သိမ်းဆည်းမည်", type="primary"):
                    if st_name and st_class:
                        try:
                            execute_query(
                                """INSERT INTO students (student_name, age, class_type, class_name, parent_name, phone, social_account, address)
                                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                                (st_name.strip(), st_age, st_type, st_class.strip(), st_parent, st_phone, st_social, st_address),
                            )
                            run_query.clear()
                            st.toast("✅ ကျောင်းသားစာရင်း သိမ်းဆည်းပြီးပါပြီ!", icon="🎉")
                        except psycopg2.IntegrityError:
                            st.error("ဤအတန်းတွင် ယခုအမည်ဖြင့် ရှိပြီးသားဖြစ်နေပါသည်။")
                    else:
                        st.warning("ကျောင်းသားအမည်နှင့် အတန်း ဖြည့်သွင်းပါ။")

    with s_c2:
        with st.expander("📂 ကျောင်းသားစာရင်း Excel မှ Import"):
            up_stu = st.file_uploader("Excel ဖိုင်တင်ရန်", type=["xlsx", "xls"])
            if up_stu and st.button("📥 ကျောင်းသား Import စတင်မည်"):
                try:
                    imp_s = pd.read_excel(up_stu)
                    if {"Student_Name", "Class_Type", "Class_Name"}.issubset(set(imp_s.columns)):
                        inserted, skipped = 0, 0
                        for _, r in imp_s.iterrows():
                            try:
                                execute_query(
                                    """INSERT INTO students (student_name, age, class_type, class_name, parent_name, phone, social_account, address)
                                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                                    (str(r["Student_Name"]), int(r["Age"]) if pd.notna(r.get("Age")) else None, str(r["Class_Type"]), str(r["Class_Name"]),
                                     str(r["Parent_Name"]) if pd.notna(r.get("Parent_Name")) else None, str(r["Phone"]) if pd.notna(r.get("Phone")) else None,
                                     str(r["Social_Account"]) if pd.notna(r.get("Social_Account")) else None, str(r["Address"]) if pd.notna(r.get("Address")) else None),
                                )
                                inserted += 1
                            except psycopg2.IntegrityError:
                                skipped += 1
                        run_query.clear()
                        st.toast(f"✅ ထည့်သွင်းမှု: {inserted} | ကျော်ခဲ့သည်: {skipped}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("📋 ကျောင်းသားစာရင်း ပြင်ဆင်/ဖျက်ခြင်း")
    stu_df = run_query("SELECT id, student_name AS \"Student_Name\", age AS \"Age\", class_type AS \"Class_Type\", class_name AS \"Class_Name\", parent_name AS \"Parent_Name\", phone AS \"Phone\", social_account AS \"Social_Account\", address AS \"Address\" FROM students ORDER BY class_type, class_name, student_name")
    if not stu_df.empty:
        sel_all_stu = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_stu")
        stu_df.insert(0, "Select", sel_all_stu)
        edited_stu = st.data_editor(stu_df, use_container_width=True, hide_index=True, disabled=[c for c in stu_df.columns if c != "Select"])
        sel_stu_ids = edited_stu[edited_stu["Select"] == True]["id"].tolist()

        c_del_s, c_ed_s = st.columns([3, 7])
        with c_del_s:
            if st.button("🗑️ ရွေးထားသော ကျောင်းသားများ ဖျက်မည်", disabled=len(sel_stu_ids) == 0):
                execute_query(f"DELETE FROM students WHERE id IN ({','.join(['%s'] * len(sel_stu_ids))})", tuple(sel_stu_ids))
                run_query.clear()
                st.toast(f"🗑️ ကျောင်းသား {len(sel_stu_ids)} ဦး ဖျက်ပြီးပါပြီ!")
                st.rerun()
        with c_ed_s:
            ed_stu_id = st.selectbox("ပြင်ဆင်လိုသည့် ကျောင်းသား ID", stu_df["id"].tolist())
            if st.button("✏️ ရွေးထားသည့် ကျောင်းသား အချက်အလက် ပြင်မည်"):
                edit_student_dialog(ed_stu_id)

# =========================================================
# PAGE 4: ATTENDANCE
# =========================================================
elif selected_page == "📋 ကျောင်းခေါ်ချိန် မှတ်တမ်း":
    st.subheader("📋 နေ့စဉ် ကျောင်းခေါ်ချိန် မှတ်တမ်း")
    st_classes = run_query("SELECT DISTINCT class_type, class_name FROM students ORDER BY class_type, class_name")
    if not st_classes.empty:
        a1, a2, a3 = st.columns(3)
        with a1:
            att_date = st.date_input("ရက်စွဲ ရွေးချယ်ပါ", date.today()).strftime("%Y-%m-%d")
        with a2:
            sel_at_type = st.selectbox("ကျောင်းအမျိုးအစား", sorted(st_classes["class_type"].unique().tolist()))
        with a3:
            filtered_cn = st_classes[st_classes["class_type"] == sel_at_type]["class_name"].unique().tolist()
            sel_at_cls = st.selectbox("တန်းခွဲ", filtered_cn)

        stu_in_c = run_query("SELECT student_name, phone FROM students WHERE class_type = %s AND class_name = %s ORDER BY student_name", (sel_at_type, sel_at_cls))
        if not stu_in_c.empty:
            existing_att = run_query("SELECT student_name, status FROM attendance WHERE date = %s AND class_type = %s AND class_name = %s", (att_date, sel_at_type, sel_at_cls))
            status_map = dict(zip(existing_att["student_name"], existing_att["status"])) if not existing_att.empty else {}

            with st.form("daily_att_form"):
                saved_att = []
                statuses = ["တက်ရောက်", "ပျက်ကွက်", "ခွင့်"]
                for _, srow in stu_in_c.iterrows():
                    sname = srow["student_name"]
                    sphone = str(srow["phone"]) if pd.notna(srow["phone"]) else "-"
                    curr_st = status_map.get(sname, "တက်ရောက်")
                    idx = statuses.index(curr_st) if curr_st in statuses else 0

                    col_info, col_radio = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"**{sname}** | 📞 `{sphone}`")
                    with col_radio:
                        st_choice = st.radio(f"st_{sname}", statuses, index=idx, horizontal=True, label_visibility="collapsed")
                    saved_att.append((att_date, sel_at_type, sel_at_cls, sname, sphone, st_choice))

                if st.form_submit_button("💾 ကျောင်းခေါ်ချိန် သိမ်းဆည်းမည်", type="primary"):
                    execute_query("DELETE FROM attendance WHERE date = %s AND class_type = %s AND class_name = %s", (att_date, sel_at_type, sel_at_cls))
                    conn = get_conn()
                    try:
                        cur = conn.cursor()
                        cur.executemany("INSERT INTO attendance (date, class_type, class_name, student_name, phone, status) VALUES (%s,%s,%s,%s,%s,%s)", saved_att)
                        conn.commit()
                    finally:
                        cur.close()
                        release_conn(conn)
                    run_query.clear()
                    st.toast("✅ ကျောင်းခေါ်ချိန် အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!", icon="🎉")
        else:
            st.warning("ဤအတန်းအတွက် ကျောင်းသား မရှိသေးပါ။")
    else:
        st.info("ကျောင်းခေါ်ချိန်စစ်ရန် ကျောင်းသားစာရင်း ဦးစွာ ထည့်သွင်းပါ။")

# =========================================================
# PAGE 5: ATTENDANCE SUMMARY
# =========================================================
elif selected_page == "📊 တက်/ပျက် စာရင်းချုပ်":
    st.subheader("📊 ကျောင်းသားအင်အားနှင့် တက်/ပျက် စာရင်းချုပ်")
    rep_date = st.date_input("စစ်ဆေးလိုသည့် ရက်စွဲ", date.today()).strftime("%Y-%m-%d")
    summary_q = """
        SELECT s.class_type AS "ကျောင်းအမျိုးအစား", s.class_name AS "တန်းခွဲ",
               COUNT(s.student_name) AS "ကျောင်းသားအင်အား",
               SUM(CASE WHEN a.status = 'တက်ရောက်' THEN 1 ELSE 0 END) AS "တက်ရောက်",
               SUM(CASE WHEN a.status = 'ပျက်ကွက်' THEN 1 ELSE 0 END) AS "ပျက်ကွက်",
               SUM(CASE WHEN a.status = 'ခွင့်' THEN 1 ELSE 0 END) AS "ခွင့်",
               SUM(CASE WHEN a.status IS NULL THEN 1 ELSE 0 END) AS "စာရင်းမသွင်းရသေး"
        FROM students s
        LEFT JOIN attendance a ON s.student_name = a.student_name AND s.class_type = a.class_type AND s.class_name = a.class_name AND a.date = %s
        GROUP BY s.class_type, s.class_name
        ORDER BY s.class_type, s.class_name
    """
    rep_df = run_query(summary_q, (rep_date,))
    if not rep_df.empty:
        st.dataframe(rep_df, use_container_width=True, hide_index=True)
    else:
        st.info("အချက်အလက်များ မရှိသေးပါ။")

# =========================================================
# PAGE 6: TEACHERS MANAGEMENT (ADMIN)
# =========================================================
elif selected_page == "👨‍🏫 ဆရာ/မ စာရင်း":
    st.subheader("👨‍🏫 ဆရာ/ဆရာမ စာရင်း စီမံခန့်ခွဲမှု")
    tc1, tc2 = st.columns(2)
    with tc1:
        with st.expander("➕ ဆရာ/မ အသစ် တစ်ဦးချင်း ထည့်ရန်", expanded=True):
            with st.form("teach_single_form", clear_on_submit=True):
                t_name = st.text_input("ဆရာ/မ အမည်")
                t_phone = st.text_input("ဖုန်းနံပါတ်")
                if st.form_submit_button("သိမ်းဆည်းမည်", type="primary"):
                    if t_name:
                        try:
                            execute_query("INSERT INTO teachers (teacher_name, phone) VALUES (%s, %s)", (t_name.strip(), t_phone.strip()))
                            run_query.clear()
                            st.toast("✅ ဆရာ/မ အချက်အလက် သိမ်းဆည်းပြီးပါပြီ!", icon="🎉")
                        except psycopg2.IntegrityError:
                            st.error("ဤဆရာ/မ အမည် ရှိပြီးသားဖြစ်နေပါသည်။")
                    else:
                        st.warning("အမည် ဖြည့်သွင်းပါ။")

    with tc2:
        with st.expander("📂 ဆရာ/မ စာရင်း Excel မှ Import"):
            up_teach = st.file_uploader("Excel တင်ရန်", type=["xlsx", "xls"])
            if up_teach and st.button("📥 ဆရာ/မ Import စတင်မည်"):
                try:
                    imp_t = pd.read_excel(up_teach)
                    if "Teacher_Name" in imp_t.columns:
                        inserted, skipped = 0, 0
                        for _, r in imp_t.iterrows():
                            try:
                                execute_query("INSERT INTO teachers (teacher_name, phone) VALUES (%s, %s)", (str(r["Teacher_Name"]).strip(), str(r["Phone"]) if pd.notna(r.get("Phone")) else None))
                                inserted += 1
                            except psycopg2.IntegrityError:
                                skipped += 1
                        run_query.clear()
                        st.toast(f"✅ ထည့်သွင်းမှု: {inserted} | ကျော်ခဲ့သည်: {skipped}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("📋 ဆရာ/မ စာရင်း ပြင်ဆင်/ဖျက်ခြင်း")
    teach_df = run_query("SELECT id, teacher_name AS \"Teacher_Name\", phone AS \"Phone\" FROM teachers ORDER BY teacher_name")
    if not teach_df.empty:
        sel_all_t = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_t")
        teach_df.insert(0, "Select", sel_all_t)
        edited_t = st.data_editor(teach_df, use_container_width=True, hide_index=True, disabled=[c for c in teach_df.columns if c != "Select"])
        sel_t_ids = edited_t[edited_t["Select"] == True]["id"].tolist()

        c_del_t, c_ed_t = st.columns([3, 7])
        with c_del_t:
            if st.button("🗑️ ရွေးထားသော ဆရာ/မများ ဖျက်မည်", disabled=len(sel_t_ids) == 0):
                execute_query(f"DELETE FROM teachers WHERE id IN ({','.join(['%s'] * len(sel_t_ids))})", tuple(sel_t_ids))
                run_query.clear()
                st.toast(f"🗑️ ဆရာ/မ {len(sel_t_ids)} ဦး ဖျက်ပြီးပါပြီ!")
                st.rerun()
        with c_ed_t:
            ed_t_id = st.selectbox("ပြင်ဆင်လိုသည့် ဆရာ/မ ID", teach_df["id"].tolist())
            if st.button("✏️ ရွေးထားသည့် ဆရာ/မ အချက်အလက် ပြင်မည်"):
                edit_teacher_dialog(ed_t_id)

# =========================================================
# PAGE 7: LESSONS MANAGEMENT (ADMIN)
# =========================================================
elif selected_page == "📖 သင်ခန်းစာများ စီမံရန်":
    st.subheader("📖 သင်ခန်းစာများ စီမံခန့်ခွဲမှု")
    lc1, lc2 = st.columns(2)
    with lc1:
        with st.expander("➕ သင်ခန်းစာ အသစ်ထည့်ရန်", expanded=True):
            with st.form("lsn_single_form", clear_on_submit=True):
                l_lvl = st.text_input("Level")
                l_topic = st.text_input("သင်ခန်းစာ အမည်")
                if st.form_submit_button("သိမ်းဆည်းမည်", type="primary"):
                    if l_lvl and l_topic:
                        try:
                            execute_query("INSERT INTO lessons (level, lesson_topic) VALUES (%s, %s)", (l_lvl.strip(), l_topic.strip()))
                            run_query.clear()
                            st.toast("✅ သင်ခန်းစာ အသစ် ထည့်သွင်းပြီးပါပြီ!", icon="🎉")
                        except psycopg2.IntegrityError:
                            st.error("ဤ Level တွင် ယခုသင်ခန်းစာ ရှိပြီးသားဖြစ်နေပါသည်။")
                    else:
                        st.warning("Level နှင့် သင်ခန်းစာအမည် ဖြည့်သွင်းပါ။")

    with lc2:
        with st.expander("📂 သင်ခန်းစာများ Excel မှ Import"):
            up_lsn = st.file_uploader("Excel တင်ရန်", type=["xlsx", "xls"])
            if up_lsn and st.button("📥 သင်ခန်းစာ Import စတင်မည်"):
                try:
                    imp_l = pd.read_excel(up_lsn)
                    if {"Level", "Lesson_Topic"}.issubset(set(imp_l.columns)):
                        inserted, skipped = 0, 0
                        for _, r in imp_l.iterrows():
                            try:
                                execute_query("INSERT INTO lessons (level, lesson_topic) VALUES (%s, %s)", (str(r["Level"]).strip(), str(r["Lesson_Topic"]).strip()))
                                inserted += 1
                            except psycopg2.IntegrityError:
                                skipped += 1
                        run_query.clear()
                        st.toast(f"✅ ထည့်သွင်းမှု: {inserted} | ကျော်ခဲ့သည်: {skipped}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("📋 သင်ခန်းစာများ ပြင်ဆင်/ဖျက်ခြင်း")
    lsn_df = run_query("SELECT id, level AS \"Level\", lesson_topic AS \"Lesson_Topic\" FROM lessons ORDER BY level, id")
    if not lsn_df.empty:
        sel_all_l = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_l")
        lsn_df.insert(0, "Select", sel_all_l)
        edited_l = st.data_editor(lsn_df, use_container_width=True, hide_index=True, disabled=[c for c in lsn_df.columns if c != "Select"])
        sel_l_ids = edited_l[edited_l["Select"] == True]["id"].tolist()

        c_del_l, c_ed_l = st.columns([3, 7])
        with c_del_l:
            if st.button("🗑️ ရွေးထားသော သင်ခန်းစာများ ဖျက်မည်", disabled=len(sel_l_ids) == 0):
                execute_query(f"DELETE FROM lessons WHERE id IN ({','.join(['%s'] * len(sel_l_ids))})", tuple(sel_l_ids))
                run_query.clear()
                st.toast(f"🗑️ သင်ခန်းစာ {len(sel_l_ids)} ခု ဖျက်ပြီးပါပြီ!")
                st.rerun()
        with c_ed_l:
            ed_l_id = st.selectbox("ပြင်ဆင်လိုသည့် သင်ခန်းစာ ID", lsn_df["id"].tolist())
            if st.button("✏️ ရွေးထားသည့် သင်ခန်းစာ ပြင်မည်"):
                edit_lesson_dialog(ed_l_id)

# =========================================================
# PAGE 8: ANALYTICS (ADMIN)
# =========================================================
elif selected_page == "📈 Analytics Dashboard":
    st.subheader("📈 We Are Genius - Academic Analytics Dashboard")
    total_students = run_query("SELECT COUNT(*) AS c FROM students").iloc[0]["c"]
    total_teachers = run_query("SELECT COUNT(*) AS c FROM teachers").iloc[0]["c"]
    total_schedules = run_query("SELECT COUNT(*) AS c FROM timetable").iloc[0]["c"]
    total_lessons = run_query("SELECT COUNT(*) AS c FROM lessons").iloc[0]["c"]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">👨‍🎓 Total Students</div><div class="stat-val">{total_students}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">👨‍🏫 Faculty Teachers</div><div class="stat-val">{total_teachers}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">📅 Scheduled Classes</div><div class="stat-val">{total_schedules}</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="stat-card"><div class="stat-label">📖 Active Lessons</div><div class="stat-val">{total_lessons}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        st.markdown("##### 📊 အတန်းတက် / ပျက် / ခွင့် နှုန်းထား")
        att_stat_df = run_query("SELECT status AS \"အခြေအနေ\", COUNT(*) AS \"ဦးရေ\" FROM attendance GROUP BY status ORDER BY status")
        if not att_stat_df.empty:
            st.bar_chart(att_stat_df.set_index("အခြေအနေ"), use_container_width=True)
        else:
            st.info("ကျောင်းခေါ်ချိန် မှတ်တမ်းများ မရှိသေးပါ။")
    with chart_c2:
        st.markdown("##### 👨‍🏫 ဆရာ/မ တစ်ဦးချင်း သင်ကြားချိန်")
        teach_stat_df = run_query("""
            SELECT teacher AS "Teacher", COUNT(*) AS "စာသင်ချိန်_အရေအတွက်" FROM (
                SELECT teacher_name AS teacher FROM timetable WHERE teacher_name IS NOT NULL
                UNION ALL SELECT assistant_1 AS teacher FROM timetable WHERE assistant_1 IS NOT NULL
                UNION ALL SELECT assistant_2 AS teacher FROM timetable WHERE assistant_2 IS NOT NULL
            ) AS teacher_data GROUP BY teacher ORDER BY COUNT(*) DESC
        """)
        if not teach_stat_df.empty:
            st.bar_chart(teach_stat_df.set_index("Teacher"), use_container_width=True)
        else:
            st.info("အချိန်ဇယား အချက်အလက်များ မရှိသေးပါ။")

# =========================================================
# PAGE 9: USER MANAGEMENT (ADMIN)
# =========================================================
elif selected_page == "🔐 User Accounts":
    st.subheader("🔐 User Account စီမံခန့်ခွဲမှု")
    with st.form("create_user_form", clear_on_submit=True):
        u1, u2 = st.columns(2)
        with u1:
            new_username = st.text_input("Username")
            new_role = st.selectbox("Role", ["Teacher", "Admin"])
        with u2:
            new_password = st.text_input("Password", type="password")
            new_password2 = st.text_input("Confirm Password", type="password")

        if st.form_submit_button("➕ User Account ဖန်တီးမည်", type="primary", use_container_width=True):
            if not new_username.strip() or not new_password:
                st.warning("Username နှင့် Password ဖြည့်ပေးပါ။")
            elif new_password != new_password2:
                st.error("Password နှစ်ခု မတူပါ။")
            elif len(new_password) < 8:
                st.error("Password သည် အနည်းဆုံး 8 characters ရှိရပါမည်။")
            else:
                try:
                    execute_query(
                        "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
                        (new_username.strip(), hash_password(new_password), new_role),
                    )
                    run_query.clear()
                    st.toast(f"✅ {new_role} account အသစ် ဖန်တီးပြီးပါပြီ!", icon="🎉")
                except psycopg2.IntegrityError:
                    st.error("ဤ Username ရှိပြီးသား ဖြစ်နေပါသည်။")

    st.markdown("---")
    users_df = run_query("SELECT id, username, role, active, created_at FROM users ORDER BY role, username")
    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        selected_user_id = st.selectbox("ပြောင်းလဲလိုသော User ID", users_df["id"].tolist())
        selected_user = users_df[users_df["id"] == selected_user_id].iloc[0]

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Active / Inactive ပြောင်းမည်", use_container_width=True):
                new_active = not bool(selected_user["active"])
                execute_query("UPDATE users SET active = %s WHERE id = %s", (new_active, int(selected_user_id)))
                run_query.clear()
                st.toast("✅ Account Status ပြောင်းလဲပြီးပါပြီ!")
                st.rerun()
        with c2:
            reset_password = st.text_input("Password အသစ်", type="password")
            if st.button("🔑 Password ပြောင်းမည်", use_container_width=True):
                if len(reset_password) < 8:
                    st.error("Password သည် အနည်းဆုံး 8 characters ရှိရပါမည်။")
                else:
                    execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(reset_password), int(selected_user_id)))
                    run_query.clear()
                    st.toast("✅ Password ပြောင်းလဲပြီးပါပြီ!")
