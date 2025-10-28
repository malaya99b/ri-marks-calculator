import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import io

# ---------------------------- CONFIG ----------------------------
st.set_page_config(page_title="RI Marks & Rank Calculator", page_icon="📘", layout="centered")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)
st.title("📘 RI Marks & Rank Calculator")

st.markdown("""
> 🔒 **Privacy Notice:**  
> Your uploaded data is processed **entirely on your device**.  
> No files or marks are stored, logged, or shared.
""")

# ---------------------------- INPUT ----------------------------
st.header("🧾 Student Details")
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name")
    roll = st.text_input("Roll Number")
    gender = st.selectbox("Gender", ["Select", "Male", "Female"])
with col2:
    category = st.selectbox("Category", ["Select", "UR", "SEBC", "SC", "ST"])
    shift = st.selectbox("Exam Shift", ["Select", "1", "2", "3"])

uploaded_file = st.file_uploader("📤 Upload Response Sheet (CSV)", type=["csv"])

# ---------------------------- FUNCTIONS ----------------------------
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


def percentile_rank(series, value):
    return round((sum(series <= value) / len(series)) * 100, 2)


def generate_pdf(user_data, cat_avg, shift_avg):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RI Marks & Rank Scorecard", ln=True, align="C")
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Name: {user_data['Name']} (Roll: {user_data['Roll']})", ln=True)
    pdf.cell(0, 10, f"Category: {user_data['Category']} | Shift: {user_data['Shift']}", ln=True)
    pdf.cell(0, 10, f"Gender: {user_data['Gender']}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, "Section-wise Marks:", ln=True)
    for s in ["Mathematics", "General Awareness", "English", "Odia", "Reasoning"]:
        pdf.cell(0, 10, f" - {s}: {user_data[s]}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, f"Total Marks: {user_data['Total']}", ln=True)
    pdf.cell(0, 10, f"Normalized Marks: {round(user_data['Normalized'], 2)}", ln=True)
    pdf.cell(0, 10, f"Overall Rank: {user_data['Overall_Rank']}", ln=True)
    pdf.cell(0, 10, f"Category Rank: {user_data['Cat_Rank']}", ln=True)
    pdf.cell(0, 10, f"Shift Rank: {user_data['Shift_Rank']}", ln=True)
    pdf.cell(0, 10, f"Overall Percentile: {user_data['Overall_Percentile']}%", ln=True)
    pdf.cell(0, 10, f"Category Percentile: {user_data['Cat_Percentile']}%", ln=True)
    pdf.cell(0, 10, f"Shift Percentile: {user_data['Shift_Percentile']}%", ln=True)
    pdf.cell(0, 10, f"Average Marks: {round(user_data['Avg_Marks'],2)}", ln=True)
    pdf.cell(0, 10, f"Average Category Marks: {round(cat_avg[user_data['Category']],2)}", ln=True)
    pdf.cell(0, 10, f"Average Shift Marks: {round(shift_avg[user_data['Shift']],2)}", ln=True)
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output


# ---------------------------- MAIN PROCESS ----------------------------
if uploaded_file and st.button("🔍 Calculate Marks & Rank"):
    df = pd.read_csv(uploaded_file)
    required = ["Roll", "Name", "Category", "Shift", "Mathematics", "General Awareness", "English", "Odia", "Reasoning"]
    if not all(c in df.columns for c in required):
        st.error("❌ CSV must have columns: Roll, Name, Category, Shift, Mathematics, General Awareness, English, Odia, Reasoning")
        st.stop()

    df["Total"] = df[["Mathematics", "General Awareness", "English", "Odia", "Reasoning"]].sum(axis=1)
    df, shift_means, shift_sds = normalize_marks(df)

    # Ranks and Percentiles
    df["Overall_Rank"] = df["Normalized"].rank(ascending=False, method="min").astype(int)
    df["Cat_Rank"] = df.groupby("Category")["Normalized"].rank(ascending=False, method="min").astype(int)
    df["Shift_Rank"] = df.groupby("Shift")["Normalized"].rank(ascending=False, method="min").astype(int)

    df["Overall_Percentile"] = df["Normalized"].rank(pct=True) * 100
    df["Cat_Percentile"] = df.groupby("Category")["Normalized"].rank(pct=True) * 100
    df["Shift_Percentile"] = df.groupby("Shift")["Normalized"].rank(pct=True) * 100

    avg_marks = df["Total"].mean()
    cat_avg = df.groupby("Category")["Total"].mean().to_dict()
    shift_avg = df.groupby("Shift")["Total"].mean().to_dict()

    user = df[df["Roll"].astype(str) == roll]
    if user.empty:
        st.error("❌ Roll number not found in uploaded data.")
        st.stop()

    user_data = user.iloc[0]
    user_data["Gender"] = gender
    user_data["Avg_Marks"] = avg_marks

    st.success(f"✅ Result for **{user_data['Name']} ({user_data['Roll']})**")

    sec_order = ["Mathematics", "General Awareness", "English", "Odia", "Reasoning"]
    st.subheader("📊 Section-wise Marks")
    st.table(pd.DataFrame({"Section": sec_order, "Marks": [user_data[s] for s in sec_order]}))

    st.subheader("🏁 Summary")
    st.write(f"""
    - **Total Marks:** {user_data['Total']}
    - **Normalized Marks:** {round(user_data['Normalized'], 2)}
    - **Overall Rank:** {user_data['Overall_Rank']}
    - **Category Rank ({user_data['Category']}):** {user_data['Cat_Rank']}
    - **Shift Rank ({user_data['Shift']}):** {user_data['Shift_Rank']}
    - **Overall Percentile:** {round(user_data['Overall_Percentile'], 2)}%
    - **Category Percentile:** {round(user_data['Cat_Percentile'], 2)}%
    - **Shift Percentile:** {round(user_data['Shift_Percentile'], 2)}%
    - **Average Marks (All):** {round(avg_marks,2)}
    - **Average Category Marks:** {round(cat_avg[user_data['Category']],2)}
    - **Average Shift Marks:** {round(shift_avg[user_data['Shift']],2)}
    """)

    pdf_output = generate_pdf(user_data, cat_avg, shift_avg)
    st.download_button("📄 Download My Scorecard (PDF)",
                       data=pdf_output,
                       file_name=f"RI_Scorecard_{user_data['Roll']}.pdf",
                       mime="application/pdf")
