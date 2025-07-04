import pandas as pd import streamlit as st import sqlite3 from datetime import datetime, timedelta, timezone from PIL import Image import hashlib import socket import os import time

st.set_page_config(page_title="Expiry Checker", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

📌 Splash Screen محاكاة

if 'splash_shown' not in st.session_state: st.image("logo.png", width=250) st.markdown('<h2 style="text-align:center;">🧪 Expiry Checker - Unimedica</h2>', unsafe_allow_html=True) st.markdown('<p style="text-align:center;">...جارٍ التحميل...</p>', unsafe_allow_html=True) time.sleep(1.5) st.session_state['splash_shown'] = True st.rerun()

إعدادات الاتصال بقاعدة البيانات

conn = sqlite3.connect('users.db', check_same_thread=False) c = conn.cursor() c.execute('''CREATE TABLE IF NOT EXISTS users ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, last_login TEXT, is_logged_in INTEGER DEFAULT 0, ip_address TEXT )''') conn.commit()

إنشاء حساب admin تلقائي إذا لم يوجد

c.execute("SELECT COUNT(*) FROM users") if c.fetchone()[0] == 0: c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashlib.sha256("2025".encode()).hexdigest())) conn.commit() st.success("✅ تم إنشاء حساب Admin تلقائي (admin/2025) عند أول تشغيل.")

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

إعداد توقيت بغداد

baghdad_tz = timezone(timedelta(hours=3))

الخروج التلقائي بعد 30 ثانية

c.execute("SELECT id, last_login, is_logged_in FROM users WHERE is_logged_in = 1") for user_id, last_login, is_logged_in in c.fetchall(): if last_login: last_login_time = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S") if datetime.now(baghdad_tz) - last_login_time.replace(tzinfo=baghdad_tz) > timedelta(seconds=30): c.execute("UPDATE users SET is_logged_in = 0 WHERE id = ?", (user_id,)) conn.commit()

🩺 واجهة تسجيل الدخول

if os.path.exists("logo.png"): st.image("logo.png", width=120) st.markdown('<p style="font-size:36px; text-align:center; font-weight:bold;">Expiry Checker 🧪</p>', unsafe_allow_html=True)

st.markdown("## تسجيل الدخول") username = st.text_input("👤 اسم المستخدم:") password = st.text_input("🔑 كلمة المرور:", type="password", on_change=lambda: st.session_state.update({'enter_login': True}))

ip_address = socket.gethostbyname(socket.gethostname())

if st.button("تسجيل الدخول") or st.session_state.get('enter_login'): st.session_state.pop('enter_login', None) if username and password: c.execute("SELECT id, password_hash, is_logged_in FROM users WHERE username = ?", (username,)) result = c.fetchone() if result: user_id, stored_hash, is_logged_in = result if hash_password(password) == stored_hash: if is_logged_in: st.error("❌ هذا الحساب مسجل دخول في مكان آخر.") else: current_time = datetime.now(baghdad_tz).strftime("%Y-%m-%d %H:%M:%S") c.execute("UPDATE users SET last_login = ?, is_logged_in = 1, ip_address = ? WHERE id = ?", (current_time, ip_address, user_id)) conn.commit() st.success("✅ تم تسجيل الدخول بنجاح.") st.session_state['logged_in'] = True st.session_state['username'] = username else: st.error("❌ كلمة المرور غير صحيحة.") else: st.error("❌ المستخدم غير موجود.") else: st.warning("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور.")

🚪 تسجيل الخروج

if st.session_state.get('logged_in'): if st.button("🚪 تسجيل الخروج"): c.execute("UPDATE users SET is_logged_in = 0 WHERE username = ?", (st.session_state['username'],)) conn.commit() st.session_state.clear() st.success("✅ تم تسجيل الخروج.") st.stop()

📊 عرض البيانات والبحث باسم المادة أو رقم اللوت

file_path =

