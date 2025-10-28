import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import io
import html

# -----------------------------
# App Configuration
# -----------------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="📊", layout="centered")

st.title("📊 RI Exam Marks & Rank Calculator (Secure Mode)")
st.caption("Your data is processed safely and never stored or shared. All processing happens in memory only.")

# -----------------------------
# Candidate Details
# -----------------------------
st.subheader("🧾 Candidate Information")

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Full Name")
    gender = st.radio("Gender", ["Male", "Female", "Other"])
with col2:
    roll_no = st.text_input("Roll Number")
    medium = st.selectbox("Medium of Examination", ["English", "Odia"])

st.markdown("---")

# -----------------------------
# File Upload Section
# -----------------------------
st.subheader("📂 Upload Response Sheet")

st.info("Upload your combined response sheet file in **CSV** or **HTML** format. "
        "Your file is read only in memory — it is **not uploaded or saved anywhere.**")

file = st.file_uploader("🧾 Upload Response Sheet", type=["csv", "html"])

# -----------------------------
# Safe HTML Parser
# -----------------------------
def parse_html_response_sheet(html_bytes):
    """Safely extract Qno, Correct_Answer, and Response from an HTML file."""
    html_text = html.escape(html_bytes.decode("utf-8"))  # escape to neutralize scripts
    soup = BeautifulSoup(html_text, "html.parser")

    # remove potentially dangerous tags
    for tag in soup(["script", "style", "iframe"]):
        tag.decompose()

    # Try extracting tables
    tables = pd.read_html(io.StringIO(str(soup)), flavor='lxml')
    if not tables:
        raise ValueError("No readable table found in HTML file.")

    # Try to identify the correct table
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

    # Clean potential script text
    df = df.applymap(lambda x: html.escape(str(x)))
    return df

# -----------------------------
# Main Logic
# -----------------------------
if st.button("🔍 Calculate Marks"):

    if file is not None:
        try:
            # Process uploaded file securely
            if file.name.endswith('.csv'):
                data = pd.read_csv(file)
            elif file.name.endswith('.html'):
                data = parse_html_response_sheet(file.read())
            else:
                st.error("Unsupported file format. Please upload CSV or HTML.")
                st.stop()

            required_columns = {"Qno", "Correct_Answer", "Response"}
            if not required_columns.issubset(set(data.columns)):
                st.error("⚠️ File must contain: Qno, Correct_Answer, Response")
                st.stop()

            # Evaluation
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

            # Display result
            st.markdown("---")
            st.subheader("🏆 Result Summary")
            st.write(f"**Name:** {html.escape(name) if name else 'N/A'}")
            st.write(f"**Roll No.:** {html.escape(roll_no) if roll_no else 'N/A'}")
            st.write(f"**Gender:** {gender}")
            st.write(f"**Medium:** {medium}")
            st.write("---")
            st.write(f"✅ **Correct:** {correct}")
            st.write(f"❌ **Wrong:** {wrong}")
            st.write(f"⚪ **Unattempted:** {unattempted}")
            st.write(f"🎯 **Total Marks:** `{total_marks:.2f} / 100`")
            st.write(f"📈 **Estimated Rank Range:** {rank_est}")

            # Section-wise analysis (if present)
            if "Section" in data.columns:
                st.write("---")
                st.subheader("📚 Section-wise Performance")
                section_summary = data.groupby("Section")["Result"].value_counts().unstack(fill_value=0)
                st.dataframe(section_summary)

            # Download Result (in memory only)
            data["Marks"] = np.where(
                data["Result"] == "Correct", 1,
                np.where(data["Result"] == "Wrong", -1/3, 0)
            )
            csv_data = data.to_csv(index=False).encode('utf-8')

            st.download_button(
                "📥 Download Detailed Result (CSV)",
                csv_data,
                "RI_Exam_Result.csv",
                "text/csv"
            )

        except Exception as e:
            st.error("⚠️ Secure Processing Error — your file may not be formatted correctly or is unsafe.")
            st.stop()
    else:
        st.warning("⚠️ Please upload your response sheet before clicking Calculate.")
else:
    st.info("👆 Fill in your details and upload your response sheet, then click **Calculate Marks**.")
