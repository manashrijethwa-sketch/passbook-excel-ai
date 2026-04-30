# =========================
# ALL-IN-ONE PASSBOOK AI SAAS
# =========================

import streamlit as st
import pytesseract
import cv2
import numpy as np
import pandas as pd
import re
from PIL import Image
from datetime import datetime
import requests

# Optional AI OCR (Google Document AI)
USE_AI = False
GOOGLE_API_KEY = "YOUR_API_KEY"

# ---------------- UI CONFIG ----------------
st.set_page_config(layout="wide")

st.markdown("""
<style>
body {
    background: linear-gradient(to right, #00c6ff, #0072ff);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(to bottom, #ff7e5f, #feb47b);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- AUTH (SaaS placeholder) ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login (Demo SaaS)")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Smart Controls")

bank_name = st.sidebar.text_input("🏦 Bank Name")
account_holder = st.sidebar.text_input("👤 Account Holder")
flat_no = st.sidebar.text_input("🏠 Flat No.")

ocr_mode = st.sidebar.selectbox("OCR Mode", ["Fast (Tesseract)", "AI (High Accuracy)"])
export_format = st.sidebar.selectbox("Export", ["Excel", "CSV"])

st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Use clear images for 90%+ accuracy")

# ---------------- TITLE ----------------
st.title("📘 AI Passbook → Excel SaaS")

uploaded_file = st.file_uploader("Upload Passbook Image", type=["png","jpg","jpeg"])

# ---------------- IMAGE PREPROCESS ----------------
def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(5,5),0)
    thresh = cv2.threshold(blur,150,255,cv2.THRESH_BINARY)[1]
    return thresh

# ---------------- OCR ----------------
def tesseract_ocr(img):
    return pytesseract.image_to_string(img)

def ai_ocr(image):
    """Google Vision style API"""
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_API_KEY}"

    _, img_encoded = cv2.imencode('.jpg', image)
    content = img_encoded.tobytes()

    body = {
        "requests": [{
            "image": {"content": content.decode('latin1')},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
        }]
    }

    try:
        res = requests.post(url, json=body)
        return res.json()['responses'][0]['fullTextAnnotation']['text']
    except:
        return ""

# ---------------- SMART PARSER ----------------
def smart_parse(text):
    lines = text.split("\n")
    data = []

    for line in lines:
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', line)
        amount_match = re.search(r'\d+\.\d{2}', line)

        if date_match and amount_match:
            amount = float(amount_match.group())

            entry = {
                "Date": date_match.group(),
                "Bank Name": bank_name,
                "Account Holder": account_holder,
                "Flat No": flat_no,
                "Description": line,
                "Amount": amount,
                "Debit": "",
                "Credit": "",
                "UPI": "Yes" if "UPI" in line.upper() else "No"
            }

            if any(x in line.upper() for x in ["DR", "DEBIT", "-"]):
                entry["Debit"] = amount
            else:
                entry["Credit"] = amount

            data.append(entry)

    df = pd.DataFrame(data)

    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df = df.sort_values("Date")

    return df

# ---------------- MAIN FLOW ----------------
if uploaded_file:
    image = Image.open(uploaded_file)
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    processed = preprocess(img)
    st.image(processed, caption="Processed Image")

    # OCR Selection
    if ocr_mode.startswith("AI"):
        text = ai_ocr(processed)
    else:
        text = tesseract_ocr(processed)

    # Parse
    df = smart_parse(text)

    if not df.empty:
        st.success("✅ Data Extracted")

        # ---------------- HUMAN-IN-LOOP EDIT ----------------
        edited_df = st.data_editor(df, num_rows="dynamic")

        # ---------------- EXPORT ----------------
        file_name = f"passbook_{datetime.now().strftime('%Y%m%d')}"

        if export_format == "Excel":
            file_name += ".xlsx"
            edited_df.to_excel(file_name, index=False)
        else:
            file_name += ".csv"
            edited_df.to_csv(file_name, index=False)

        with open(file_name, "rb") as f:
            st.download_button("⬇️ Download File", f, file_name)

    else:
        st.warning("⚠️ No structured data detected")

# ---------------- FUTURE API (FASTAPI STYLE MOCK) ----------------
def api_extract(image_bytes):
    """Simulated backend endpoint"""
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    processed = preprocess(img)
    text = tesseract_ocr(processed)
    return smart_parse(text)

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("🚀 Built as AI SaaS Prototype | Upgrade with Document AI for 90%+ accuracy")
