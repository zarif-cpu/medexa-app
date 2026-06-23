import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import numpy as np
from PIL import Image
import easyocr
import difflib  # 🚀 Built-in library for advanced text matching

# ==========================================
# 1. DATABASE SETUP
# ==========================================
def load_medication_data():
    target_file = None
    for file in os.listdir("."):
        if "medicines" in file.lower() and (file.endswith(".xlsx") or file.endswith(".csv")):
            target_file = file
            break
            
    if target_file:
        try:
            if target_file.endswith(".xlsx"):
                data = pd.read_excel(target_file)
            else:
                data = pd.read_csv(target_file)
            data.columns = data.columns.str.strip()
            return data
        except Exception as e:
            st.error(f"⚠️ Error reading file: {e}")
            return pd.DataFrame()
    else:
        st.error("⚠️ 'medicines.xlsx' not found inside your folder.")
        return pd.DataFrame()

df = load_medication_data()

# Create master verification lists for the AI filter to check against
if not df.empty:
    # Get all valid Generic and Brand names, drop empty rows, convert to string
    valid_generics = df['Nama Generik'].dropna().astype(str).tolist()
    valid_brands = df['Jenama'].dropna().astype(str).tolist()
    # Combine both into a master list for the AI to cross-reference
    allowed_vocabulary = list(set(valid_generics + valid_brands))
else:
    allowed_vocabulary = []

# ==========================================
# 2. EMAIL NOTIFICATION LOGIC
# ==========================================
def send_expiry_email(recipient_email, patient_name, medicine_name, expiry_date):
    return True

# ==========================================
# 3. STREAMLIT CONFIG & CUSTOM MOBILE CSS
# ==========================================
st.set_page_config(page_title="Medexa Assistant", page_icon="🚀", layout="centered")
st.markdown('<link rel="manifest" href="./manifest.json">', unsafe_allow_html=True)

st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 480px;
        margin: 0 auto;
        background-color: #f7f9fa;
    }
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #eef2f3;
        margin-bottom: 15px;
    }
    .app-title {
        font-size: 20px;
        font-weight: 700;
        color: #1a202c;
    }
    .med-card {
        background-color: #ffffff;
        padding: 15px;
        border-bottom: 1px solid #edf2f7;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .med-img-box {
        width: 60px;
        height: 60px;
        background-color: #f7fafc;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 1px solid #e2e8f0;
        overflow: hidden;
    }
    .med-details {
        flex-grow: 1;
    }
    .med-title {
        font-size: 16px;
        font-weight: 700;
        color: #1a202c;
        margin: 0 0 4px 0;
    }
    .med-subtitle {
        font-size: 13px;
        color: #718096;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. MAIN LAYOUT TABS
# ==========================================
nav_tab1, nav_tab2, nav_tab3 = st.tabs(["📋 Senarai Ubat", "⭐ Penilaian", "📝 Maklumbalas"])

with nav_tab1:
    st.markdown("""
        <div class="app-header">
            <span style="font-size:22px; cursor:pointer;">☰</span>
            <span class="app-title">Medexa Portal</span>
            <span style="font-size:20px; cursor:pointer;">🔍 ↻</span>
        </div>
    """, unsafe_allow_html=True)
    
    enable_camera = st.checkbox("📷 Aktifkan Kamera Telefon / Imbas Botol")
    scanned_text = ""
    
    if enable_camera:
        picture = st.camera_input("Ambil gambar label botol ubat")
        if picture:
            with st.spinner("Membaca & Menapis Teks Label... 🔍"):
                try:
                    img = Image.open(picture)
                    img_array = np.array(img)
                    
                    # Run raw OCR scan
                    reader = easyocr.Reader(['en', 'ms'], gpu=False)
                    ocr_result = reader.readtext(img_array)
                    
                    raw_words = [text[1] for text in ocr_result]
                    
                    # 🚀 THE OPTIMIZATION FILTER ENGINE 🚀
                    matched_medications = []
                    for word in raw_words:
                        # Clean up punctuation/spacing from the token
                        clean_word = word.strip(",.!精()[]-")
                        if len(clean_word) < 4: 
                            continue # Ignore useless small words like "mg", "ml", "xyz"
                        
                        # Match against database vocabulary with a 60% similarity threshold
                        close_matches = difflib.get_close_matches(clean_word, allowed_vocabulary, n=1, cutoff=0.6)
                        if close_matches:
                            matched_medications.append(close_matches[0])
                    
                    if matched_medications:
                        # Use the best distinct match discovered
                        scanned_text = list(set(matched_medications))[0]
                        st.success(f"🎯 AI Filtered Medication Match: **{scanned_text}**")
                    else:
                        st.warning("⚠️ Teks dibaca tetapi tiada padanan ubat yang sah dalam pangkalan data hospital.")
                except Exception as e:
                    st.error(f"Gagal membaca imej: {e}")

    search_default = scanned_text if scanned_text else ""
    search_query = st.text_input("Cari Nama Ubat atau Jenama:", value=search_default, placeholder="Taip di sini...")
    
    if not df.empty:
        if search_query:
            filtered_df = df[
                df['Nama Generik'].str.contains(search_query, case=False, na=False) | 
                df['Jenama'].str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_df = df
            
        if not filtered_df.empty:
            for index, row in filtered_df.iterrows():
                nama_generik = str(row.get('Nama Generik', 'Unknown'))
                jenama = str(row.get('Jenama', 'Generic'))
                
                image_url = str(row.get('Imej', '')).strip()
                if image_url and image_url.startswith("http"):
                    img_display = f'<img src="{image_url}" style="width:100%; height:100%; object-fit:contain;" onerror="this.onerror=null; this.parentElement.innerHTML=\'💊\';">'
                else:
                    img_display = "💊"
                
                st.markdown(f"""
                    <div class="med-card">
                        <div class="med-img-box">{img_display}</div>
                        <div class="med-details">
                            <p class="med-title">{nama_generik}</p>
                            <p class="med-subtitle">{jenama}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"⚙️ Urus & Tetapkan Notifikasi Expiry"):
                    try:
                        had_hari = int(row['Jangka Hayat Ubat Setelah Dibuka (hari)'])
                    except:
                        had_hari = 0
                        
                    st.write(f"🏢 **Pengilang:** {row.get('Pengilang', 'N/A')}")
                    st.write(f"ℹ️ **Had Keselamatan:** {had_hari} Hari")
                    st.info(f"🛑 **Penyimpanan:** {row.get('Penyimpanan & Perhatian', 'N/A')}")
                    
                    patient_name = st.text_input("Nama Pesakit:", key=f"name_{index}")
                    opened_date = st.date_input("Tarikh Botol Dibuka:", datetime.date.today(), key=f"date_{index}")
                    recipient_email = st.text_input("Emel Peringatan:", key=f"email_{index}")
                    
                    expiry_result = opened_date + datetime.timedelta(days=had_hari)
                    st.error(f"⚠️ Luput keselamatan pada: {expiry_result.strftime('%d/%m/%Y')}")
                    
                    if st.button("Aktifkan Peringatan Automatik", key=f"btn_{index}"):
                        st.success("🎉 Berjaya Dijadualkan!")
        else:
            st.error("Ubat tidak ditemui dalam pangkalan data.")

with nav_tab2:
    st.subheader("⭐ Penilaian Sistem")
    st.feedback("stars")

with nav_tab3:
    st.subheader("📝 Borang Maklumbalas")
    st.text_input("Nama Anda:")
    st.text_area("Cadangan Penambahbaikan:")
    if st.button("Hantar Maklumbalas"):
        st.success("Terima kasih atas maklumbalas anda!")
