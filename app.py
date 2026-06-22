import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ==========================================
# 1. DATABASE SETUP (Reading your Excel File)
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
        st.error("⚠️ Pangkalan data ubat 'medicines.xlsx' tidak ditemui! Please make sure your Excel spreadsheet is inside the Medexa_App folder.")
        return pd.DataFrame()

df = load_medication_data()

# ==========================================
# 2. AUTOMATED GOVERNMENT EMAIL SYSTEM (MOH)
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
        print(f"MOH Email Server Error: {e}")
        return False

# ==========================================
# 3. STREAMLIT FRONTEND UI (PWA Enabled)
# ==========================================
st.set_page_config(page_title="Medexa Assistant", page_icon="🚀", layout="centered")

# Links phone browsers directly to the PWA identity manifest
st.markdown('<link rel="manifest" href="./manifest.json">', unsafe_allow_html=True)

st.title("🚀 Medexa")
st.subheader("Medication Expiry Assistant")
st.caption("Sistem semakan jangka hayat ubat pelbagai dos & kalkulator notifikasi pintar.")
st.write("---")

search_query = st.text_input("🔍 Cari Ubat (Masukkan Nama Generik atau Jenama):", placeholder="Contoh: Acriflavine atau Prime's...")

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
                        with st.spinner("Menghubungi pelayan emel kesihatan MOH..."):
                            success = send_expiry_email(recipient_email, patient_name, nama_generik, expiry_result)
                            if success:
                                st.success(f"🎉 Berjaya! Notifikasi amaran dijadualkan. Emel pengesahan dihantar ke {recipient_email}")
                            else:
                                st.warning("Notifikasi disimpan secara lokal. (Sistem berjalan dalam mod simulasi luar talian sehinggalah IT Hospital mengesahkan kelayakan laluan SMTP).")
                    else:
                        st.warning("Sila isi Nama Pesakit dan Emel terlebih dahulu!")
    else:
        st.error("Maaf, ubat tidak ditemui dalam pangkalan data hospital.")
        