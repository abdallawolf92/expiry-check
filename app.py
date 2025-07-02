import pandas as pd
import streamlit as st
import os
from datetime import datetime

# حماية بكلمة مرور
password = st.text_input("🔒 أدخل كلمة المرور", type="password")
if password != "12345":  # يمكنك تغيير كلمة المرور هنا
    st.warning("🚫 كلمة المرور غير صحيحة.")
    st.stop()

st.set_page_config(page_title="🩺 Expiry Tracker", layout="wide")
st.title("🩺 Expiry Tracker")

# تحسين عرض الجدول على الموبايل
st.markdown(
    """
    <style>
    .stDataFrame div[data-testid="stVerticalBlock"] {overflow-x: auto;}
    .stDataFrame table {font-size: 18px;}
    </style>
    """,
    unsafe_allow_html=True
)

file_path = "المواد.xlsx"

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

        # استبدال ص و م بالانكليزية
        filtered_df['تاريخ الصلاحية'] = filtered_df['تاريخ الصلاحية'].astype(str).str.replace('ص', 'AM').str.replace('م', 'PM')

        # تحويل إلى datetime
        filtered_df['تاريخ الصلاحية'] = pd.to_datetime(filtered_df['تاريخ الصلاحية'], format='%d/%m/%Y %I:%M:%S %p', errors='coerce', dayfirst=True)

        # إزالة القيم الفارغة
        filtered_df = filtered_df.dropna(subset=['تاريخ الصلاحية'])

        # حساب الأيام المتبقية
        filtered_df['الأيام المتبقية'] = (filtered_df['تاريخ الصلاحية'] - pd.Timestamp(datetime.now())).dt.days

        # إضافة عمود الخصم حسب الأيام المتبقية
        def calculate_discount(days_left):
            if days_left <= 30:
                return "خصم 75%"
            elif days_left <= 60:
                return "خصم 50%"
            elif days_left <= 90:
                return "خصم 25%"
            else:
                return ""
        filtered_df['الخصم'] = filtered_df['الأيام المتبقية'].apply(calculate_discount)

        # اختيار أقرب تاريخ صلاحية فقط لكل اسم مادة
        idx = filtered_df.groupby('اسم المادة')['تاريخ الصلاحية'].idxmin()
        filtered_df = filtered_df.loc[idx].reset_index(drop=True)

        st.dataframe(filtered_df, use_container_width=True)
else:
    st.warning("⚠️ لم يتم العثور على الملف داخل مجلد المشروع. يرجى رفع ملف المواد بالاسم المناسب.")
