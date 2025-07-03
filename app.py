import pandas as pd
import streamlit as st
import os
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Expiry Checker", page_icon="🧪", layout="wide", initial_sidebar_state="collapsed")

# تخصيص CSS احترافي
st.markdown("""
    <style>
    .big-font {font-size:36px !important; text-align: center; font-weight: bold;}
    .center {text-align: center;}
    .stTextInput input {font-size: 18px; padding: 10px;}
    .stButton>button {font-size:18px; padding: 0.5em 2em;}
    .css-1l269bu {padding-top: 2rem;}
    .small-font {font-size:18px !important;}
    </style>
""", unsafe_allow_html=True)

# اللوگو والاسم
if os.path.exists("logo.png"):
    logo = Image.open("logo.png")
    st.image(logo, width=120)
st.markdown('<p class="big-font">Expiry Checker 🧪</p>', unsafe_allow_html=True)

file_path = "المواد.xlsx"
PASSWORD = "2025"

password_input = st.text_input("🔑 الرجاء إدخال كلمة المرور:", type="password", help="اكتب كلمة المرور ثم اضغط Enter")

if password_input == PASSWORD:
    st.success("✅ تم تسجيل الدخول بنجاح، يمكنك الآن البحث عن المواد.")

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

            # تحويل التاريخ
            filtered_df['تاريخ الصلاحية'] = filtered_df['تاريخ الصلاحية'].astype(str).str.replace('ص', 'AM').str.replace('م', 'PM')
            filtered_df['تاريخ الصلاحية'] = pd.to_datetime(
                filtered_df['تاريخ الصلاحية'],
                format='%d/%m/%Y %I:%M:%S %p',
                errors='coerce',
                dayfirst=True
            )
            filtered_df = filtered_df.dropna(subset=['تاريخ الصلاحية'])

            # أقرب تاريخ صلاحية
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

            # عداد النتائج
            st.markdown(f"<p class='center small-font'>📦 عدد النتائج: <b>{len(filtered_df)}</b></p>", unsafe_allow_html=True)

            # تلوين الخصم
            def color_discount(val):
                color = ""
                if val == "خصم 75%":
                    color = 'background-color: #ff9999; color: black;'
                elif val == "خصم 50%":
                    color = 'background-color: #ffcc99; color: black;'
                elif val == "خصم 25%":
                    color = 'background-color: #ffff99; color: black;'
                elif val == "لا يوجد خصم":
                    color = 'background-color: #ccffcc; color: black;'
                return color

            styled_df = filtered_df.style.applymap(color_discount, subset=['الخصم'])

            st.dataframe(styled_df, use_container_width=True)

    else:
        st.warning("⚠️ لم يتم العثور على ملف المواد داخل المستودع.")
else:
    if password_input != "":
        st.error("❌ كلمة المرور غير صحيحة.")
