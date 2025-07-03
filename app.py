import pandas as pd
import streamlit as st
import sqlite3
from datetime import datetime
from PIL import Image
import hashlib
import socket
import os

st.set_page_config(page_title="Expiry Checker", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

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

# إنشاء حساب admin تلقائي إذا لم يكن هناك مستخدمون
c.execute("SELECT COUNT(*) FROM users")
user_count = c.fetchone()[0]
if user_count == 0:
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
              ("admin", hashlib.sha256("2025".encode()).hexdigest()))
    conn.commit()
    st.success("✅ تم إنشاء حساب Admin تلقائي (admin/2025) عند أول تشغيل.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if os.path.exists("logo.png"):
    logo = Image.open("logo.png")
    st.image(logo, width=120)
st.markdown('<p style="font-size:36px; text-align:center; font-weight:bold;">Expiry Checker 🧪</p>', unsafe_allow_html=True)

st.markdown("## تسجيل الدخول")
username = st.text_input("👤 اسم المستخدم:")
password = st.text_input("🔑 كلمة المرور:", type="password")

ip_address = socket.gethostbyname(socket.gethostname())

if st.button("تسجيل الدخول"):
    if username and password:
        c.execute("SELECT id, password_hash, is_logged_in FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        if result:
            user_id, stored_hash, is_logged_in = result
            if hash_password(password) == stored_hash:
                if is_logged_in:
                    st.error("❌ هذا الحساب مسجل دخول في مكان آخر.")
                else:
                    c.execute("UPDATE users SET last_login = ?, is_logged_in = 1, ip_address = ? WHERE id = ?",
                              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ip_address, user_id))
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

if st.session_state.get('logged_in'):
    if st.button("🚪 تسجيل الخروج"):
        c.execute("UPDATE users SET is_logged_in = 0 WHERE username = ?", (st.session_state['username'],))
        conn.commit()
        st.session_state.clear()
        st.success("✅ تم تسجيل الخروج.")
        st.stop()

file_path = "المواد.xlsx"

if st.session_state.get('logged_in'):
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {e}")
            st.stop()

        if not {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية"}.issubset(df.columns):
            st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة.")
            st.stop()

        search_query = st.text_input("🔎 ابحث باسم المادة هنا 👇", placeholder="اكتب اسم المادة للبحث...")

        if search_query:
            filtered_df = df[df['اسم المادة'].astype(str).str.contains(search_query, case=False, na=False)].copy()

            filtered_df['تاريخ الصلاحية'] = filtered_df['تاريخ الصلاحية'].astype(str).str.replace('ص', 'AM').str.replace('م', 'PM')
            filtered_df['تاريخ الصلاحية'] = pd.to_datetime(
                filtered_df['تاريخ الصلاحية'],
                format='%d/%m/%Y %I:%M:%S %p',
                errors='coerce',
                dayfirst=True
            )
            filtered_df = filtered_df.dropna(subset=['تاريخ الصلاحية'])

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

            st.write(f"📦 عدد النتائج: {len(filtered_df)}")
            st.dataframe(filtered_df)
    else:
        st.warning("⚠️ لم يتم العثور على ملف المواد داخل المستودع.")

if st.session_state.get('username') == 'admin':
    st.markdown("## 📊 لوحة التحكم")
    user_stats = pd.read_sql_query("SELECT username, last_login, ip_address FROM users WHERE last_login IS NOT NULL ORDER BY last_login DESC", conn)
    st.dataframe(user_stats)
    count_today = pd.read_sql_query("SELECT COUNT(*) as count FROM users WHERE DATE(last_login) = DATE('now', 'localtime')", conn)['count'][0]
    st.info(f"✅ عدد المستخدمين الذين دخلوا اليوم: {count_today}")

    st.markdown("## ➕ إضافة مستخدم جديد")
    new_username = st.text_input("اسم المستخدم الجديد")
    new_password = st.text_input("كلمة مرور المستخدم الجديد", type="password")
    if st.button("إضافة المستخدم"):
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

conn.close()
