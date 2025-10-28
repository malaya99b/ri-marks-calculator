import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="RI Exam Marks & Rank Calculator", page_icon="📊")

st.title("📊 RI Exam Marks & Rank Calculator")
st.write("""
Check your **marks** and **section-wise performance** for the RI Exam.  
Scoring: +1 for correct, -⅓ for wrong, 0 for unattempted.
""")

# ----- Generate Sample Data -----
st.subheader("Demo Mode (Sample Data)")

# Generate 100 random correct answers (A/B/C/D)
np.random.seed(42)
sample_key = pd.DataFrame({
    "QNo": np.arange(1, 101),
    "CorrectAnswer": np.random.choice(list("ABCD"), 100)
})
sample_response = pd.DataFrame({
    "QNo": np.arange(1, 101),
    "YourAnswer": np.random.choice(list("ABCD") + [np.nan], 100, p=[0.23,0.23,0.23,0.23,0.08])
})

st.success("✅ Sample Answer Key and Response Loaded!")

# ----- Merge & Evaluate -----
merged = pd.merge(sample_key, sample_response, on="QNo", how="left")

# Correct, wrong, unattempted
merged["Correct"] = merged["YourAnswer"] == merged["CorrectAnswer"]
merged["Wrong"] = (~merged["Correct"]) & merged["YourAnswer"].notna()
merged["Unattempted"] = merged["YourAnswer"].isna()

merged["Marks"] = merged["Correct"] * 1 + merged["Wrong"] * (-1/3)

# Total score
total_marks = merged["Marks"].sum()
correct_count = merged["Correct"].sum()
wrong_count = merged["Wrong"].sum()
unattempted_count = merged["Unattempted"].sum()

st.subheader("📋 Your Result Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("✅ Correct", int(correct_count))
col2.metric("❌ Wrong", int(wrong_count))
col3.metric("⭕ Unattempted", int(unattempted_count))
col4.metric("🏁 Total Marks", f"{total_marks:.2f}/100")

# ----- Section-wise -----
merged["Section"] = pd.cut(merged["QNo"],
    bins=[0,20,40,60,80,100],
    labels=["Mathematics","General Awareness","English","Odia","Reasoning"])

section_scores = merged.groupby("Section")["Marks"].sum().reset_index()
st.subheader("📚 Section-wise Scores")
st.dataframe(section_scores)

# ----- Simulated Rank (Random Peers) -----
st.subheader("🏆 Rank Estimation (Demo)")
num_students = 500
peer_scores = np.random.normal(loc=55, scale=15, size=num_students)
rank = 1 + np.sum(peer_scores > total_marks)
percentile = (1 - rank / num_students) * 100

st.write(f"**Estimated Rank:** {rank} out of {num_students}")
st.write(f"**Percentile:** {percentile:.2f}%")

st.info("In real mode, ranks would be computed from all uploaded responses.")
