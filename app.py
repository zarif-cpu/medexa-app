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
import difflib

# ==========================================
# 1. LIGHTNING FAST CACHED DATABASE SETUP
# ==========================================
@st.cache_data(ttl=3600)
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

if not df.empty:
    valid_generics = df['Nama Generik'].dropna().astype(str).tolist()
    valid_brands = df['Jenama'].dropna().astype(str).tolist()
    allowed_vocabulary = list(set(valid_generics + valid_brands))
else:
    allowed_vocabulary = []

@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['en', 'ms'], gpu=False)

reader = load_ocr_reader()

# ==========================================
# 2. LOCAL DATA STORAGE INITIALIZATION
# ==========================================
if "medicine_cabinet" not in st.session_state:
    st.session_state.medicine_cabinet = []

# ==========================================
# 3. STREAMLIT CONFIG & CUSTOM MOBILE CSS
# ==========================================
st.set_page_config(page_title="Medexa Assistant", page_icon="🏥", layout="centered")
st.markdown('<link rel="manifest" href="./manifest.json">', unsafe_allow_html=True)

st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 480px;
        margin: 0 auto;
        background-color: #f7f9fa;
    }
    .app-header {
        display: flex;
        justify-content: center;
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
        margin: 0 0 4
