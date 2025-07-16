import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import hashlib
import os

st.set_page_config(page_title="Expiry Checker 🧪", page_icon="🧪", layout="wide")

# ---------- إعدادات ----------
USER_DB = "user.db"
EXCEL_FILE = "المواد.xlsx"

# ---------- دوال ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    if username == "admin":
        admin_secret = st.secrets.get("admin", {}).get("password", None)
        if admin_secret and password == admin_secret:
            return True, ""
        else:
            return False, "كلمة مرور الأدمن غير صحيحة"
    else:
        if not os.path.exists(USER_DB):
            return False, "قاعدة بيانات المستخدمين غير موجودة"
        conn = sqlite3.connect(USER_DB)
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        if result and hash_password(password) == result[0]:
            return True, ""
        return False, "اسم المستخدم أو كلمة المرور غير صحيحة"

def load_excel():
    if not os.path.exists(EXCEL_FILE):
        st.error("❌ ملف المواد غير موجود")
        st.stop()
    try:
        df = pd.read_excel(EXCEL_FILE)
        return df
    except Exception as e:
        st.error(f"❌ خطأ في قراءة ملف المواد: {e}")
        st.stop()

def calculate_discount(expiry_date):
    today = pd.Timestamp(datetime.today().date())
    days_left = (expiry_date - today).days
    if days_left <= 30:
        return "خصم 75%"
    elif days_left <= 60:
        return "خصم 50%"
    elif days_left <= 90:
        return "خصم 25%"
    else:
        return "لا يوجد خصم"

# ---------- تسجيل الدخول ----------
st.title("🧪 برنامج فحص المواد المنتهية")
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.subheader("🔐 تسجيل الدخول")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("👤 اسم المستخدم")
    with col2:
        password = st.text_input("🔒 كلمة المرور", type="password")

    if st.button("🚪 دخول"):
        valid, msg = check_login(username, password)
        if valid:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("✅ تم تسجيل الدخول بنجاح")
            st.experimental_rerun()
        else:
            st.error(f"❌ {msg}")
    st.stop()

# ---------- بعد تسجيل الدخول ----------
st.markdown(f"### 👋 أهلا وسهلا، `{st.session_state.username}`")

st.divider()
df = load_excel()

if not {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية"}.issubset(df.columns):
    st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة")
    st.stop()

try:
    df['تاريخ الصلاحية'] = pd.to_datetime(df['تاريخ الصلاحية'], errors='coerce', dayfirst=True)
except:
    st.error("❌ خطأ في تحويل التاريخ")
    st.stop()

search_query = st.text_input("🔍 ابحث عن اسم مادة أو رقم دفعة")
if search_query:
    df = df[df['اسم المادة'].astype(str).str.contains(search_query, case=False, na=False) |
            df['رقم الدفعة'].astype(str).str.contains(search_query, case=False, na=False)]

df['الخصم'] = df['تاريخ الصلاحية'].apply(lambda x: calculate_discount(x) if pd.notnull(x) else "-")

st.subheader("📋 النتائج:")
st.success(f"✅ عدد النتائج: {len(df)}")
st.dataframe(df[["اسم المادة", "رقم الدفعة", "تاريخ الصلاحية", "الخصم"]], use_container_width=True)

if st.button("🔒 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.experimental_rerun()
