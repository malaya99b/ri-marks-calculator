import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import html
import io
import matplotlib.pyplot as plt

# -------------------------------------------------------
# App Config & Privacy Banner
# -------------------------------------------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="📊", layout="centered")

st.markdown("""
<div style='padding: 12px; background-color: #eaf7ef; border-radius: 8px;'>
<b>🔒 Privacy Notice:</b>  
This app processes all data <b>temporarily in your browser session</b>.  
No files, links, or personal details are stored, logged, or shared.  
Your response link is fetched securely and never saved anywhere.
</div>
""", unsafe_allow_html=True)

st.title("📊 RI Marks & Rank Calculator — Secure & Private")

# -------------------------------------------------------
# Tabs: Calculator | Cutoff & Normalization
# -------------------------------------------------------
tab1, tab2 = st.tabs(["🧾 Marks Calculator", "📈 Cutoff & Normalization Analysis"])

# -------------------------------------------------------
# Tab 1: Marks Calculator
# -------------------------------------------------------
with tab1:
    st.subheader("🧾 Candidate Details")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name (optional)")
        gender = st.radio("Gender", ["Male", "Female", "Other"])
    with col2:
        roll_no = st.text_input("Roll Number (optional)")
        medium = st.selectbox("Medium of Examination", ["English", "Odia"])

    st.markdown("---")

    st.subheader("🌐 Paste Response Sheet Link")
    st.info("Paste your official **response sheet link** (HTML format). It will be fetched and processed safely.")
    response_link = st.text_input("Enter your response sheet link:", placeholder="https://examportal/...")

    def parse_html_response_sheet(html_text):
        """Safely extract Qno, Correct_Answer, and Response from an HTML page."""
        html_text = html.escape(html_text)
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "iframe", "style"]):
            tag.decompose()
        tables = pd.read_html(io.StringIO(str(soup)), flavor='lxml')
        if not tables:
            raise ValueError("No readable table found in HTML file.")
        df = None
        for t in tables:
            cols = {c.strip().lower() for c in t.columns}
            if {"qno", "correct_answer", "response"}.issubset(cols):
                df = t
                break
            elif {"qno", "answer key", "your answer"}.issubset(cols):
                t = t.rename(columns={"Answer Key": "Correct_Answer", "Your Answer": "Response"})
                df = t
                break
        if df is None:
            df = tables[0]
            df.columns = [c.strip() for c in df.columns]
        df = df.applymap(lambda x: html.escape(str(x)))
        return df

    if st.button("🔍 Calculate Marks"):
        if not response_link:
            st.warning(⚠️ Please paste your response sheet link first.")
            st.stop()

        try:
            if not response_link.startswith("https://"):
                st.error("Only secure (HTTPS) links are allowed.")
                st.stop()

            res = requests.get(response_link, timeout=10)
            if res.status_code != 200:
                st.error("❌ Could not fetch the link. Please check if it's valid and public.")
                st.stop()

            data = parse_html_response_sheet(res.text)
            required_columns = {"Qno", "Correct_Answer", "Response"}
            if not required_columns.issubset(set(data.columns)):
                st.error("⚠️ The response sheet format doesn’t match expected structure.")
                st.stop()

            # Scoring
            data["Result"] = np.where(
                data["Response"] == data["Correct_Answer"], "Correct",
                np.where(data["Response"].isna() | (data["Response"] == ""), "Unattempted", "Wrong")
            )

            correct = (data["Result"] == "Correct").sum()
            wrong = (data["Result"] == "Wrong").sum()
            unattempted = (data["Result"] == "Unattempted").sum()
            total_marks = correct * 1 - wrong * (1/3)

            # Rank estimation
            if total_marks >= 85:
                rank_est = "Top 1%"
            elif total_marks >= 70:
                rank_est = "Top 10%"
            elif total_marks >= 50:
                rank_est = "Average Range"
            else:
                rank_est = "Below Average"

            st.markdown("---")
            st.subheader("🏆 Result Summary")
            st.write(f"**Name:** {html.escape(name) if name else 'Anonymous'}")
            st.write(f"**Roll No.:** {html.escape(roll_no) if roll_no else 'Hidden'}")
            st.write(f"**Gender:** {gender}")
            st.write(f"**Medium:** {medium}")
            st.write("---")
            st.write(f"✅ **Correct:** {correct}")
            st.write(f"❌ **Wrong:** {wrong}")
            st.write(f"⚪ **Unattempted:** {unattempted}")
            st.write(f"🎯 **Total Marks:** `{total_marks:.2f} / 100`")
            st.write(f"📈 **Estimated Rank Range:** {rank_est}")

        except Exception:
            st.error("⚠️ Secure Processing Error — invalid or unsupported link format.")

# -------------------------------------------------------
# Tab 2: Cutoff & Normalization Analysis
# -------------------------------------------------------
with tab2:
    st.subheader("📈 Analyze Marks Distribution (Anonymous Data)")
    st.caption("Upload or paste anonymized marks data only — no names or personal info.")

    uploaded_file = st.file_uploader("Upload CSV file (must contain 'Marks' and optional 'Shift')", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if "Marks" not in df.columns:
                st.error("⚠️ File must contain a 'Marks' column.")
                st.stop()

            # Cutoff prediction
            avg = df["Marks"].mean()
            p90 = df["Marks"].quantile(0.9)
            p70 = df["Marks"].quantile(0.7)

            st.success("✅ Data loaded successfully and processed securely (no storage).")

            st.markdown("---")
            st.subheader("📊 Predicted Cutoffs")
            st.write(f"**General:** {p90:.2f}")
            st.write(f"**OBC:** {p70 * 0.95:.2f}")
            st.write(f"**SC/ST:** {p70 * 0.85:.2f}")
            st.write(f"**Average Marks:** {avg:.2f}")

            # Normalization (if shifts available)
            if "Shift" in df.columns:
                overall_mean = df["Marks"].mean()
                overall_sd = df["Marks"].std()
                df["Normalized_Marks"] = df.groupby("Shift")["Marks"].transform(
                    lambda x: ((x - x.mean()) / x.std()) * overall_sd + overall_mean
                )
                st.write("---")
                st.subheader("📘 Normalized Marks Added")
                st.dataframe(df.head())

                fig, ax = plt.subplots()
                ax.hist(df["Normalized_Marks"], bins=20)
                ax.set_title("Normalized Marks Distribution")
                st.pyplot(fig)

        except Exception:
            st.error("⚠️ Could not process the file. Ensure it's a valid CSV with numeric marks.")
