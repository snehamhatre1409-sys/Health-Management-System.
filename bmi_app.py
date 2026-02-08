import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import time

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v5.0", page_icon="⚖️", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white; }
    </style>
    """, unsafe_allow_id=True)

# --- Session State Initialization ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_db' not in st.session_state: st.session_state['user_db'] = {"admin": "password123"}
if 'health_data' not in st.session_state: st.session_state['health_data'] = []

# --- Helper Functions ---
def calculate_bmr(w, h, a, g):
    # Mifflin-St Jeor Equation
    if g == "Male": return 10 * w + 6.25 * (h*100) - 5 * a + 5
    else: return 10 * w + 6.25 * (h*100) - 5 * a - 161

# --- AUTHENTICATION UI ---
if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.title("Welcome Back")
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Login"):
            if u in st.session_state['user_db'] and st.session_state['user_db'][u] == p:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.success("Access Granted!")
                st.rerun()
            else: st.error("Invalid credentials")
            
    with tab2:
        st.title("Create Account")
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            if new_u and new_p:
                st.session_state['user_db'][new_u] = new_p
                st.success("Account created! Please login.")
            else: st.warning("Fields cannot be empty")

# --- MAIN APPLICATION UI ---
else:
    st.sidebar.title(f"👤 {st.session_state['current_user']}")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Analytics", "Report Export", "Logout"])

    if page == "Dashboard":
        st.title("🏥 Health Dashboard")
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Physical Metrics")
            w = st.number_input("Weight (kg)", 1.0, 300.0, 70.0)
            h = st.number_input("Height (m)", 0.5, 2.5, 1.75)
            age = st.number_input("Age", 1, 120, 25)
            gender = st.selectbox("Gender", ["Male", "Female"])

        with col2:
            st.subheader("Results")
            bmi = round(w / (h**2), 2)
            bmr = calculate_bmr(w, h, age, gender)
            water = round(w * 0.033, 2)
            
            st.metric("BMI Index", bmi)
            st.metric("Daily Calorie Needs (BMR)", f"{bmr} kcal")
            st.info(f"💧 Recommended Daily Water: {water} Liters")

        if st.button("💾 Save to History"):
            entry = {"Date": datetime.date.today(), "Weight": w, "BMI": bmi, "BMR": bmr}
            st.session_state['health_data'].append(entry)
            st.toast("Progress Saved!")

    elif page == "Analytics":
        st.title("📉 Progress Tracking")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.subheader("BMI Trend Over Time")
            st.line_chart(df.set_index("Date")["BMI"])
            st.subheader("Log History")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data yet. Save metrics in the Dashboard.")

    elif page == "Report Export":
        st.title("📄 Medical Report Generator")
        if st.session_state['health_data']:
            latest = st.session_state['health_data'][-1]
            st.write("Generating report for your latest entry...")
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_fill_color(240, 240, 240)
            pdf.rect(0, 0, 210, 297, 'F')
            
            pdf.set_font("Arial", 'B', 24)
            pdf.set_text_color(46, 125, 50)
            pdf.cell(200, 20, "PROHEALTH MEDICAL REPORT", ln=True, align='C')
            
            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(10)
            pdf.cell(200, 10, f"Patient Name: {st.session_state['current_user']}", ln=True)
            pdf.cell(200, 10, f"Date: {latest['Date']}", ln=True)
            pdf.line(10, 55, 200, 55)
            
            pdf.ln(10)
            pdf.cell(100, 10, f"Body Mass Index (BMI): {latest['BMI']}", ln=True)
            pdf.cell(100, 10, f"Basal Metabolic Rate: {latest['BMR']} kcal", ln=True)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📩 Download PDF Report", pdf_bytes, "ProHealth_Report.pdf", "application/pdf")
        else:
            st.error("Please record some data first!")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()
