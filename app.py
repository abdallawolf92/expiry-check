import pandas as pd
import streamlit as st
import os

st.set_page_config(page_title="📊 البحث عن المواد في الاكسل", layout="wide")
st.title("📊 برنامج البحث عن المواد")

file_path = "المواد.xlsx"
PASSWORD = "2025"

# استخدام session_state لحفظ حالة تسجيل الدخول
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password_input = st.text_input("🔑 الرجاء إدخال كلمة المرور:", type="password")
    if st.button("دخول"):
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ تم تسجيل الدخول بنجاح.")
        else:
            st.error("❌ كلمة المرور غير صحيحة.")
else:
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {e}")
            st.stop()

        if not {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية"}.issubset(df.columns):
            st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة: اسم المادة، رقم الدفعة، تاريخ الصلاحية.")
            st.stop()

        search_query = st.text_input("🔎 ابحث باسم المادة")

        if search_query:
            filtered_df = df[df['اسم المادة'].astype(str).str.contains(search_query, case=False, na=False)].copy()

            st.write("🟩 النتائج بعد البحث:")
            st.dataframe(filtered_df, use_container_width=True)

    else:
        st.warning("⚠️ لم يتم العثور على الملف داخل المستودع.")
