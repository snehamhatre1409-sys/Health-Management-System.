import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v5.0", page_icon="⚖️", layout="wide")

# --- Custom Styling (Fixed Bug) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .main { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_db' not in st.session_state: st.session_state['user_db'] = {"admin": "password123"}
if 'health_data' not in st.session_state: st.session_state['health_data'] = []

# --- Logic Functions ---
def calculate_bmr(w, h, a, g):
    if g == "Male": return round(10 * w + 6.25 * (h*100) - 5 * a + 5, 2)
    else: return round(10 * w + 6.25 * (h*100) - 5 * a - 161, 2)

# --- AUTHENTICATION GATE ---
if not st.session_state['logged_in']:
    st.title("🏥 ProHealth Suite Access")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register New Account"])
    
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Log In"):
            if u in st.session_state['user_db'] and st.session_state['user_db'][u] == p:
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else: st.error("Incorrect username or password.")
            
    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if new_u and new_p:
                st.session_state['user_db'][new_u] = new_p
                st.success("Registration successful! Switch to Login tab.")
            else: st.warning("Please fill in all fields.")

# --- MAIN APPLICATION ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}!")
    page = st.sidebar.selectbox("Go To:", ["Dashboard", "Analytics & History", "Export Report", "Logout"])

    if page == "Dashboard":
        st.title("📊 Personal Health Dashboard")
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Enter Metrics")
            w = st.number_input("Weight (kg)", 10.0, 250.0, 70.0)
            h = st.number_input("Height (m)", 0.5, 2.5, 1.70)
            age = st.number_input("Age", 5, 110, 25)
            gender = st.radio("Gender", ["Male", "Female"])
        
        with c2:
            st.subheader("Your Health Analysis")
            bmi = round(w / (h**2), 2)
            bmr = calculate_bmr(w, h, age, gender)
            water = round(w * 0.035, 2) # Hydration rule: ~35ml per kg
            
            if bmi < 18.5: status, col = "Underweight", "blue"
            elif 18.5 <= bmi < 24.9: status, col = "Normal", "green"
            else: status, col = "Overweight", "red"
            
            st.metric("Body Mass Index (BMI)", f"{bmi}", f"{status}", delta_color="normal" if status=="Normal" else "inverse")
            st.metric("Basal Metabolic Rate (BMR)", f"{bmr} kcal/day")
            st.info(f"💧 Daily Hydration Target: **{water} Liters**")
            
        if st.button("💾 Save to Records"):
            st.session_state['health_data'].append({
                "Date": datetime.date.today().strftime("%Y-%m-%d"),
                "Weight": w, "BMI": bmi, "BMR": bmr, "Status": status
            })
            st.success("Record saved successfully!")

    elif page == "Analytics & History":
        st.title("📈 Health Trends")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.line_chart(df.set_index("Date")["Weight"])
            st.write("### Detailed History Log")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No records found. Please save data in the Dashboard.")

    elif page == "Export Report":
        st.title("📄 Generate Medical PDF")
        if st.session_state['health_data']:
            data = st.session_state['health_data'][-1]
            if st.button("Generate Professional Report"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 20)
                pdf.cell(200, 15, "PROHEALTH MEDICAL SUMMARY", ln=True, align='C')
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(200, 10, f"User: {st.session_state['current_user']}", ln=True)
                pdf.cell(200, 10, f"Date: {data['Date']}", ln=True)
                pdf.line(10, 50, 200, 50)
                pdf.ln(10)
                pdf.cell(100, 10, f"Weight: {data['Weight']} kg")
                pdf.cell(100, 10, f"BMI: {data['BMI']} ({data['Status']})", ln=True)
                pdf.cell(100, 10, f"Daily Calories (BMR): {data['BMR']} kcal", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("📩 Download PDF", pdf_output, "ProHealth_Report.pdf", "application/pdf")
        else:
            st.error("Nothing to export yet!")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()
