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

# إنشاء حساب admin تلقائي بكلمة مرور من ملف خارجي آمن
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    if os.path.exists("admin_config.txt"):
        with open("admin_config.txt", "r") as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith("admin_password="):
                admin_pass = line.strip().split("=")[1]
                break
        else:
            st.error("❌ لم يتم العثور على admin_password في ملف config.")
            st.stop()
    else:
        st.error("❌ لم يتم العثور على ملف admin_config.txt.")
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
col1, col2 = st.columns([2,2])
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

# ------------------- زر تسجيل الخروج -------------------
if st.session_state.get('logged_in'):
    if st.button("🔒 تسجيل الخروج", type="secondary"):
        c.execute("UPDATE users SET is_logged_in = 0 WHERE username = ?", (st.session_state['username'],))
        conn.commit()
        st.session_state.clear()
        st.success("✅ تم تسجيل الخروج.")
        st.stop()

# ------------------- عرض ملف المواد -------------------
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
