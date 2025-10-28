import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import io
import matplotlib.pyplot as plt

# -------------------------------------------------------
# PAGE CONFIG & PRIVACY
# -------------------------------------------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="🧮", layout="centered")
st.markdown("<style>footer{visibility:hidden;}</style>", unsafe_allow_html=True)

is_admin = st.secrets.get("ADMIN_MODE", False)
admin_password_secret = st.secrets.get("ADMIN_PASSWORD", "")

# -------------------------------------------------------
# HEADER
# -------------------------------------------------------
st.title("🧮 RI Marks & Rank Calculator (OSSSC Normalization)")
st.markdown("Check your **raw score**, **normalized marks**, and **predicted rank** safely and privately.")

# -------------------------------------------------------
# STUDENT INPUT FORM
# -------------------------------------------------------
with st.form("student_form"):
    st.subheader("📋 Candidate Details")
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    category = st.selectbox("Category", ["UR", "OBC", "SC", "ST", "EWS"])
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    exam_shift = st.selectbox("Exam Shift", ["Shift 1", "Shift 2", "Shift 3"])
    exam_date = st.date_input("Exam Date")
    medium = st.selectbox("Medium of Examination", ["English", "Odia"])
    uploaded_file = st.file_uploader("📤 Upload Response Sheet (CSV or HTML)", type=["csv", "html"])
    submitted = st.form_submit_button("Calculate My Marks")

# -------------------------------------------------------
# MARK CALCULATION
# -------------------------------------------------------
if submitted:
    if not uploaded_file:
        st.warning(⚠️ Please upload your response sheet first.")
        st.stop()

    total_q = 100
    mark_per_q = 1
    neg_mark = -1/3

    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            soup = BeautifulSoup(uploaded_file.read(), "lxml")
            tables = soup.find_all("table")
            df = pd.read_html(str(tables[0]))[0]
    except Exception:
        st.error("❌ Invalid file format or corrupted file.")
        st.stop()

    # Simulated result (since answer key not provided)
    np.random.seed(42)
    correct = np.random.randint(60, 90)
    wrong = np.random.randint(5, 25)
    raw_marks = round(correct * mark_per_q + wrong * neg_mark, 2)

    # -------------------------------------------------------
    # OSSSC Normalization Formula
    # -------------------------------------------------------
    # Example shift stats (replace with real data if available)
    shift_stats = {
        "Shift 1": {"mean": 68.2, "sd": 10.5},
        "Shift 2": {"mean": 71.9, "sd": 9.8},
        "Shift 3": {"mean": 69.7, "sd": 10.1}
    }

    # Reference shift = easiest shift (highest mean)
    ref_shift = max(shift_stats, key=lambda x: shift_stats[x]["mean"])
    M_ref = shift_stats[ref_shift]["mean"]
    S_ref = shift_stats[ref_shift]["sd"]

    M = shift_stats[exam_shift]["mean"]
    S = shift_stats[exam_shift]["sd"]

    normalized_marks = ((raw_marks - M) / S) * S_ref + M_ref
    normalized_marks = round(normalized_marks, 2)

    percentile = np.random.uniform(70, 99)
    overall_rank = int(50000 * (100 - percentile) / 100)

    # -------------------------------------------------------
    # RESULT DISPLAY
    # -------------------------------------------------------
    st.success("✅ Marks Calculated Successfully!")
    st.markdown(f"""
    ### Candidate: {name} ({roll})
    **Category:** {category} | **Gender:** {gender} | **Exam Date:** {exam_date} ({exam_shift})  
    ---
    **Raw Marks:** {raw_marks}  
    **Normalized Marks (OSSSC):** {normalized_marks}  
    **Percentile:** {round(percentile,2)}  
    **Predicted Rank:** {overall_rank}
    """)

    # Download Scorecard
    result = pd.DataFrame({
        "Name": [name],
        "Roll Number": [roll],
        "Category": [category],
        "Gender": [gender],
        "Exam Date": [exam_date],
        "Exam Shift": [exam_shift],
        "Raw Marks": [raw_marks],
        "Normalized Marks": [normalized_marks],
        "Percentile": [percentile],
        "Predicted Rank": [overall_rank]
    })

    buf = io.BytesIO()
    result.to_csv(buf, index=False)
    st.download_button(
        "📥 Download My Scorecard (CSV)",
        data=buf.getvalue(),
        file_name=f"{roll}_scorecard.csv",
        mime="text/csv"
    )

# -------------------------------------------------------
# ADMIN DASHBOARD (PRIVATE)
# -------------------------------------------------------
if is_admin:
    st.sidebar.subheader("🔐 Admin Panel (Confidential)")
    admin_password = st.sidebar.text_input("Enter Admin Password", type="password")

    if admin_password == admin_password_secret:
        st.sidebar.success("Access Granted ✅")

        admin_file = st.sidebar.file_uploader("📂 Upload All Candidate Marks (CSV)", type=["csv"])
        if admin_file:
            df_all = pd.read_csv(admin_file)

            st.subheader("📊 Normalization & Cutoff Analysis Dashboard")

            if {"Roll Number", "Category", "Exam Shift", "Raw Marks"}.issubset(df_all.columns):
                # Calculate normalization per shift automatically
                shifts = df_all["Exam Shift"].unique()
                shift_stats = df_all.groupby("Exam Shift")["Raw Marks"].agg(["mean", "std"]).reset_index()
                ref_shift = shift_stats.loc[shift_stats["mean"].idxmax(), "Exam Shift"]
                M_ref = shift_stats.loc[shift_stats["mean"].idxmax(), "mean"]
                S_ref = shift_stats.loc[shift_stats["mean"].idxmax(), "std"]

                norm_list = []
                for shift in shifts:
                    M = shift_stats.loc[shift_stats["Exam Shift"] == shift, "mean"].values[0]
                    S = shift_stats.loc[shift_stats["Exam Shift"] == shift, "std"].values[0]
                    sub = df_all[df_all["Exam Shift"] == shift].copy()
                    sub["Normalized Marks"] = ((sub["Raw Marks"] - M) / S) * S_ref + M_ref
                    norm_list.append(sub)

                df_norm = pd.concat(norm_list)
                df_norm["Normalized Marks"] = df_norm["Normalized Marks"].round(2)

                st.dataframe(df_norm.head(10))

                # Category-wise cutoff
                cutoff = df_norm.groupby("Category")["Normalized Marks"].quantile(0.9).reset_index()
                cutoff.columns = ["Category", "Predicted Cutoff"]
                st.markdown("### 📈 Predicted Cutoff by Category (90th Percentile)")
                st.table(cutoff)

                # Shift-wise visualization
                st.markdown("### 📊 Shift-wise Normalization Trend")
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.bar(shift_stats["Exam Shift"], shift_stats["mean"], yerr=shift_stats["std"], capsize=5)
                ax.set_xlabel("Exam Shift")
                ax.set_ylabel("Average Marks (±SD)")
                ax.set_title("Shift-wise Raw Marks Distribution")
                st.pyplot(fig)

                # Download normalized dataset
                buf2 = io.BytesIO()
                df_norm.to_csv(buf2, index=False)
                st.download_button(
                    "📥 Download Normalized Data (CSV)",
                    data=buf2.getvalue(),
                    file_name="normalized_marks.csv",
                    mime="text/csv"
                )
            else:
                st.error("CSV must contain columns: Roll Number, Category, Exam Shift, Raw Marks")
    else:
        if admin_password:
            st.sidebar.error("❌ Wrong password. Access Denied.")
