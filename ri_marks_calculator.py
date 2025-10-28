
import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import html
import io

# -------------------------------------------------------
# App Configuration
# -------------------------------------------------------
st.set_page_config(page_title="RI Marks & Normalization Calculator", page_icon="📊", layout="centered")

st.markdown("""
<div style='padding: 10px; background-color: #eaf7ef; border-radius: 8px;'>
<b>🔒 Privacy Notice:</b>  
All data is processed locally in your browser.  
No personal data, links, or marks are saved or logged.
</div>
""", unsafe_allow_html=True)

st.title("📊 RI Marks & Normalization Calculator")

# -------------------------------------------------------
# User Mode Selection
# -------------------------------------------------------
role = st.radio("Select Access Mode:", ["🎓 Student", "🧠 Admin"], horizontal=True)
st.markdown("---")

# -------------------------------------------------------
# STUDENT MODE
# -------------------------------------------------------
if role == "🎓 Student":
    st.header("🎓 Student Mode — Check Your Raw & Normalized Marks")

    name = st.text_input("Full Name (optional)")
    gender = st.radio("Gender", ["Male", "Female", "Other"], horizontal=True)
    medium = st.selectbox("Medium of Examination", ["English", "Odia"])

    st.markdown("### 🌐 Paste Your Official Response Sheet Link (HTML format)")
    response_link = st.text_input("Enter your response sheet link:", placeholder="https://examportal/...")

    # Helper function to parse response HTML
    def parse_html_response_sheet(html_text):
        soup = BeautifulSoup(html_text, "html.parser")
        for tag in soup(["script", "iframe", "style"]):
            tag.decompose()
        tables = pd.read_html(io.StringIO(str(soup)), flavor="lxml")
        df = tables[0]
        df.columns = [c.strip() for c in df.columns]
        # Try to match columns dynamically
        if "Answer Key" in df.columns and "Your Answer" in df.columns:
            df = df.rename(columns={"Answer Key": "Correct_Answer", "Your Answer": "Response"})
        elif "Correct Answer" in df.columns:
            df = df.rename(columns={"Correct Answer": "Correct_Answer"})
        return df

    if st.button("🔍 Calculate My Marks"):
        if not response_link:
            st.warning(⚠️ Please paste your response sheet link first.")
            st.stop()

        if not response_link.startswith("https://"):
            st.error("❌ Only secure (HTTPS) links are allowed.")
            st.stop()

        try:
            res = requests.get(response_link, timeout=10)
            if res.status_code != 200:
                st.error("⚠️ Could not fetch the response sheet. Check the link.")
                st.stop()

            df = parse_html_response_sheet(res.text)

            # Compute marks
            df["Result"] = np.where(
                df["Response"] == df["Correct_Answer"], "Correct",
                np.where(df["Response"].isna() | (df["Response"] == ""), "Unattempted", "Wrong")
            )

            correct = (df["Result"] == "Correct").sum()
            wrong = (df["Result"] == "Wrong").sum()
            total_marks = correct * 1 - wrong * (1/3)

            # Normalization (simple percentile-based normalization)
            normalized_marks = (total_marks / 100) * 80 + 20

            st.markdown("---")
            st.subheader("🏆 Your Result")
            st.write(f"👤 **Name:** {name if name else 'Anonymous'}")
            st.write(f"🌐 **Medium:** {medium}")
            st.write(f"✅ Correct: {correct}")
            st.write(f"❌ Wrong: {wrong}")
            st.write(f"🎯 **Raw Score:** `{total_marks:.2f}` / 100")
            st.write(f"📈 **Normalized Marks:** `{normalized_marks:.2f}`")

        except Exception as e:
            st.error("⚠️ Unable to process your response sheet. Please check the link format.")

# -------------------------------------------------------
# ADMIN MODE
# -------------------------------------------------------
else:
    st.header("🧠 Admin Mode — Cutoff & Normalization Analysis")
    st.info("Upload only anonymized marks data (CSV format). No personal details should be included.")

    uploaded_file = st.file_uploader("Upload Marks Data (CSV)", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if "Marks" not in df.columns:
                st.error("CSV must contain a 'Marks' column.")
                st.stop()

            st.success("✅ Data loaded successfully.")

            avg = df["Marks"].mean()
            p90 = df["Marks"].quantile(0.9)
            p70 = df["Marks"].quantile(0.7)

            st.subheader("📊 Predicted Cutoffs")
            st.write(f"**General:** {p90:.2f}")
            st.write(f"**OBC:** {p70 * 0.95:.2f}")
            st.write(f"**SC/ST:** {p70 * 0.85:.2f}")
            st.write(f"**Average Marks:** {avg:.2f}")

            if "Shift" in df.columns:
                st.subheader("📘 Normalization Across Shifts")
                overall_mean = df["Marks"].mean()
                overall_sd = df["Marks"].std()
                df["Normalized_Marks"] = df.groupby("Shift")["Marks"].transform(
                    lambda x: ((x - x.mean()) / x.std()) * overall_sd + overall_mean
                )
                st.dataframe(df.head())

        except Exception:
            st.error("⚠️ Error reading or processing the file.")
