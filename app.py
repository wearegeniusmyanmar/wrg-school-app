import hashlib
import hmac
import os
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
# CUSTOM CSS (DARK & LIGHT MODE ADAPTIVE)
# =========================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Padauk:wght@400;700&display=swap');

footer {
    display: none !important;
}

.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1350px;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', 'Padauk', sans-serif;
}

/* Titles with High Contrast */
.brand-title-large {
    font-family: 'Cinzel', serif;
    font-size: 2.5rem;
    font-weight: 900;
    letter-spacing: 2px;
    background: linear-gradient(120deg, #10b981 0%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 10px;
    margin-bottom: 2px;
    line-height: 1.15;
    text-align: center;
}

.brand-subtitle-large {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--text-color, #10b981);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 8px;
    text-align: center;
}

.app-badge-large {
    display: inline-block;
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    font-size: 0.88rem;
    font-weight: 700;
    padding: 6px 18px;
    border-radius: 20px;
    border: 1px solid rgba(16, 185, 129, 0.4);
    letter-spacing: 0.5px;
    margin-bottom: 20px;
}

/* Adaptive Stat Cards */
.stat-card {
    background-color: var(--secondary-background-color, rgba(255, 255, 255, 0.05));
    border: 1.5px solid rgba(16, 185, 129, 0.35);
    border-radius: 18px;
    padding: 22px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-4px);
    border-color: #10b981;
    box-shadow: 0 8px 20px rgba(16, 185, 129, 0.25);
}

.stat-val {
    font-size: 2.5rem;
    font-weight: 900;
    color: #10b981;
    margin: 6px 0;
}

.stat-label {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-color, #94a3b8);
}

/* Tab Bar Colors (Always Visible Text) */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: var(--secondary-background-color, rgba(16, 185, 129, 0.08));
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(16, 185, 129, 0.25);
    margin-bottom: 1.5rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: var(--text-color, inherit) !important;
    font-weight: 600;
    padding: 8px 18px;
}

.stTabs [aria-selected="true"] {
    background-color: #10b981 !important;
    color: #ffffff !important;
    font-weight: 700;
}

.stTabs [data-baseweb="tab"] p {
    color: inherit !important;
}

/* Expander Style */
div[data-testid="stExpander"] {
    border-radius: 14px;
    border: 1px solid rgba(16, 185, 129, 0.25);
    background-color: var(--secondary-background-color, transparent);
}
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
    st.error("DATABASE_URL မသတ်မှတ်ရသေးပါ။ Streamlit Secrets တွင် ထည့်သွင်းပါ။")
    st.stop()

CLASS_TYPES = ["ကိုယ်ပိုင်ကျောင်းများ", "On Campus", "Zoom Online"]

# =========================================================
# DATABASE CONNECTION POOLING & CACHING
# =========================================================
@st.cache_resource
def get_db_pool():
    return ThreadedConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

def get_conn():
    return get_db_pool().getconn()

def release_conn(conn):
    get_db_pool().putconn(conn)

@st.cache_data(ttl=60, show_spinner=False)
def run_query(query, params=()):
    conn = get_conn()
    try:
        return pd.read_sql_query(query, conn, params=params)
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
# DATABASE SETUP (ONE-TIME ONLY)
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
            admin_u = get_setting("ADMIN_USERNAME", "admin").strip()
            admin_p = get_setting("ADMIN_PASSWORD", "admin12345")
            teacher_u = get_setting("TEACHER_USERNAME", "teacher").strip()
            teacher_p = get_setting("TEACHER_PASSWORD", "teacher12345")
            if admin_u and admin_p:
                cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'Admin') ON CONFLICT DO NOTHING", (admin_u, hash_password(admin_p)))
            if teacher_u and teacher_p:
                cur.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'Teacher') ON CONFLICT DO NOTHING", (teacher_u, hash_password(teacher_p)))
            conn.commit()
    finally:
        cur.close()
        release_conn(conn)
    return True

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
    except Exception:
        return False

def authenticate_user(username, password, role):
    df = run_query("SELECT username, role, password_hash, active FROM users WHERE username = %s AND role = %s", (username.strip(), role))
    if df.empty or not bool(df.iloc[0]["active"]):
        return False
    return verify_password(password, df.iloc[0]["password_hash"])

initialize_database()

