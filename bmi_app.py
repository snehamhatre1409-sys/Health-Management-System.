import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# Page Config (Makes it look good on mobile)
st.set_page_config(page_title="ProHealth Web", page_icon="🏥")

st.title("🏥 ProHealth Management System")
st.write("Track your health metrics from any device.")

# Sidebar for Navigation
menu = ["Dashboard", "History"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Dashboard":
    st.subheader("Health Calculator")
    
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("Weight (kg)", min_value=1.0, value=70.0)
    with col2:
        height = st.number_input("Height (m)", min_value=0.5, value=1.7)
        
    if st.button("Calculate BMI"):
        bmi = round(weight / (height**2), 2)
        
        if bmi < 18.5: status, col = "Underweight", "blue"
        elif 18.5 <= bmi < 24.9: status, col = "Normal", "green"
        else: status, col = "Overweight", "red"
        
        st.success(f"Your BMI is {bmi}")
        st.markdown(f"Status: **:{col}[{status}]**")
        
        # Save Logic (Simulated for Web)
        new_data = {"Date": datetime.datetime.now().strftime("%Y-%m-%d"), "BMI": bmi, "Status": status}
        st.session_state['history'] = st.session_state.get('history', []) + [new_data]
        
        # PDF Generation
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="ProHealth Medical Report", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Date: {new_data['Date']}", ln=True)
        pdf.cell(200, 10, txt=f"BMI: {bmi} ({status})", ln=True)
        
        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Download PDF Report", data=pdf_output, file_name="Health_Report.pdf")

elif choice == "History":
    st.subheader("Your Records")
    if 'history' in st.session_state:
        df = pd.DataFrame(st.session_state['history'])
        st.table(df)
    else:
        st.info("No records found yet. Go to Dashboard!")
