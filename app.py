import pandas as pd
import streamlit as st
import os
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="📊 برنامج البحث عن المواد", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# تخصيص CSS لتحسين الشكل
st.markdown("""
    <style>
    .big-font {font-size:30px !important; text-align: center;}
    .stTextInput input {font-size: 18px; padding: 10px;}
    .stButton>button {font-size:18px; padding: 0.5em 2em;}
    .css-1l269bu {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# عنوان البرنامج
st.markdown('<p class="big-font">📊 برنامج البحث عن المواد في المخزن</p>', unsafe_allow_html=True)

file_path = "المواد.xlsx"
PASSWORD = "2025"

# تحسين شكل إدخال كلمة المرور
password_input = st.text_input("🔑 الرجاء إدخال كلمة المرور للدخول:", type="password", help="أدخل كلمة السر ثم اضغط Enter")

if password_input == PASSWORD:
    st.success("✅ تم تسجيل الدخول بنجاح. يمكنك الآن البحث عن المواد.")

    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            st.error(f"❌ خطأ في قراءة الملف: {e}")
            st.stop()

        if not {"اسم المادة", "رقم الدفعة", "تاريخ الصلاحية"}.issubset(df.columns):
            st.error("❌ الملف لا يحتوي على الأعمدة المطلوبة: اسم المادة، رقم الدفعة، تاريخ الصلاحية.")
            st.stop()

        # مربع البحث
        search_query = st.text_input("🔎 ابحث باسم المادة هنا 👇", placeholder="اكتب اسم المادة للبحث...")

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

            # إضافة عمود الخصم
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

            st.success(f"✅ تم العثور على {len(filtered_df)} نتيجة.")

            # عرض النتائج بجدول جميل
            st.dataframe(
                filtered_df.style.set_properties(**{
                    'background-color': '#f9f9f9',
                    'color': '#000',
                    'border-color': 'white',
                    'text-align': 'center'
                }),
                use_container_width=True
            )

    else:
        st.warning("⚠️ لم يتم العثور على ملف المواد داخل المستودع.")
else:
    if password_input != "":
        st.error("❌ كلمة المرور غير صحيحة. حاول مرة أخرى.")
