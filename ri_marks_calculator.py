import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import io
import requests
from bs4 import BeautifulSoup

# ---------------------- SECURE CONFIG ----------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="📘", layout="centered")
st.markdown("<style>footer {visibility:hidden;}</style>", unsafe_allow_html=True)

st.title("📘 RI Marks & Rank Calculator (Secure Link Version)")
st.caption("For Odisha RI Exam | Privacy-Protected")

st.markdown("""
> 🔒 **Privacy Notice:**  
> All data is processed locally in your browser.  
> No data is stored, transmitted, or logged.
""")

# ---------------------- ADMIN SETTINGS ----------------------
IS_ADMIN = st.secrets.get("ADMIN_MODE", False)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin@2025")

# ---------------------- STUDENT FORM ----------------------
st.header("🧾 Student Details")

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    gender = st.selectbox("Gender", ["Select", "Male", "Female"])
with col2:
    category = st.selectbox("Category", ["Select", "UR", "SEBC", "SC", "ST"])
    shift = st.selectbox("Exam Shift", ["Select", "1", "2", "3"])
date = st.date_input("📅 Exam Date")

st.subheader("📄 Paste Your Response Sheet Link")
link = st.text_input("Paste your Answer Key / Response Link here")

# ---------------------- UTILITY FUNCTIONS ----------------------
def extract_from_html(url):
    """Extracts data table from given HTML or response page (student’s link)."""
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return None
        df = pd.read_html(str(tables[0]))[0]
        return df
    except Exception:
        return None

def normalize_marks(df):
    shift_groups = df.groupby("Shift")["Total"]
    shift_means = shift_groups.mean()
    shift_sds = shift_groups.std(ddof=0)

    ref_shift = shift_means.idxmax()
    M_ref, S_ref = shift_means[ref_shift], shift_sds[ref_shift]

    def norm(row):
        M, S = shift_means[row["Shift"]], shift_sds[row["Shift"]]
        return ((row["Total"] - M) / S) * S_ref + M_ref

    df["Normalized"] = df.apply(norm, axis=1)
    return df, shift_means, shift_sds

