import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="📊", layout="centered")

st.title("📊 RI Exam Marks & Rank Calculator")
st.write("Upload your combined response sheet (with both correct answers and your responses) to calculate your score and estimated rank.")

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

st.write("Please upload your combined response sheet file (CSV or Excel). It must include columns: **Qno, Correct_Answer, Response**.")

file = st.file_uploader("🧾 Upload Response Sheet", type=["csv", "xlsx"])

# -----------------------------
# Process Logic
# -----------------------------
if st.button("🔍 Calculate Marks"):

    if file is not None:
        try:
            # Read uploaded file
            if file.name.endswith('.csv'):
                data = pd.read_csv(file)
            else:
                data = pd.read_excel(file)

            required_columns = {"Qno", "Correct_Answer", "Response"}
            if not required_columns.issubset(data.columns):
                st.error("⚠️ The uploaded file must contain the columns: Qno, Correct_Answer, Response")
            else:
                # -----------------------------
                # Evaluation
                # -----------------------------
                data["Result"] = np.where(
                    data["Response"] == data["Correct_Answer"], "Correct",
                    np.where(data["Response"].isna() | (data["Response"] == ""), "Unattempted", "Wrong")
                )

                # Count results
                correct = (data["Result"] == "Correct").sum()
                wrong = (data["Result"] == "Wrong").sum()
                unattempted = (data["Result"] == "Unattempted").sum()

                # Score
                total_marks = correct * 1 - wrong * (1/3)

                # Rank estimation (example logic)
                if total_marks >= 85:
                    rank_est = "Top 1%"
                elif total_marks >= 70:
                    rank_est = "Top 10%"
                elif total_marks >= 50:
                    rank_est = "Average Range"
                else:
                    rank_est = "Below Average"

                # -----------------------------
                # Result Display
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

                # Section-wise performance (optional)
                if "Section" in data.columns:
                    st.write("---")
                    st.subheader("📚 Section-wise Performance")
                    section_summary = data.groupby("Section")["Result"].value_counts().unstack(fill_value=0)
                    st.dataframe(section_summary)

                # -----------------------------
                # Download Button
                # -----------------------------
                data["Marks"] = np.where(
                    data["Result"] == "Correct", 1,
                    np.where(data["Result"] == "Wrong", -1/3, 0)
                )
                data["Candidate_Name"] = name
                data["Roll_No"] = roll_no
                data["Gender"] = gender
                data["Medium"] = medium

                st.download_button(
                    "📥 Download Detailed Result (CSV)",
                    data.to_csv(index=False).encode('utf-8'),
                    "RI_Exam_Result.csv",
                    "text/csv"
                )

        except Exception as e:
            st.error(f"⚠️ Error processing file: {e}")

    else:
        st.warning("⚠️ Please upload your response sheet before clicking Calculate.")

else:
    st.info("👆 Fill in your details and upload your response sheet, then click **Calculate Marks**.")

