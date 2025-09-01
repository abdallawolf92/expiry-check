# --- Expiry Checker (refactor & fixes) ---
# إضافة ميزة: عمود مخفي لفحص الكمية (لا يظهر للزبائن)
# إذا كانت كمية المادة < 10 → يكتب البرنامج "اتصل للتأكيد" في عمود الخصم.

import os
import socket
import hashlib
from datetime import datetime, timedelta, timezone

import pandas as pd
import sqlite3
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Expiry Checker",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BAGHDAD_TZ = timezone(timedelta(hours=3))
SESSION_TIMEOUT_SEC = 30
FILE_PATH = "المواد.xlsx"
USERS_DB_PATH = "user.db"

@st.cache_resource(show_spinner=False)
def get_conn():
    conn = sqlite3.connect(USERS_DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def now_str_tz(tz=BAGHDAD_TZ) -> str:
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def get_client_ip_fallback() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "unknown"


conn = get_conn()
c = conn.cursor()

c.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        last_login TEXT,
        is_logged_in INTEGER DEFAULT 0,
        ip_address TEXT
    )
    """
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS logins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        login_time TEXT
    )
    """
)
conn.commit()

try:
    admin_password = st.secrets["admin_password"]
    c.execute("SELECT 1 FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", hash_password(admin_password)),
        )
        conn.commit()
        st.success("✅ تم إنشاء حساب Admin تلقائي باستخدام كلمة المرور من secrets.")
except KeyError:
    st.warning("⚠️ لم يتم العثور على admin_password في secrets. يرجى إضافته في إعدادات Streamlit Cloud.")

c.execute("SELECT id, last_login, is_logged_in FROM users WHERE is_logged_in = 1")
for user_id, last_login, is_logged_in in c.fetchall():
    if last_login:
        try:
            last_login_dt = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S").replace(tzinfo=BAGHDAD_TZ)
            if datetime.now(BAGHDAD_TZ) - last_login_dt > timedelta(seconds=SESSION_TIMEOUT_SEC):
                c.execute("UPDATE users SET is_logged_in = 0 WHERE id = ?", (user_id,))
                conn.commit()
        except Exception:
            pass

if st.session_state.get("logged_in") and st.session_state.get("username"):
    c.execute("SELECT is_logged_in FROM users WHERE username = ?", (st.session_state["username"],))
    row = c.fetchone()
    if row and row[0] == 0:
        st.session_state.clear()
        st.info("ℹ️ انتهت الجلسة تلقائيًا. يرجى تسجيل الدخول من جديد.")

if os.path.exists("logo.png"):
    try:
        st.image(Image.open("logo.png"), width=120)
    except Exception:
        pass

st.markdown('<p style="font-size:36px; text-align:center; font-weight:bold;">Expiry Checker 🧪</p>', unsafe_allow_html=True)

st.markdown("## تسجيل الدخول")
username = st.text_input("👤 اسم المستخدم:")
password = st.text_input("🔑 كلمة المرور:", type="password")
client_ip = get_client_ip_fallback()

col_login, col_logout = st.columns([1, 1], gap="small")
with col_login:
    if st.button("تسجيل الدخول"):
        if username and password:
            c.execute("SELECT id, password_hash, is_logged_in FROM users WHERE username = ?", (username,))
            row = c.fetchone()
            if row:
                user_id, stored_hash, is_logged = row
                if hash_password(password) == stored_hash:
                    if is_logged:
                        st.error("❌ هذا الحساب مسجل دخول في مكان آخر.")
                    else:
                        current_time = now_str_tz()
                        c.execute(
                            "UPDATE users SET last_login = ?, is_logged_in = 1, ip_address = ? WHERE id = ?",
                            (current_time, client_ip, user_id),
                        )
                        c.execute(
                            "INSERT INTO logins (username, login_time) VALUES (?, ?)",
                            (username, current_time),
                        )
                        conn.commit()
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.success("✅ تم تسجيل الدخول بنجاح.")
                        st.experimental_rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة.")
            else:
                st.error("❌ المستخدم غير موجود.")
        else:
            st.warning("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور.")

with col_logout:
    if st.session_state.get("logged_in"):
        if st.button("🚪 تسجيل الخروج"):
            c.execute("UPDATE users SET is_logged_in = 0 WHERE username = ?", (st.session_state["username"],))
            conn.commit()
            st.session_state.clear()
            st.success("✅ تم تسجيل الخروج.")
            st.experimental_rerun()

