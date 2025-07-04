import pandas as pd import streamlit as st import sqlite3 from datetime import datetime, timedelta, timezone from PIL import Image import hashlib import socket import os import time

st.set_page_config(page_title="Expiry Checker", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

Splash Screen Simulation

if 'splash_shown' not in st.session_state: st.image("logo.png", width=250) st.write("Expiry Checker - Unimedica") time.sleep(1.5) st.session_state['splash_shown'] = True st.rerun()

conn = sqlite3.connect('users.db', check_same_thread=False) c = conn.cursor() c.execute('''CREATE TABLE IF NOT EXISTS users ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, last_login TEXT, is_logged_in INTEGER DEFAULT 0, ip_address TEXT )''') conn.commit()

c.execute("SELECT COUNT(*) FROM users") if c.fetchone()[0] == 0: c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashlib.sha256("2025".encode()).hexdigest())) conn.commit() st.success("Admin account created: admin/2025")

def hash_password(password): return hashlib.sha256(password.encode()).hexdigest()

baghdad_tz = timezone(timedelta(hours=3))

c.execute("SELECT id, last_login, is_logged_in FROM users WHERE is_logged_in = 1") for user_id, last_login, is_logged_in in c.fetchall(): if last_login: last_login_time = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S") if datetime.now(baghdad_tz) - last_login_time.replace(tzinfo=baghdad_tz) > timedelta(seconds=30): c.execute("UPDATE users SET is_logged_in = 0 WHERE id = ?", (user_id,)) conn.commit()

if os.path.exists("logo.png"): st.image("logo.png", width=120) st.title("Expiry Checker")

username = st.text_input("Username") password = st.text_input("Password", type="password", on_change=lambda: st.session_state.update({'enter_login': True})) ip_address = socket.gethostbyname(socket.gethostname())

if st.button("Login") or st.session_state.get('enter_login'): st.session_state.pop('enter_login', None) if username and password: c.execute("SELECT id, password_hash, is_logged_in FROM users WHERE username = ?", (username,)) result = c.fetchone() if result: user_id, stored_hash, is_logged_in = result if hash_password(password) == stored_hash: if is_logged_in: st.error("This account is already logged in elsewhere.") else: current_time = datetime.now(baghdad_tz).strftime("%Y-%m-%d %H:%M:%S") c.execute("UPDATE users SET last_login = ?, is_logged_in = 1, ip_address = ? WHERE id = ?", (current_time, ip_address, user_id)) conn.commit() st.success("Logged in successfully.") st.session_state['logged_in'] = True st.session_state['username'] = username else: st.error("Incorrect password.") else: st.error("User does not exist.") else: st.warning("Please enter both username and password.")

if st.session_state.get('logged_in'): if st.button("Logout"): c.execute("UPDATE users SET is_logged_in = 0 WHERE username = ?", (st.session_state['username'],)) conn.commit() st.session_state.clear() st.success("Logged out successfully.") st.stop()

file_path = "المواد.xlsx" if st.session_state.get('logged_in'): if os.path.exists(file_path): df = pd.read_excel(file_path) if not {'اسم المادة', 'رقم الدفعة', 'تاريخ الصلاحية'}.issubset(df.columns): st.error("The file does not contain the required columns.") st.stop()

search_query = st.text_input("Search by Material Name or Lot Number", placeholder="Type here to search...")
    if search_query:
        filtered_df = df[df['اسم المادة'].astype(str).str.contains(search_query, case=False, na=False) |
                         df['رقم الدفعة'].astype(str).str.contains(search_query, case=False, na=False)].copy()
    else:
        filtered_df = df.copy()

    filtered_df['تاريخ الصلاحية'] = pd.to_datetime(filtered_df['تاريخ الصلاحية'], errors='coerce', dayfirst=True)
    filtered_df = filtered_df.dropna(subset=['تاريخ الصلاحية'])

    today = pd.Timestamp(datetime.today().date())
    def discount_label(exp_date):
        days_left = (exp_date - today).days
        if days_left <= 30:
            return "75% Discount"
        elif days_left <= 60:
            return "50% Discount"
        elif days_left <= 90:
            return "25% Discount"
        else:
            return "No Discount"
    
    filtered_df['Discount'] = filtered_df['تاريخ الصلاحية'].apply(discount_label)

    st.write(f"Results found: {len(filtered_df)}")
    st.dataframe(filtered_df)
else:
    st.warning("Materials file not found in the repository.")

if st.session_state.get('username') == 'admin': st.subheader("Admin Dashboard") user_stats = pd.read_sql_query("SELECT id, username, last_login, ip_address FROM users ORDER BY id ASC", conn) st.dataframe(user_stats)

count_today = pd.read_sql_query("SELECT COUNT(*) as count FROM users WHERE DATE(last_login) = DATE('now', 'localtime')", conn)['count'][0]
st.info(f"Users logged in today: {count_today}")

st.subheader("Add New User")
new_username = st.text_input("New Username")
new_password = st.text_input("New User Password", type="password")
if st.button("Add User"):
    if new_username and new_password:
        try:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (new_username, hash_password(new_password)))
            conn.commit()
            st.success("User added successfully.")
        except sqlite3.IntegrityError:
            st.error("Username already exists.")
    else:
        st.warning("Please enter username and password.")

st.subheader("Delete User")
delete_user_id = st.number_input("Enter User ID to Delete", min_value=1, step=1)
if st.button("Delete User"):
    try:
        c.execute("DELETE FROM users WHERE id = ? AND username != 'admin'", (delete_user_id,))
        conn.commit()
        st.success("User deleted successfully (admin cannot be deleted).")
    except Exception as e:
        st.error(f"Error during deletion: {e}")

conn.close()