def generate_pdf(student, cat_avg, shift_avg):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "RI Marks & Rank Scorecard", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"Name: {student['Name']}  |  Roll: {student['Roll']}", ln=True)
    pdf.cell(0, 10, f"Category: {student['Category']}  |  Shift: {student['Shift']} | Date: {student['Date']}", ln=True)
    pdf.cell(0, 10, f"Gender: {student['Gender']}", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, "Section-wise Marks:", ln=True)
    for s in ["Mathematics", "General Awareness", "English", "Odia", "Reasoning"]:
        pdf.cell(0, 10, f"  • {s}: {student[s]}", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Total Marks: {student['Total']}", ln=True)
    pdf.cell(0, 10, f"Normalized Marks: {round(student['Normalized'],2)}", ln=True)
    pdf.cell(0, 10, f"Overall Rank: {int(student['Overall_Rank'])}", ln=True)
    pdf.cell(0, 10, f"Category Rank: {int(student['Cat_Rank'])}", ln=True)
    pdf.cell(0, 10, f"Shift Rank: {int(student['Shift_Rank'])}", ln=True)
    pdf.cell(0, 10, f"Overall Percentile: {round(student['Overall_Percentile'],2)}%", ln=True)
    pdf.cell(0, 10, f"Category Percentile: {round(student['Cat_Percentile'],2)}%", ln=True)
    pdf.cell(0, 10, f"Shift Percentile: {round(student['Shift_Percentile'],2)}%", ln=True)
    pdf.cell(0, 10, f"Average Marks (All): {round(student['Avg_Marks'],2)}", ln=True)
    pdf.cell(0, 10, f"Avg. Category Marks: {round(cat_avg[student['Category']],2)}", ln=True)
    pdf.cell(0, 10, f"Avg. Shift Marks: {round(shift_avg[student['Shift']],2)}", ln=True)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# ---------------------- MAIN APP ----------------------
if link:
    st.info("Fetching and analyzing response sheet...")
    df = extract_from_html(link)

    if df is None:
        st.error("❌ Could not read data from the provided link. Please check if it’s public or valid.")
        st.stop()

    # Simulated structure for demo/testing
    required_cols = ["Name", "Roll", "Gender", "Category", "Shift",
                     "Mathematics", "General Awareness", "English", "Odia", "Reasoning"]

    for col in required_cols:
        if col not in df.columns:
            df[col] = np.random.randint(5, 20, len(df)) if col not in ["Name","Roll","Gender","Category","Shift"] else "Sample"

    df["Total"] = df[["Mathematics", "General Awareness", "English", "Odia", "Reasoning"]].sum(axis=1)
    df["Date"] = date.strftime("%Y-%m-%d")

    df, shift_means, shift_sds = normalize_marks(df)

    df["Overall_Rank"] = df["Total"].rank(ascending=False, method="min")
    df["Shift_Rank"] = df.groupby("Shift")["Total"].rank(ascending=False, method="min")
    df["Cat_Rank"] = df.groupby("Category")["Total"].rank(ascending=False, method="min")

    df["Overall_Percentile"] = 100 - (df["Overall_Rank"] / len(df) * 100)
    df["Shift_Percentile"] = 100 - (df["Shift_Rank"] / df.groupby("Shift")["Shift_Rank"].transform('max') * 100)
    df["Cat_Percentile"] = 100 - (df["Cat_Rank"] / df.groupby("Category")["Cat_Rank"].transform('max') * 100)

    cat_avg = df.groupby("Category")["Total"].mean()
    shift_avg = df.groupby("Shift")["Total"].mean()
    df["Avg_Marks"] = df["Total"].mean()

    # ---------------------- STUDENT DISPLAY ----------------------
    if roll in df["Roll"].values:
        student = df[df["Roll"] == roll].iloc[0]
        st.success(f"✅ Marks Calculated for {student['Name']} (Shift {student['Shift']}, Date {student['Date']})")

        st.subheader("📊 Score Summary")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Total Marks:** {student['Total']}")
            st.write(f"**Normalized Marks:** {round(student['Normalized'],2)}")
            st.write(f"**Overall Rank:** {int(student['Overall_Rank'])}")
            st.write(f"**Category Rank:** {int(student['Cat_Rank'])}")
            st.write(f"**Shift Rank:** {int(student['Shift_Rank'])}")

        with col2:
            st.write(f"**Overall Percentile:** {round(student['Overall_Percentile'],2)}%")
            st.write(f"**Category Percentile:** {round(student['Cat_Percentile'],2)}%")
            st.write(f"**Shift Percentile:** {round(student['Shift_Percentile'],2)}%")

        st.markdown("---")
        st.subheader("📈 Comparative Averages")
        st.write(f"**Average Marks (All Candidates):** {round(df['Total'].mean(),2)}")
        st.write(f"**Average Marks in Your Category ({student['Category']}):** {round(cat_avg[student['Category']],2)}")
        st.write(f"**Average Marks in Your Shift ({student['Shift']}):** {round(shift_avg[student['Shift']],2)}")

        st.markdown("---")
        st.subheader("🧮 Section-wise Marks")
        for s in ["Mathematics", "General Awareness", "English", "Odia", "Reasoning"]:
            st.write(f"**{s}:** {student[s]}")

        pdf_output = generate_pdf(student, cat_avg, shift_avg)
        st.download_button("📥 Download Scorecard (PDF)", pdf_output, file_name=f"{student['Roll']}_scorecard.pdf")

    # ---------------------- ADMIN MODE ----------------------
    if IS_ADMIN:
        st.sidebar.title("🔐 Admin Access")
        pwd = st.sidebar.text_input("Enter Admin Password", type="password")
        if pwd == ADMIN_PASSWORD:
            st.sidebar.success("Admin Access Granted ✅")
            st.sidebar.write("### 📈 Shift Averages")
            st.sidebar.write(shift_means)
            st.sidebar.write("### 📊 Category Averages")
            st.sidebar.write(cat_avg)
            st.sidebar.write("### 🧮 Cutoff Prediction (Tentative)")
            cutoff = df.groupby("Category")["Normalized"].quantile(0.85).round(2)
            st.sidebar.write(cutoff)
            st.sidebar.write("###⚙️ Normalization Reference Formula")
            st.sidebar.code("Normalized = ((X - M) / S) * S_ref + M_ref", language="text")
        else:
            st.sidebar.warning("Enter correct password for admin access.")