if st.session_state.get("logged_in"):
    if os.path.exists(FILE_PATH):
        @st.cache_data(show_spinner=False)
        def load_excel(path: str) -> pd.DataFrame:
            try:
                df = pd.read_excel(path)
            except Exception as e:
                raise RuntimeError(f"خطأ في قراءة الملف: {e}")
            return df

        try:
            df = load_excel(FILE_PATH)
        except Exception as e:
            st.error(f"❌ {e}")
            st.stop()

        required_cols = {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية", "الكمية"}
        if not required_cols.issubset(df.columns):
            st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة: 'اسم المادة'، 'رقم الدفعة'، 'تاريخ الصلاحية'، 'الكمية'.")
            st.stop()

        search_query = st.text_input("🔎 ابحث باسم المادة هنا 👇", placeholder="اكتب اسم المادة للبحث…")

        if search_query:
            base = df[df["اسم المادة"].astype(str).str.contains(search_query, case=False, na=False)].copy()

            if base.empty:
                st.info("ℹ️ لا توجد نتائج مطابقة.")
            else:
                if base["تاريخ الصلاحية"].dtype == "O":
                    base["تاريخ الصلاحية"] = (
                        base["تاريخ الصلاحية"].astype(str)
                        .str.replace("ص", "AM")
                        .str.replace("م", "PM")
                    )
                base["تاريخ الصلاحية"] = pd.to_datetime(
                    base["تاريخ الصلاحية"], errors="coerce", dayfirst=True
                )
                base = base.dropna(subset=["تاريخ الصلاحية"]).copy()

                if base.empty:
                    st.info("ℹ️ لا توجد تواريخ صالحة بعد التحويل.")
                else:
                    idx = base.groupby("اسم المادة")["تاريخ الصلاحية"].idxmin()
                    filtered_df = base.loc[idx].reset_index(drop=True)

                    today = pd.Timestamp(datetime.now(BAGHDAD_TZ).date())                    discounts = []
                    for _, row in filtered_df.iterrows():
                        exp = row["تاريخ الصلاحية"]
                        qty = row["الكمية"] if not pd.isna(row["الكمية"]) else 0
                        days_left = (exp - today).days

                        # احسب الخصم الأساسي حسب التاريخ
                        if days_left <= 30:
                            base = "خصم 75%"
                        elif days_left <= 60:
                            base = "خصم 50%"
                        elif days_left <= 90:
                            base = "خصم 25%"
                        else:
                            base = "لا يوجد خصم"

                        # أضف "\ كمية قليلة" داخل نفس الخلية إذا الكمية أقل من 10
                        q = pd.to_numeric(qty, errors="coerce")
                        if pd.isna(q):
                            q = 0
                        if q < 10:
                            base = f"{base} \ كمية قليلة"

                        discounts.append(base)

                    filtered_df["الخصم"] = discounts
                    filtered_df = filtered_df.drop(columns=["الكمية"])

                    st.write(f"📦 عدد النتائج: {len(filtered_df)}")
                    st.dataframe(filtered_df, use_container_width=True)
        else:
            st.caption("اكتب جزءًا من اسم المادة لعرض أقرب صلاحية والخصم المقترح.")
    else:
        st.warning("⚠️ لم يتم العثور على ملف المواد داخل المستودع.")

if st.session_state.get("logged_in") and st.session_state.get("username") == "admin":
    st.markdown("## 📊 لوحة التحكم")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        user_stats = pd.read_sql_query(
            "SELECT id, username, last_login, ip_address FROM users ORDER BY id ASC", conn
        )
        st.dataframe(user_stats, use_container_width=True)

    with col_b:
        try:
            with open(USERS_DB_PATH, "rb") as f:
                st.download_button(
                    label="⬇️ تنزيل users.db",
                    data=f,
                    file_name="users.db",
                    mime="application/octet-stream",
                )
        except Exception:
            st.caption("لا يمكن تنزيل قاعدة البيانات الآن.")

    st.markdown("## 🧾 سجلات الدخول لليوم")
    today_str = datetime.now(BAGHDAD_TZ).strftime("%Y-%m-%d")
    login_logs = pd.read_sql_query(
        "SELECT username, login_time FROM logins WHERE DATE(login_time) = ?",
        conn,
        params=(today_str,),
    )
    st.info(f"✅ عدد المستخدمين الذين دخلوا اليوم: {len(login_logs)}")
    st.dataframe(login_logs, use_container_width=True)

    st.markdown("## ➕ إضافة مستخدم جديد")
    new_username = st.text_input("اسم المستخدم الجديد")
    new_password = st.text_input("كلمة مرور المستخدم الجديد", type="password")
    if st.button("إضافة المستخدم"):
        if new_username and new_password:
            try:
                c.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (new_username, hash_password(new_password)),
                )
                conn.commit()
                st.success("✅ تم إضافة المستخدم بنجاح.")
                st.experimental_rerun()
            except sqlite3.IntegrityError:
                st.error("❌ اسم المستخدم موجود مسبقًا.")
        else:
            st.warning("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور.")

    st.markdown("## 🗑️ حذف مستخدم")
    delete_user_id = st.number_input("أدخل رقم ID للمستخدم المراد حذفه:", min_value=1, step=1)
    if st.button("🗑️ حذف المستخدم"):
        try:
            c.execute("DELETE FROM users WHERE id = ? AND username != 'admin'", (delete_user_id,))
            conn.commit()
            st.success("✅ تم حذف المستخدم بنجاح (لا يمكن حذف admin).")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء الحذف: {e}")
