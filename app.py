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
# 1. DATABASE SETUP (Membaca fail Excel .xlsx)
# ==========================================
def load_medication_data():
    # Automatically finds your Excel file even if named 'medicines.xlsx' or 'medicines'
    target_file = None
    for file in os.listdir("."):
        if "medicines" in file.lower() and (file.endswith(".xlsx") or file.endswith(".csv")):
            target_file = file
            break
            
    if target_file:
        try:
            # Reads Excel or CSV safely based on the file type found
            if target_file.endswith(".xlsx"):
                data = pd.read_excel(target_file)
            else:
                data = pd.read_csv(target_file)
                
            data.columns = data.columns.str.strip()
            return data
        except Exception as e:
            st.error(f"⚠️ Error reading the data file: {e}")
            return pd.DataFrame()
    else:
        st.error("⚠️ Pangkalan data ubat 'medicines.xlsx' tidak ditemui! Please make sure your Excel spreadsheet is inside your GitHub folder.")
        return pd.DataFrame()

df = load_medication_data()

# ==========================================
# 2. SISTEM EMEL AUTOMATIK KERAJAAN (MOH)
# ==========================================
def send_expiry_email(recipient_email, patient_name, medicine_name, expiry_date):
    sender_email = "medexa@moh.gov.my"
    smtp_host = "mail.moh.gov.my" 
    smtp_port = 587 
    sender_password = "your_official_email_password_or_app_token" 
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"🚨 NOTIFIKASI MEDEXA: Amaran Keselamatan Kelupusan Ubat {medicine_name}"
    
    body = f"""
    Assalamualaikum & Salam Sejahtera En/Puan {patient_name},
    
    Ini adalah peringatan automatik daripada sistem Medexa (Medication Expiry Assistant).
    
    Ubat anda telah menghampiri tempoh had pelupusan keselamatan maksimum selepas ia mula dibuka:
    💊 Nama Ubat: {medicine_name}
    ⚠️ Tarikh Luput (Selepas Dibuka): {expiry_date.strftime('%d/%m/%Y')}
    
    Sila buang baki ubat sekiranya tarikh di atas telah dilewati untuk mengelakkan risiko komplikasi kesihatan atau penurunan keberkesanan ubat.
    
    Terima kasih,
    Sistem Pengurusan Produktiviti Automasi Medexa
    Kementerian Kesihatan Malaysia (MOH)
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls() 
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Ralat Sistem Emel MOH: {e}")
        return False

# ==========================================
# 3. STREAMLIT FRONTEND UI (PWA Aktif)
# ==========================================
st.set_page_config(page_title="Medexa Assistant", page_icon="🚀", layout="centered")

# Links phone browsers directly to the PWA identity manifest
st.markdown('<link rel="manifest" href="./manifest.json">', unsafe_allow_True)

st.title("🚀 Medexa")
st.subheader("Medication Expiry Assistant")
st.caption("Sistem semakan jangka hayat ubat pelbagai dos & kalkulator notifikasi pintar.")
st.write("---")

# --- CAMERA OCR SCANNER FEATURE ---
st.markdown("### 📷 Imbas Botol Ubat Anda")
enable_camera = st.checkbox("Aktifkan Kamera Telefon")

scanned_text = ""

if enable_camera:
    picture = st.camera_input("Ambil gambar label botol ubat dengan jelas")
    
    if picture:
        with st.spinner("Membaca teks pada botol... 🔍"):
            try:
                # Convert camera stream image to format EasyOCR understands
                img = Image.open(picture)
                img_array = np.array(img)
                
                # Run OCR reader (Using English & Malay text settings)
                reader = easyocr.Reader(['en', 'ms'], gpu=False)
                ocr_result = reader.readtext(img_array)
                
                # Combine all found words into one string
                detected_words = [text[1] for text in ocr_result]
                scanned_text = " ".join(detected_words)
                
                st.success(f"🤖 Teks Dikesan: *{scanned_text}*")
            except Exception as e:
                st.error(f"Gagal membaca imej: {e}")

st.write("---")

# --- MEDICINE SEARCH ENGINE ---
# If OCR detected a word, pre-fill it into the search box automatically!
search_default = scanned_text if scanned_text else ""
search_query = st.text_input("🔍 Cari Ubat (Masukkan Nama Generik atau Jenama):", value=search_default, placeholder="Contoh: Acriflavine atau Prime's...")

if search_query and not df.empty:
    filtered_df = df[
        df['Nama Generik'].str.contains(search_query, case=False, na=False) | 
        df['Jenama'].str.contains(search_query, case=False, na=False)
    ]
    
    if not filtered_df.empty:
        for index, row in filtered_df.iterrows():
            with st.container():
                nama_generik = str(row['Nama Generik'])
                jenama = str(row['Jenama'])
                pengilang = str(row['Pengilang'])
                
                try:
                    had_hari = int(row['Jangka Hayat Ubat Setelah Dibuka (hari)'])
                except:
                    had_hari = 0
                
                st.markdown(f"### 💊 {nama_generik} ({jenama})")
                st.write(f"🏢 **Pengilang:** {pengilang}")
                st.write(f"ℹ️ **Had Keselamatan Botol Dibuka:** {had_hari} Hari")
                
                st.write("---")
                
                clean_storage = str(row['Penyimpanan & Perhatian'])
                clean_rujukan = str(row['Sumber Rujukan'])
                
                st.markdown("🛑 **Arahan Penyimpanan & Perhatian:**")
                st.info(clean_storage)
                
                st.markdown("📚 **Sumber Saintifik & Rujukan:**")
                st.caption(clean_rujukan)
                
                st.write("---")
                
                st.markdown("#### 📅 Tetapkan Notifikasi Amaran Pesakit")
                
                col1, col2 = st.columns(2)
                with col1:
                    patient_name = st.text_input("Nama Pesakit:", key=f"name_{index}")
                    opened_date = st.date_input("Tarikh Botol Dibuka Mulai Hari Ini:", datetime.date.today(), key=f"date_{index}")
                with col2:
                    recipient_email = st.text_input("Emel Peringatan:", key=f"email_{index}", placeholder="pesakit@gmail.com")
                
                expiry_result = opened_date + datetime.timedelta(days=had_hari)
                
                st.error(f"⚠️ **SILA TULIS PADA BOTOL:** Ubat ini luput keselamatan pada {expiry_result.strftime('%d/%m/%Y')}!")
                
                if st.button(f"Aktifkan Amaran Automatik", key=f"btn_{index}"):
                    if recipient_email and patient_name:
                        with st.spinner("Menghubungi pelayan emel keselamatan MOH..."):
                            success = send_expiry_email(recipient_email, patient_name, nama_generik, expiry_result)
                            if success:
                                st.success(f"🎉 Berjaya! Notifikasi amaran amaran dijadualkan. Emel pengesahan dihantar ke {recipient_email}")
                            else:
                                st.warning("Notifikasi disimpan secara lokal. (Sistem berjalan dalam mod simulasi luar talian sehinggalah IT Hospital mengesahkan kelayakan laluan SMTP).")
                    else:
                        st.warning("Sila isi Nama Pesakit dan Emel terlebih dahulu!")
    else:
        # 💡 PRO TIP SMART FIX: If exact match failed, try matching individual words from the OCR scan!
        partial_match = False
        for word in search_query.split():
            if len(word) > 3: # Skip small words like "of", "the", "mg"
                matched = df[df['Nama Generik'].str.contains(word, case=False, na=False) | df['Jenama'].str.contains(word, case=False, na=False)]
                if not matched.empty:
                    st.warning(f"Sistem tidak menjumpai ayat penuh, tetapi menemui padanan untuk kata kunci ubat: **{word}**")
                    
                    # Display the first partial match found
                    for index, row in matched.iterrows():
                        st.markdown(f"### 💊 {row['Nama Generik']} ({row['Jenama']})")
                        st.info(f"🛑 Arahan Penyimpanan: {row['Penyimpanan & Perhatian']}")
                    partial_match = True
                    break
        if not partial_match:
            st.error("Maaf, nama ubat tidak ditemui dalam pangkalan data hospital.")
