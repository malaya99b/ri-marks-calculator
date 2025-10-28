import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# Title and Intro
# -----------------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="📊", layout="centered")

st.title("📊 RI Exam Marks & Rank Calculator")
st.write("Welcome! Please fill in your details and upload your response sheet below to calculate your marks and estimated rank.")

# -----------------------------
# User Details Section
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
st.subheader("📂 Upload Files")

st.write("Please upload your **Answer Key** and **Response Sheet** in CSV or Excel format.")

key_file = st.file_uploader("📘 Upload Answer Key", type=["csv", "xlsx"])
resp_file = st.file_uploader("🧾 Upload Response Sheet", type=["csv", "xlsx"])

# -----------------------------
# Process Logic
# -----------------------------
if st.button("🔍 Calculate Marks"):

    if key_file is not None and resp_file is not None:
        try:
            # Read uploaded files
            if key_file.name.endswith('.csv'):
                answer_key = pd.read_csv(key_file)
            else:
                answer_key = pd.read_excel(key_file)

            if resp_file.name.endswith('.csv'):
                responses = pd.read_csv(resp_file)
            else:
                responses = pd.read_excel(resp_file)

            st.success("✅ Files uploaded successfully!")

            # Merge answer key and responses by Question Number
            merged = pd.merge(answer_key, responses, on="Qno", suffixes=('_key', '_resp'))

            # Evaluate answers
            merged["Result"] = np.where(
                merged["Answer_key"] == merged["Answer_resp"], "Correct",
                np.where(merged["Answer_resp"].isna(), "Unattempted", "Wrong")
            )

            # Calculate scores
            correct = (merged["Result"] == "Correct").sum()
            wrong = (merged["Result"] == "Wrong").sum()
            unattempted = (merged["Result"] == "Unattempted").sum()
            total_marks = correct * 1 - wrong * (1/3)

            # Estimated rank (basic logic for demo)
            if total_marks >= 85:
                rank_est = "Top 1%"
            elif total_marks >= 70:
                rank_est = "Top 10%"
            elif total_marks >= 50:
                rank_est = "Average Range"
            else:
                rank_est = "Below Average"

            # -----------------------------
            # Display Result Section
            # -----------------------------
            st.markdown("---")
            st.subheader("🏆 Result Summary")

            st.write(f"**Name:** {name if name else 'N/A'}")
            st.write(f"**Roll No.:** {roll_no if roll_no else 'N/A'}")
            st.write(f"**Gender:** {gender}")
            st.write(f"**Medium:** {medium}")

            st.write("---")
            st.write(f"✅ **Correct:** {correct}")
            st.write(f"❌ **Wrong:** {wrong}")
            st.write(f"⚪ **Unattempted:** {unattempted}")
            st.write(f"🎯 **Total Marks:** `{total_marks:.2f} / 100`")
            st.write(f"📈 **Estimated Rank Range:** {rank_est}")

            # Download button
            merged["Marks"] = np.where(
                merged["Result"] == "Correct", 1,
                np.where(merged["Result"] == "Wrong", -1/3, 0)
            )
            merged["Candidate_Name"] = name
            merged["Roll_No"] = roll_no
            merged["Gender"] = gender
            merged["Medium"] = medium

            st.download_button(
                "📥 Download Detailed Result (CSV)",
                merged.to_csv(index=False).encode('utf-8'),
                "RI_Exam_Result.csv",
                "text/csv"
            )

        except Exception as e:
            st.error(f"⚠️ Error processing files: {e}")
    else:
        st.warning("⚠️ Please upload both files before clicking Calculate.")

else:
    st.info("👆 Fill in all details and upload both files, then click **Calculate Marks**.")

