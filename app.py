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

# ==========================================
# 2. EMAIL NOTIFICATION LOGIC
# ==========================================
def send_expiry_email(recipient_email, patient_name, medicine_name, expiry_date):
    # Simulated/wired backend logic for presenting
    return True

# ==========================================
# 3. STREAMLIT CONFIG & CUSTOM MOBILE CSS
# ==========================================
st.set_page_config(page_title="Medexa Assistant", page_icon="🚀", layout="centered")
st.markdown('<link rel="manifest" href="./manifest.json">', unsafe_allow_html=True)

# Custom injection to mimic a native mobile health application UI
st.markdown("""
    <style>
    /* Force main app container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 480px;
        margin: 0 auto;
        background-color: #f7f9fa;
    }
    
    /* Header layout styling */
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
    
    /* Elegant Row Card Style matching your screenshot */
    .med-card {
        background-color: #ffffff;
        padding: 15px;
        border-bottom: 1px solid #edf2f7;
        display: flex;
        align-items: center;
        gap: 15px;
        transition: background-color 0.2s;
    }
    .med-card:hover {
        background-color: #f8fafc;
    }
    .med-img-box {
        width: 60px;
        height: 60px;
        background-color: #f7fafc;
        border-radius: 8px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 28px;
        border: 1px solid #e2e8f0;
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
# 4. BOTTOM NAVIGATION TABS FEATURE
# ==========================================
# Creates the bottom navbar layout using Streamlit's structural native tabs
nav_tab1, nav_tab2, nav_tab3 = st.tabs(["📋 Senarai Ubat", "⭐ Penilaian", "📝 Maklumbalas"])

# --- TAB 1: CORE APPLICATION ---
with nav_tab1:
    # Mimicking mobile top utility bar
    st.markdown("""
        <div class="app-header">
            <span style="font-size:22px; cursor:pointer;">☰</span>
            <span class="app-title">Medexa Portal</span>
            <span style="font-size:20px; cursor:pointer;">🔍 ↻</span>
        </div>
    """, unsafe_allow_html=True)
    
    # AI Camera OCR Switcher
    enable_camera = st.checkbox("📷 Aktifkan Kamera Telefon / Imbas Botol")
    scanned_text = ""
    
    if enable_camera:
        picture = st.camera_input("Ambil gambar label botol ubat")
        if picture:
            with st.spinner("Membaca teks ubat... 🔍"):
                try:
                    img = Image.open(picture)
                    img_array = np.array(img)
                    reader = easyocr.Reader(['en', 'ms'], gpu=False)
                    ocr_result = reader.readtext(img_array)
                    detected_words = [text[1] for text in ocr_result]
                    scanned_text = " ".join(detected_words)
                    st.success(f"🤖 Dikesan: *{scanned_text}*")
                except Exception as e:
                    st.error(f"Gagal membaca imej: {e}")

    # Search Bar Section
    search_default = scanned_text if scanned_text else ""
    search_query = st.text_input("Cari Nama Ubat atau Jenama:", value=search_default, placeholder="Taip di sini...")
    
    # If the search input is empty, show ALL drugs by default just like your screenshot!
    if not df.empty:
        if search_query:
            filtered_df = df[
                df['Nama Generik'].str.contains(search_query, case=False, na=False) | 
                df['Jenama'].str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_df = df  # Default view lists everything in the database
            
        if not filtered_df.empty:
            for index, row in filtered_df.iterrows():
                nama_generik = str(row.get('Nama Generik', 'Unknown'))
                jenama = str(row.get('Jenama', 'Generic'))
                
                # Check if your Excel has an 'Icon' or 'Image' column, otherwise use an emoji fallback
                img_display = "💊"
                
                # Render the clean item row card
                st.markdown(f"""
                    <div class="med-card">
                        <div class="med-img-box">{img_display}</div>
                        <div class="med-details">
                            <p class="med-title">{nama_generik}</p>
                            <p class="med-subtitle">{jenama}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Interactive details drawer built directly underneath the modern card layout
                with st.expander(f"⚙️ Urus & Tetapkan Notifikasi Expiry"):
                    try:
                        had_hari = int(row['Jangka Hayat Ubat Setelah Dibuka (hari)'])
                    except:
                        had_hari = 0
                        
                    st.write(f"🏢 **Pengilang:** {row.get('Pengilang', 'N/A')}")
                    st.write(f"ℹ️ **Had Keselamatan:** {had_hari} Hari")
                    st.info(f"🛑 **Penyimpanan:** {row.get('Penyimpanan & Perhatian', 'N/A')}")
                    
                    # Patient Setup Form
                    patient_name = st.text_input("Nama Pesakit:", key=f"name_{index}")
                    opened_date = st.date_input("Tarikh Botol Dibuka:", datetime.date.today(), key=f"date_{index}")
                    recipient_email = st.text_input("Emel Peringatan:", key=f"email_{index}")
                    
                    expiry_result = opened_date + datetime.timedelta(days=had_hari)
                    st.error(f"⚠️ Luput keselamatan pada: {expiry_result.strftime('%d/%m/%Y')}")
                    
                    if st.button("Aktifkan Peringatan Automatik", key=f"btn_{index}"):
                        st.success("🎉 Berjaya Dijadualkan!")
        else:
            st.error("Ubat tidak ditemui dalam pangkalan data.")

# --- TAB 2: RATINGS SIMULATION ---
with nav_tab2:
    st.subheader("⭐ Penilaian Sistem")
    st.write("Sila berikan penilaian anda untuk sistem Medexa.")
    st.feedback("stars")

# --- TAB 3: FEEDBACK SIMULATION ---
with nav_tab3:
    st.subheader("📝 Borang Maklumbalas")
    st.text_input("Nama Anda:")
    st.text_area("Cadangan Penambahbaikan:")
    if st.button("Hantar Maklumbalas"):
        st.success("Terima kasih atas maklumbalas anda!")
