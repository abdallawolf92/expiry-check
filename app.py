import pandas as pd
import streamlit as st
import sqlite3
from datetime import datetime, timedelta, timezone
from PIL import Image
import hashlib
import socket
import os

st.set_page_config(page_title="Expiry Checker 🧪", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    last_login TEXT,
    is_logged_in INTEGER DEFAULT 0,
    ip_address TEXT
)''')
conn.commit()

# إنشاء حساب admin تلقائي باستخدام secret من Streamlit Cloud
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    admin_pass = st.secrets.get("ADMIN_PASSWORD")
    if not admin_pass:
        st.error("❌ لم يتم ضبط كلمة مرور الأدمن داخل secrets على Streamlit Cloud.")
        st.stop()

    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
              ("admin", hashlib.sha256(admin_pass.encode()).hexdigest()))
    conn.commit()
    st.success("✅ تم إنشاء حساب Admin تلقائي.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# توقيت بغداد
baghdad_tz = timezone(timedelta(hours=3))

# الخروج التلقائي بعد 30 ثانية
c.execute("SELECT id, last_login, is_logged_in FROM users WHERE is_logged_in = 1")
for user_id, last_login, is_logged_in in c.fetchall():
    if last_login:
        last_login_time = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
        if datetime.now(baghdad_tz) - last_login_time.replace(tzinfo=baghdad_tz) > timedelta(seconds=30):
            c.execute("UPDATE users SET is_logged_in = 0 WHERE id = ?", (user_id,))
            conn.commit()

# عرض الشعار إذا موجود
if os.path.exists("logo.png"):
    st.image("logo.png", width=120)

st.markdown("<h1 style='text-align: center; color: #0077b6;'>Expiry Checker 🧪</h1>", unsafe_allow_html=True)

# ------------------- تسجيل الدخول -------------------
st.divider()
st.markdown("## 🗝️ تسجيل الدخول", unsafe_allow_html=True)
col1, col2 = st.columns([2, 2])
with col1:
    username = st.text_input("👤 اسم المستخدم:")
with col2:
    password = st.text_input("🔑 كلمة المرور:", type="password")

ip_address = socket.gethostbyname(socket.gethostname())

if st.button("🚪 تسجيل الدخول", type="primary"):
    if username and password:
        c.execute("SELECT id, password_hash, is_logged_in FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        if result:
            user_id, stored_hash, is_logged_in = result
            if hash_password(password) == stored_hash:
                if is_logged_in:
                    st.error("❌ هذا الحساب مسجل دخول في مكان آخر.")
                else:
                    current_time = datetime.now(baghdad_tz).strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("UPDATE users SET last_login = ?, is_logged_in = 1, ip_address = ? WHERE id = ?",
                              (current_time, ip_address, user_id))
                    conn.commit()
                    st.success("✅ تم تسجيل الدخول بنجاح.")
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
            else:
                st.error("❌ كلمة المرور غير صحيحة.")
        else:
            st.error("❌ المستخدم غير موجود.")
    else:
        st.warning("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور.")

# ------------------- تسجيل الخروج -------------------
if st.session_state.get('logged_in'):
    if st.button("🔒 تسجيل الخروج", type="secondary"):
        c.execute("UPDATE users SET is_logged_in = 0 WHERE username = ?", (st.session_state['username'],))
        conn.commit()
        st.session_state.clear()
        st.success("✅ تم تسجيل الخروج.")
        st.stop()

# ------------------- عرض المواد -------------------
st.divider()
file_path = "المواد.xlsx"
if st.session_state.get('logged_in'):
    st.markdown("## 📦 المواد المنتهية والصلاحيات", unsafe_allow_html=True)
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {e}")
            st.stop()

        if not {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية"}.issubset(df.columns):
            st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة.")
            st.stop()

        search_query = st.text_input("🔍 ابحث باسم المادة هنا:", placeholder="أدخل اسم المادة للبحث...")
        if search_query:
            filtered_df = df[df['اسم المادة'].astype(str).str.contains(search_query, case=False, na=False)].copy()
            filtered_df['تاريخ الصلاحية'] = filtered_df['تاريخ الصلاحية'].astype(str).str.replace('ص', 'AM').str.replace('م', 'PM')
            filtered_df['تاريخ الصلاحية'] = pd.to_datetime(filtered_df['تاريخ الصلاحية'], format='%d/%m/%Y %I:%M:%S %p', errors='coerce', dayfirst=True)
            filtered_df.dropna(subset=['تاريخ الصلاحية'], inplace=True)

            idx = filtered_df.groupby('اسم المادة')['تاريخ الصلاحية'].idxmin()
            filtered_df = filtered_df.loc[idx].reset_index(drop=True)

            today = pd.Timestamp(datetime.today().date())
            filtered_df['الخصم'] = ""

            for i, row in filtered_df.iterrows():
                days_left = (row['تاريخ الصلاحية'] - today).days
                if days_left <= 30:
                    filtered_df.at[i, 'الخصم'] = "خصم 75%"
                elif days_left <= 60:
                    filtered_df.at[i, 'الخصم'] = "خصم 50%"
                elif days_left <= 90:
                    filtered_df.at[i, 'الخصم'] = "خصم 25%"
                else:
                    filtered_df.at[i, 'الخصم'] = "لا يوجد خصم"

            st.success(f"✅ عدد النتائج: {len(filtered_df)}")
            st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("⚠️ لم يتم العثور على ملف المواد داخل المستودع.")

# ------------------- لوحة تحكم المسؤول -------------------
if st.session_state.get('username') == 'admin':
    st.divider()
    st.markdown("## ⚙️ لوحة تحكم المسؤول", unsafe_allow_html=True)

    user_stats = pd.read_sql_query("SELECT id, username, last_login, ip_address FROM users ORDER BY id ASC", conn)
    st.dataframe(user_stats, use_container_width=True)

    count_today = pd.read_sql_query("SELECT COUNT(*) as count FROM users WHERE DATE(last_login) = DATE('now', 'localtime')", conn)['count'][0]
    st.info(f"✅ عدد المستخدمين الذين دخلوا اليوم: {count_today}")

    st.divider()
    st.markdown("### ➕ إضافة مستخدم جديد", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 2])
    with col1:
        new_username = st.text_input("👤 اسم المستخدم الجديد:")
    with col2:
        new_password = st.text_input("🔑 كلمة مرور المستخدم الجديد:", type="password")
    if st.button("➕ إضافة المستخدم", type="primary"):
        if new_username and new_password:
            try:
                c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                          (new_username, hash_password(new_password)))
                conn.commit()
                st.success("✅ تم إضافة المستخدم بنجاح.")
            except sqlite3.IntegrityError:
                st.error("❌ اسم المستخدم موجود مسبقًا.")
        else:
            st.warning("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور.")

    st.divider()
    st.markdown("### 🗑️ حذف مستخدم", unsafe_allow_html=True)
    delete_user_id = st.number_input("أدخل رقم ID للمستخدم المراد حذفه:", min_value=1, step=1)
    if st.button("🗑️ حذف المستخدم", type="secondary"):
        try:
            c.execute("DELETE FROM users WHERE id = ? AND username != 'admin'", (delete_user_id,))
            conn.commit()
            st.success("✅ تم حذف المستخدم بنجاح (لا يمكن حذف admin).")
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء الحذف: {e}")

    st.divider()
    st.markdown("### 📤 رفع ملف مواد جديد", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("📁 اختر ملف Excel جديد (يجب أن يحتوي على الأعمدة: اسم المادة، رقم الدفعة، تاريخ الصلاحية)", type=["xlsx"])

    if uploaded_file is not None:
        try:
            df_new = pd.read_excel(uploaded_file)
            required_columns = {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية"}
            if required_columns.issubset(df_new.columns):
                if os.path.exists(file_path):
                    os.remove(file_path)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("✅ تم رفع الملف وتحديث المواد بنجاح.")
                st.rerun()
            else:
                st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة.")
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")

# إغلاق الاتصال بقاعدة البيانات
conn.close()