# =========================================================
# DIALOGS
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
                st.toast("✅ အချိန်ဇယား ပြင်ဆင်ပြီးပါပြီ!")
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
            st.image("logo.png", use_container_width=True)
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
# TOP HEADER BAR
# =========================================================
h_col1, h_col2, h_col3 = st.columns([1, 6.5, 1.8])
with h_col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=75)
with h_col2:
    st.markdown(
        """<h2 style='margin:0; font-family:Cinzel, serif; font-weight:900; color:#059669;'>WE ARE GENIUS - BASIC SCIENCE SCHOOL</h2>
           <p style='margin:0; font-weight:700; color:#0d9488; font-size:1.02rem;'>School Management & Academic Timetable System</p>""",
        unsafe_allow_html=True,
    )
with h_col3:
    st.markdown(f"👤 **{st.session_state.username}** ({st.session_state.role})")
    if st.button("🚪 Logout (ထွက်မည်)", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

# =========================================================
# TABS DECLARATION (HORIZONTAL BAR RESTORED)
# =========================================================
if st.session_state.role == "Admin":
    tab_names = [
        "📅 အပတ်စဉ် အချိန်ဇယား",
        "➕ အချိန်ဇယား ရေးဆွဲ/စီမံ",
        "👥 ကျောင်းသား စီမံခန့်ခွဲမှု",
        "📋 နေ့စဉ် ကျောင်းခေါ်ချိန်",
        "📊 အင်အားနှင့် တက်/ပျက်",
        "👨‍🏫 ဆရာ/မ စာရင်း",
        "📖 သင်ခန်းစာများ စီမံရန်",
        "📈 Analytics Dashboard",
        "🔐 User Account စီမံရန်",
    ]
else:
    tab_names = [
        "📅 အပတ်စဉ် အချိန်ဇယား",
        "📋 နေ့စဉ် ကျောင်းခေါ်ချိန်",
        "📊 အင်အားနှင့် တက်/ပျက်",
    ]

tabs = st.tabs(tab_names)

# =========================================================
# TAB 1 - VIEW TIMETABLE (WITH CLASS NAME FILTER)
# =========================================================
with tabs[0]:
    st.subheader("🔍 အပတ်စဉ် အချိန်ဇယား ရှာဖွေကြည့်ရှုရန်")

    # Dropdown Filter များကို Column ၅ ခုဖြင့် နေရာချထားခြင်း
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        view_type = st.selectbox("ကျောင်းအမျိုးအစား", ["အားလုံး"] + CLASS_TYPES, key="v_t_filter")

    with c2:
        # ရွေးထားသော ကျောင်းအမျိုးအစားအလိုက် Class Name များကို Query လုပ်ခြင်း
        if view_type != "အားလုံး":
            class_filter_df = run_query(
                """
                SELECT DISTINCT class_name AS "Class_Name" 
                FROM timetable 
                WHERE class_type = %s AND class_name IS NOT NULL 
                ORDER BY class_name
                """,
                (view_type,),
            )
        else:
            class_filter_df = run_query(
                """
                SELECT DISTINCT class_name AS "Class_Name" 
                FROM timetable 
                WHERE class_name IS NOT NULL 
                ORDER BY class_name
                """
            )
        class_names = class_filter_df["Class_Name"].dropna().astype(str).tolist()
        view_c = st.selectbox("တန်းခွဲ (Class Name)", ["အားလုံး"] + class_names, key="v_c_name")

    with c3:
        teacher_filter_df = run_query(
            """
            SELECT DISTINCT teacher_name AS "Teacher_Name" 
            FROM teachers 
            WHERE teacher_name IS NOT NULL 
            ORDER BY teacher_name
            """
        )
        teacher_names = teacher_filter_df["Teacher_Name"].dropna().astype(str).tolist()
        t_list = ["အားလုံး"] + teacher_names
        view_t = st.selectbox("ဆရာ/မ အမည်", t_list, key="v_t_name")

    with c4:
        start_w = st.date_input(
            "စတင်မည့်ရက်",
            date.today() - timedelta(days=date.today().weekday()),
            key="v_s_date",
        )

    with c5:
        end_w = st.date_input("ပြီးဆုံးမည့်ရက်", start_w + timedelta(days=6), key="v_e_date")

    # Database Query တည်ဆောက်ခြင်း
    q = """
        SELECT 
            date AS "Date", 
            class_type AS "Class_Type", 
            class_name AS "Class_Name", 
            period AS "Period", 
            zoom_id AS "Zoom_ID", 
            teacher_name AS "Teacher_Name", 
            assistant_1 AS "Assistant_1", 
            assistant_2 AS "Assistant_2", 
            lesson_level AS "Lesson_Level", 
            lesson_topic AS "Lesson_Topic" 
        FROM timetable 
        WHERE date BETWEEN %s AND %s
    """
    p = [start_w.strftime("%Y-%m-%d"), end_w.strftime("%Y-%m-%d")]

    if view_type != "အားလုံး":
        q += " AND class_type = %s"
        p.append(view_type)

    # Class Name Filter ထည့်သွင်းခြင်း
    if view_c != "အားလုံး":
        q += " AND class_name = %s"
        p.append(view_c)

    if view_t != "အားလုံး":
        q += " AND (teacher_name = %s OR assistant_1 = %s OR assistant_2 = %s)"
        p.extend([view_t, view_t, view_t])

    q += " ORDER BY date ASC, period ASC"

    res = run_query(q, tuple(p))

    if not res.empty:
        st.dataframe(res, use_container_width=True, hide_index=True)
    else:
        st.info("ရွေးချယ်ထားသော အချက်အလက်များနှင့် ကိုက်ညီသည့် အချိန်ဇယား မရှိသေးပါ။")
# =========================================================
# ADMIN ONLY TABS
# =========================================================
if st.session_state.role == "Admin":

    # --- TAB 2: TIMETABLE MANAGEMENT ---
    with tabs[1]:
        st.subheader("➕ အချိန်ဇယား အသစ်ထည့်သွင်းရန်")
        teachers = run_query("SELECT teacher_name FROM teachers ORDER BY teacher_name")["teacher_name"].dropna().tolist()
        levels_avail = run_query("SELECT DISTINCT level FROM lessons ORDER BY level")["level"].dropna().tolist()

        if not levels_avail:
            st.warning("⚠️ သင်ခန်းစာ Level များ မရှိသေးပါ။ ဦးစွာ 'သင်ခန်းစာများ စီမံရန်' Tab တွင် ထည့်သွင်းပါ။")
        else:
            with st.form("adm_tt_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    in_date = st.date_input("ရက်စွဲ (Date)", date.today(), key="adm_in_date").strftime("%Y-%m-%d")
                    in_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, key="adm_in_type")
                    in_class = st.text_input("တန်းခွဲ", key="adm_in_class")
                    in_period = st.text_input("စာသင်ချိန်", key="adm_in_period")
                with c2:
                    in_zoom = st.text_input("Zoom ID / Link", key="adm_in_zoom")
                    in_t = st.selectbox("Lead Teacher", ["ရွေးချယ်ပါ"] + teachers, key="adm_in_t")
                    in_a1 = st.selectbox("Assistant 1", ["မရှိပါ"] + teachers, key="adm_in_a1")
                    in_a2 = st.selectbox("Assistant 2", ["မရှိပါ"] + teachers, key="adm_in_a2")
                with c3:
                    in_lvl = st.selectbox("Level", levels_avail, key="adm_in_lvl")
                    lessons = run_query("SELECT lesson_topic FROM lessons WHERE level = %s ORDER BY id", (in_lvl,))["lesson_topic"].dropna().tolist()
                    in_top = st.selectbox("သင်ကြားရမည့် သင်ခန်းစာ", lessons if lessons else ["မရှိပါ"], key="adm_in_top")

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
                            st.rerun()
                        except psycopg2.IntegrityError:
                            st.error("ယခု အချိန်ဇယား ရှိပြီးသားဖြစ်နေပါသည်။")
                    else:
                        st.warning("အချက်အလက်များကို ပြည့်စုံစွာ ဖြည့်ပေးပါ။")

            st.markdown("---")
            st.subheader("📂 အချိန်ဇယား Excel မှ Import ပြုလုပ်ရန်")
            up_tt = st.file_uploader("Excel တင်ရန်", type=["xlsx", "xls"], key="adm_up_tt")
            if up_tt and st.button("📥 အချိန်ဇယား Import စတင်မည်"):
                try:
                    imp_df = pd.read_excel(up_tt)
                    if {"Date", "Class_Type", "Class_Name", "Period", "Teacher_Name", "Lesson_Level", "Lesson_Topic"}.issubset(set(imp_df.columns)):
                        inserted, skipped = 0, 0
                        for _, r in imp_df.iterrows():
                            try:
                                execute_query(
                                    """INSERT INTO timetable (date, class_type, class_name, period, zoom_id, teacher_name, assistant_1, assistant_2, lesson_level, lesson_topic)
                                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                    (str(r["Date"]), str(r["Class_Type"]), str(r["Class_Name"]), str(r["Period"]),
                                     str(r["Zoom_ID"]) if pd.notna(r.get("Zoom_ID")) else None, str(r["Teacher_Name"]),
                                     str(r["Assistant_1"]) if pd.notna(r.get("Assistant_1")) else None, str(r["Assistant_2"]) if pd.notna(r.get("Assistant_2")) else None,
                                     str(r["Lesson_Level"]), str(r["Lesson_Topic"])),
                                )
                                inserted += 1
                            except psycopg2.IntegrityError:
                                skipped += 1
                        run_query.clear()
                        st.toast(f"✅ ထည့်သွင်းမှု: {inserted} | ကျော်ခဲ့သည်: {skipped}")
                        st.rerun()
                    else:
                        st.error("Excel ကော်လံများ မမှန်ပါ။")
                except Exception as e:
                    st.error(f"Error: {e}")

            st.markdown("---")
            st.subheader("📋 အချိန်ဇယားများ ပြင်ဆင်/ဖျက်ခြင်း")
            tt_data = run_query("SELECT id, date AS \"Date\", class_type AS \"Class_Type\", class_name AS \"Class_Name\", period AS \"Period\", zoom_id AS \"Zoom_ID\", teacher_name AS \"Teacher_Name\", assistant_1 AS \"Assistant_1\", assistant_2 AS \"Assistant_2\", lesson_level AS \"Lesson_Level\", lesson_topic AS \"Lesson_Topic\" FROM timetable ORDER BY date DESC, period ASC")
            if not tt_data.empty:
                sel_all_tt = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_tt")
                tt_data.insert(0, "Select", sel_all_tt)
                edited_table = st.data_editor(tt_data, use_container_width=True, hide_index=True, key="tt_batch_edit", disabled=[col for col in tt_data.columns if col != "Select"])
                selected_ids = edited_table[edited_table["Select"] == True]["id"].tolist()

                c_del, c_edit = st.columns([3, 7])
                with c_del:
                    if st.button("🗑️ ရွေးချယ်ထားသည်များ ဖျက်မည်", type="secondary", disabled=len(selected_ids) == 0):
                        execute_query(f"DELETE FROM timetable WHERE id IN ({','.join(['%s'] * len(selected_ids))})", tuple(selected_ids))
                        run_query.clear()
                        st.toast(f"🗑️ အချိန်ဇယား {len(selected_ids)} ခု ဖျက်ပြီးပါပြီ!")
                        st.rerun()
                with c_edit:
                    ed_id = st.selectbox("ပြင်ဆင်လိုသည့် အချိန်ဇယား ID", tt_data["id"].tolist(), key="adm_ed_tt_id")
                    if st.button("✏️ ရွေးထားသည့် အချိန်ဇယား ပြင်မည်"):
                        edit_timetable_dialog(ed_id)

    # --- TAB 3: STUDENTS ---
    with tabs[2]:
        st.subheader("👥 ကျောင်းသားများ စီမံခန့်ခွဲမှု")
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            with st.expander("➕ ကျောင်းသားအသစ် တစ်ဦးချင်း ထည့်ရန်"):
                with st.form("stu_single_form", clear_on_submit=True):
                    st_type = st.selectbox("ကျောင်းအမျိုးအစား", CLASS_TYPES, key="adm_st_type")
                    st_class = st.text_input("တန်းခွဲ အမည်", key="adm_st_class")
                    st_name = st.text_input("ကျောင်းသား အမည်", key="adm_st_name")
                    st_age = st.number_input("အသက်", min_value=3, max_value=80, value=15, key="adm_st_age")
                    st_parent = st.text_input("မိဘ အမည်", key="adm_st_parent")
                    st_phone = st.text_input("ဖုန်းနံပါတ်", key="adm_st_phone")
                    st_social = st.text_input("မိဘ Social အကောင့်", key="adm_st_social")
                    st_address = st.text_area("လိပ်စာ", key="adm_st_address")
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
                                st.rerun()
                            except psycopg2.IntegrityError:
                                st.error("ဤအတန်းတွင် ယခုအမည်ဖြင့် ကျောင်းသား ရှိပြီးသားဖြစ်နေပါသည်။")
                        else:
                            st.warning("ကျောင်းသားအမည်နှင့် အတန်း ဖြည့်သွင်းပါ။")

        with s_c2:
            with st.expander("📂 ကျောင်းသားစာရင်း Excel မှ Import"):
                up_stu = st.file_uploader("Excel ဖိုင်တင်ရန်", type=["xlsx", "xls"], key="adm_up_stu")
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
                        else:
                            st.error("Excel တွင် Student_Name, Class_Type, Class_Name ကော်လံများ ပါဝင်ရပါမည်။")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 ကျောင်းသားစာရင်း ပြင်ဆင်/ဖျက်ခြင်း")
        stu_df = run_query("SELECT id, student_name AS \"Student_Name\", age AS \"Age\", class_type AS \"Class_Type\", class_name AS \"Class_Name\", parent_name AS \"Parent_Name\", phone AS \"Phone\", social_account AS \"Social_Account\", address AS \"Address\" FROM students ORDER BY class_type, class_name, student_name")
        if not stu_df.empty:
            sel_all_stu = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_stu")
            stu_df.insert(0, "Select", sel_all_stu)
            edited_stu = st.data_editor(stu_df, use_container_width=True, hide_index=True, key="adm_stu_batch_edit", disabled=[col for col in stu_df.columns if col != "Select"])
            sel_stu_ids = edited_stu[edited_stu["Select"] == True]["id"].tolist()

            col_s_del, col_s_edit = st.columns([3, 7])
            with col_s_del:
                if st.button("🗑️ ရွေးထားသော ကျောင်းသားများ ဖျက်မည်", disabled=len(sel_stu_ids) == 0):
                    execute_query(f"DELETE FROM students WHERE id IN ({','.join(['%s'] * len(sel_stu_ids))})", tuple(sel_stu_ids))
                    run_query.clear()
                    st.toast(f"🗑️ ကျောင်းသား {len(sel_stu_ids)} ဦး ဖျက်ပြီးပါပြီ!")
                    st.rerun()
            with col_s_edit:
                ed_stu_id = st.selectbox("ပြင်ဆင်လိုသည့် ကျောင်းသား ID", stu_df["id"].tolist(), key="adm_ed_stu_id")
                if st.button("✏️ ရွေးထားသည့် ကျောင်းသား အချက်အလက် ပြင်မည်"):
                    edit_student_dialog(ed_stu_id)

    att_tab = tabs[3]
    rep_tab = tabs[4]

    # --- TAB 6: TEACHERS ---
    with tabs[5]:
        st.subheader("👨‍🏫 ဆရာ/ဆရာမ စာရင်း စီမံခန့်ခွဲမှု")
        tc1, tc2 = st.columns(2)
        with tc1:
            with st.expander("➕ ဆရာ/မ အသစ် တစ်ဦးချင်း ထည့်ရန်"):
                with st.form("teach_single_form", clear_on_submit=True):
                    t_name = st.text_input("ဆရာ/မ အမည်")
                    t_phone = st.text_input("ဖုန်းနံပါတ်")
                    if st.form_submit_button("သိမ်းဆည်းမည်", type="primary"):
                        if t_name:
                            try:
                                execute_query("INSERT INTO teachers (teacher_name, phone) VALUES (%s, %s)", (t_name.strip(), t_phone.strip()))
                                run_query.clear()
                                st.toast("✅ ဆရာ/မ အချက်အလက် သိမ်းဆည်းပြီးပါပြီ!", icon="🎉")
                                st.rerun()
                            except psycopg2.IntegrityError:
                                st.error("ဤဆရာ/မ အမည် ရှိပြီးသားဖြစ်နေပါသည်။")
                        else:
                            st.warning("အမည် ဖြည့်သွင်းပါ။")

        with tc2:
            with st.expander("📂 ဆရာ/မ စာရင်း Excel မှ Import"):
                up_teach = st.file_uploader("Excel တင်ရန်", type=["xlsx", "xls"], key="adm_up_teach")
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
                        else:
                            st.error("Excel တွင် Teacher_Name ကော်လံ ပါဝင်ရပါမည်။")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 ဆရာ/မ စာရင်း ပြင်ဆင်/ဖျက်ခြင်း")
        teach_df = run_query("SELECT id, teacher_name AS \"Teacher_Name\", phone AS \"Phone\" FROM teachers ORDER BY teacher_name")
        if not teach_df.empty:
            sel_all_t = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_t")
            teach_df.insert(0, "Select", sel_all_t)
            edited_t = st.data_editor(teach_df, use_container_width=True, hide_index=True, key="adm_teach_batch_edit", disabled=[col for col in teach_df.columns if col != "Select"])
            sel_t_ids = edited_t[edited_t["Select"] == True]["id"].tolist()

            col_t_del, col_t_edit = st.columns([3, 7])
            with col_t_del:
                if st.button("🗑️ ရွေးထားသော ဆရာ/မများ ဖျက်မည်", disabled=len(sel_t_ids) == 0):
                    execute_query(f"DELETE FROM teachers WHERE id IN ({','.join(['%s'] * len(sel_t_ids))})", tuple(sel_t_ids))
                    run_query.clear()
                    st.toast(f"🗑️ ဆရာ/မ {len(sel_t_ids)} ဦး ဖျက်ပြီးပါပြီ!")
                    st.rerun()
            with col_t_edit:
                ed_t_id = st.selectbox("ပြင်ဆင်လိုသည့် ဆရာ/မ ID", teach_df["id"].tolist(), key="adm_ed_t_id")
                if st.button("✏️ ရွေးထားသည့် ဆရာ/မ အချက်အလက် ပြင်မည်"):
                    edit_teacher_dialog(ed_t_id)

    # --- TAB 7: LESSONS ---
    with tabs[6]:
        st.subheader("📖 သင်ခန်းစာများ စီမံခန့်ခွဲမှု")
        lc1, lc2 = st.columns(2)
        with lc1:
            with st.expander("➕ သင်ခန်းစာ အသစ်ထည့်ရန်"):
                with st.form("lsn_single_form", clear_on_submit=True):
                    l_lvl = st.text_input("Level")
                    l_topic = st.text_input("သင်ခန်းစာ အမည်")
                    if st.form_submit_button("သိမ်းဆည်းမည်", type="primary"):
                        if l_lvl and l_topic:
                            try:
                                execute_query("INSERT INTO lessons (level, lesson_topic) VALUES (%s, %s)", (l_lvl.strip(), l_topic.strip()))
                                run_query.clear()
                                st.toast("✅ သင်ခန်းစာ အသစ် ထည့်သွင်းပြီးပါပြီ!", icon="🎉")
                                st.rerun()
                            except psycopg2.IntegrityError:
                                st.error("ဤ Level တွင် ယခုသင်ခန်းစာ ရှိပြီးသားဖြစ်နေပါသည်။")
                        else:
                            st.warning("Level နှင့် သင်ခန်းစာအမည် ဖြည့်သွင်းပါ။")

        with lc2:
            with st.expander("📂 သင်ခန်းစာများ Excel မှ Import"):
                up_lsn = st.file_uploader("Excel တင်ရန်", type=["xlsx", "xls"], key="adm_up_lsn")
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
                        else:
                            st.error("Excel တွင် Level နှင့် Lesson_Topic ကော်လံများ ပါဝင်ရပါမည်။")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("📋 သင်ခန်းစာများ ပြင်ဆင်/ဖျက်ခြင်း")
        lsn_df = run_query("SELECT id, level AS \"Level\", lesson_topic AS \"Lesson_Topic\" FROM lessons ORDER BY level, id")
        if not lsn_df.empty:
            sel_all_l = st.checkbox("☑️ အားလုံးရွေးမည်", key="chk_all_l")
            lsn_df.insert(0, "Select", sel_all_l)
            edited_l = st.data_editor(lsn_df, use_container_width=True, hide_index=True, key="adm_lsn_batch_edit", disabled=[col for col in lsn_df.columns if col != "Select"])
            sel_l_ids = edited_l[edited_l["Select"] == True]["id"].tolist()

            col_l_del, col_l_edit = st.columns([3, 7])
            with col_l_del:
                if st.button("🗑️ ရွေးထားသော သင်ခန်းစာများ ဖျက်မည်", disabled=len(sel_l_ids) == 0):
                    execute_query(f"DELETE FROM lessons WHERE id IN ({','.join(['%s'] * len(sel_l_ids))})", tuple(sel_l_ids))
                    run_query.clear()
                    st.toast(f"🗑️ သင်ခန်းစာ {len(sel_l_ids)} ခု ဖျက်ပြီးပါပြီ!")
                    st.rerun()
            with col_l_edit:
                ed_l_id = st.selectbox("ပြင်ဆင်လိုသည့် သင်ခန်းစာ ID", lsn_df["id"].tolist(), key="adm_ed_l_id")
                if st.button("✏️ ရွေးထားသည့် သင်ခန်းစာ ပြင်မည်"):
                    edit_lesson_dialog(ed_l_id)
        else:
            st.info("သင်ခန်းစာ အချက်အလက်များ မရှိသေးပါ။")

    # --- TAB 8: ANALYTICS ---
    with tabs[7]:
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

        st.markdown("---")
        chart_c3, chart_c4 = st.columns(2)
        with chart_c3:
            st.markdown("##### 🏫 သင်ကြားမှု စနစ်အလိုက် ကျောင်းသား အင်အား")
            class_dist_df = run_query("SELECT class_type AS \"Class_Type\", COUNT(*) AS \"ကျောင်းသားဦးရေ\" FROM students GROUP BY class_type ORDER BY class_type")
            if not class_dist_df.empty:
                st.bar_chart(class_dist_df.set_index("Class_Type"), use_container_width=True)
            else:
                st.info("ကျောင်းသားစာရင်း မရှိသေးပါ။")

        with chart_c4:
            st.markdown("##### 📖 Level အလိုက် သင်ခန်းစာ အရေအတွက်")
            lsn_dist_df = run_query("SELECT level AS \"Level\", COUNT(*) AS \"သင်ခန်းစာ အရေအတွက်\" FROM lessons GROUP BY level ORDER BY level")
            if not lsn_dist_df.empty:
                st.bar_chart(lsn_dist_df.set_index("Level"), use_container_width=True)
            else:
                st.info("သင်ခန်းစာ စာရင်း မရှိသေးပါ။")

    # --- TAB 9: USER MANAGEMENT ---
    with tabs[8]:
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
                        st.rerun()
                    except psycopg2.IntegrityError:
                        st.error("ဤ Username ရှိပြီးသား ဖြစ်နေပါသည်။")

        st.markdown("---")
        users_df = run_query("SELECT id, username, role, active, created_at FROM users ORDER BY role, username")
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True, hide_index=True)
            selected_user_id = st.selectbox("ပြောင်းလဲလိုသော User ID", users_df["id"].tolist(), key="selected_user_id")
            selected_user = users_df[users_df["id"] == selected_user_id].iloc[0]

            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 Active / Inactive ပြောင်းမည်", use_container_width=True):
                    new_active = not bool(selected_user["active"])
                    execute_query("UPDATE users SET active = %s WHERE id = %s", (new_active, int(selected_user_id)))
                    run_query.clear()
                    st.toast("✅ Account Status ပြောင်းလဲပြီးပါပြီ!", icon="🎉")
                    st.rerun()
            with c2:
                reset_password = st.text_input("Password အသစ်", type="password", key="reset_password")
                if st.button("🔑 Password ပြောင်းမည်", use_container_width=True):
                    if len(reset_password) < 8:
                        st.error("Password သည် အနည်းဆုံး 8 characters ရှိရပါမည်။")
                    else:
                        execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(reset_password), int(selected_user_id)))
                        run_query.clear()
                        st.toast("✅ Password ပြောင်းလဲပြီးပါပြီ!", icon="🎉")

else:
    att_tab = tabs[1]
    rep_tab = tabs[2]

# =========================================================
# DAILY ATTENDANCE TAB
# =========================================================
with att_tab:
    st.subheader("📋 နေ့စဉ် ကျောင်းခေါ်ချိန် မှတ်တမ်း")
    st_classes = run_query("SELECT DISTINCT class_type AS \"Class_Type\", class_name AS \"Class_Name\" FROM students ORDER BY class_type, class_name")

    if not st_classes.empty:
        a1, a2, a3 = st.columns(3)
        with a1:
            att_date = st.date_input("ရက်စွဲ ရွေးချယ်ပါ", date.today(), key="att_d_pick").strftime("%Y-%m-%d")
        with a2:
            sel_at_type = st.selectbox("ကျောင်းအမျိုးအစား", sorted(st_classes["Class_Type"].dropna().unique().tolist()), key="at_tp_sel")
        with a3:
            filtered_cn = st_classes[st_classes["Class_Type"] == sel_at_type]["Class_Name"].dropna().unique().tolist()
            sel_at_cls = st.selectbox("တန်းခွဲ", filtered_cn, key="at_cls_sel")

        stu_in_c = run_query(
            "SELECT student_name AS \"Student_Name\", phone AS \"Phone\" FROM students WHERE class_type = %s AND class_name = %s ORDER BY student_name",
            (sel_at_type, sel_at_cls),
        )

        if not stu_in_c.empty:
            existing_att = run_query(
                "SELECT student_name AS \"Student_Name\", status AS \"Status\" FROM attendance WHERE date = %s AND class_type = %s AND class_name = %s",
                (att_date, sel_at_type, sel_at_cls),
            )
            status_map = dict(zip(existing_att["Student_Name"], existing_att["Status"])) if not existing_att.empty else {}

            st.write(f"**{sel_at_type} - {sel_at_cls}** ({att_date} ရက်စွဲ)")
            with st.form("daily_att_form"):
                saved_att = []
                for _, srow in stu_in_c.iterrows():
                    sname = srow["Student_Name"]
                    sphone = str(srow["Phone"]) if pd.notna(srow["Phone"]) else "-"
                    curr_st = status_map.get(sname, "တက်ရောက်")
                    statuses = ["တက်ရောက်", "ပျက်ကွက်", "ခွင့်"]
                    idx = statuses.index(curr_st) if curr_st in statuses else 0

                    col_info, col_radio = st.columns([3, 2])
                    with col_info:
                        st.markdown(f"**{sname}** | 📞 `{sphone}`")
                    with col_radio:
                        st_choice = st.radio(f"status_{sname}", statuses, index=idx, horizontal=True, label_visibility="collapsed")
                    saved_att.append((att_date, sel_at_type, sel_at_cls, sname, sphone, st_choice))

                if st.form_submit_button("💾 ကျောင်းခေါ်ချိန် သိမ်းဆည်းမည်", type="primary"):
                    conn = get_conn()
                    try:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM attendance WHERE date = %s AND class_type = %s AND class_name = %s", (att_date, sel_at_type, sel_at_cls))
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
# ATTENDANCE & STRENGTH REPORT TAB
# =========================================================
with rep_tab:
    st.subheader("📊 ကျောင်းသားအင်အားနှင့် တက်/ပျက် စာရင်းချုပ်")
    rep_date = st.date_input("စစ်ဆေးလိုသည့် ရက်စွဲ", date.today(), key="sum_d_pick").strftime("%Y-%m-%d")
    summary_q = """
        SELECT
            s.class_type AS "ကျောင်းအမျိုးအစား",
            s.class_name AS "တန်းခွဲ",
            COUNT(s.student_name) AS "ကျောင်းသားအင်အား",
            SUM(CASE WHEN a.status = 'တက်ရောက်' THEN 1 ELSE 0 END) AS "တက်ရောက်",
            SUM(CASE WHEN a.status = 'ပျက်ကွက်' THEN 1 ELSE 0 END) AS "ပျက်ကွက်",
            SUM(CASE WHEN a.status = 'ခွင့်' THEN 1 ELSE 0 END) AS "ခွင့်",
            SUM(CASE WHEN a.status IS NULL THEN 1 ELSE 0 END) AS "စာရင်းမသွင်းရသေး"
        FROM students s
        LEFT JOIN attendance a
            ON s.student_name = a.student_name
            AND s.class_type = a.class_type
            AND s.class_name = a.class_name
            AND a.date = %s
        GROUP BY s.class_type, s.class_name
        ORDER BY s.class_type, s.class_name
    """
    rep_df = run_query(summary_q, (rep_date,))
    if not rep_df.empty:
        st.dataframe(rep_df, use_container_width=True, hide_index=True)
    else:
        st.info("အချက်အလက်များ မရှိသေးပါ။")
