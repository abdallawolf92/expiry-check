import pandas as pd
import streamlit as st
import os

st.set_page_config(page_title="📊 البحث عن المواد في الاكسل", layout="wide")
st.title("📊 برنامج البحث عن المواد")

file_path = "المواد.xlsx"
PASSWORD = "2025"

# إدخال كلمة المرور فقط بدون جلسة معقدة
password_input = st.text_input("🔑 الرجاء إدخال كلمة المرور:", type="password")
if password_input == PASSWORD:
    st.success("✅ تم تسجيل الدخول بنجاح.")

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

    # تنظيف وتحويل التاريخ
    filtered_df['تاريخ الصلاحية'] = filtered_df['تاريخ الصلاحية'].astype(str).str.replace('ص', 'AM').str.replace('م', 'PM')
    filtered_df['تاريخ الصلاحية'] = pd.to_datetime(filtered_df['تاريخ الصلاحية'], format='%d/%m/%Y %I:%M:%S %p', errors='coerce', dayfirst=True)

    # إزالة الصفوف التي لا تحتوي تاريخ صالح
    filtered_df = filtered_df.dropna(subset=['تاريخ الصلاحية'])

    # فلترة أقرب تاريخ صلاحية لكل مادة
    idx = filtered_df.groupby('اسم المادة')['تاريخ الصلاحية'].idxmin()
    filtered_df = filtered_df.loc[idx].reset_index(drop=True)

    st.write("🟩 أقرب تاريخ صلاحية لكل مادة:")
    st.dataframe(filtered_df, use_container_width=True)


    else:
        st.warning("⚠️ لم يتم العثور على الملف داخل المستودع.")
else:
    if password_input != "":
        st.error("❌ كلمة المرور غير صحيحة.")
