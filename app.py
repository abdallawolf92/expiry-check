import pandas as pd
import streamlit as st

st.set_page_config(page_title="Expiry Checker", page_icon="🧪", layout="wide")

st.title("🔎 Expiry Checker - Search Materials")

# تحميل الملف
file_path = "المواد.xlsx"

def normalize_text(text):
    text = str(text)
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي')
    text = text.replace('ؤ','و').replace('ئ','ي')
    text = text.replace(' ','').lower()
    return text

if st.file_uploader("Upload المواد.xlsx if needed", type=["xlsx"], key="uploader") is not None:
    file_path = st.session_state.uploader.name

if st.button("📂 Load Data"):
    if not os.path.exists(file_path):
        st.error("⚠️ File المواد.xlsx not found in directory.")
    else:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        
        if 'اسم المادة' not in df.columns:
            st.error("⚠️ Column 'اسم المادة' not found in the file.")
        else:
            st.session_state.df_loaded = True
            df['normalized_name'] = df['اسم المادة'].apply(normalize_text)
            st.session_state.df = df
            st.success("✅ Data loaded successfully, ready for search.")

if 'df_loaded' in st.session_state and st.session_state.df_loaded:
    search_query = st.text_input("🔍 Enter part of the material name to search (Arabic/English):").strip()
    
    if search_query != "":
        normalized_query = normalize_text(search_query)
        df = st.session_state.df
        filtered_df = df[df['normalized_name'].str.contains(normalized_query, na=False)]
        
        if not filtered_df.empty:
            st.success(f"✅ Found {len(filtered_df)} matching results:")
            st.dataframe(filtered_df[['اسم المادة', 'رقم الدفعة', 'تاريخ الصلاحية']])
        else:
            st.warning("⚠️ No results found for your search.")
    else:
        st.info("⌨️ Please enter a search term to display results.")

else:
    st.info("📌 Click 'Load Data' to prepare the file for searching.")
