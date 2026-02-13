import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v6.0", page_icon="🏥", layout="wide")

# --- Database Setup (Permanent Login) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('INSERT OR IGNORE INTO users VALUES ("admin", "password123")')
    conn.commit()
    conn.close()

def add_user(u, p):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users VALUES (?, ?)', (u, p))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_user(u, p):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (u, p))
    data = c.fetchone()
    conn.close()
    return data

init_db()

# --- Custom Styling (FIXED: Dark text for white boxes) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #1b5e20; color: white; font-weight: bold; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    /* This fixes the "Invisible Numbers" problem */
    [data-testid="stMetricValue"] { color: #1f1f1f !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #444444 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'health_data' not in st.session_state: st.session_state['health_data'] = []

# --- Business Logic ---
def calculate_metrics(w, h, a, g, activity):
    if g == "Male": bmr = 10 * w + 6.25 * (h*100) - 5 * a + 5
    else: bmr = 10 * w + 6.25 * (h*100) - 5 * a - 161
    multipliers = {"Sedentary (Little/No Exercise)": 1.2, "Lightly Active (1-3 days/week)": 1.375, "Moderately Active (3-5 days/week)": 1.55, "Very Active (6-7 days/week)": 1.725}
    tdee = bmr * multipliers[activity]
    return round(bmr, 2), round(tdee, 2), round(w * 1.6, 2)

# --- AUTHENTICATION ---
if not st.session_state['logged_in']:
    st.title("🏥 ProHealth Suite Access")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Log In"):
            if check_user(u, p):
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else: st.error("Incorrect credentials.")
    with tab2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            if new_u and new_p and add_user(new_u, new_p):
                st.success("Account created! Go to Login tab.")
            else: st.error("User already exists or field empty.")

# --- MAIN APP ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}")
    
    # Persistent Inputs
    w = st.sidebar.number_input("Weight (kg)", 10.0, 250.0, 70.0)
    h = st.sidebar.number_input("Height (m)", 0.5, 2.5, 1.70)
    age = st.sidebar.number_input("Age", 5, 110, 25)
    gender = st.sidebar.radio("Gender", ["Male", "Female"])
    activity = st.sidebar.selectbox("Activity Level", ["Sedentary (Little/No Exercise)", "Lightly Active (1-3 days/week)", "Moderately Active (3-5 days/week)", "Very Active (6-7 days/week)"])
    prot_in = st.sidebar.number_input("Daily Protein Intake (g)", 0, 300, 50)
    diseases = st.sidebar.multiselect("Medical Conditions", ["None", "Diabetes", "Hypertension", "Thyroid"])

    # Shared Calculations
    bmi = round(w / (h**2), 2)
    bmr, tdee, prot_target = calculate_metrics(w, h, age, gender, activity)
    status = "Underweight" if bmi < 18.5 else "Normal" if bmi < 24.9 else "Overweight"

    page = st.sidebar.selectbox("Navigate:", ["Analysis Dashboard", "Targets & Nutrition", "Health Suggestions", "History & Export", "Logout"])

    if page == "Analysis Dashboard":
        st.title("📊 Physical Analysis")
        col1, col2 = st.columns(2)
        col1.metric("Body Mass Index (BMI)", f"{bmi}", status)
        col2.metric("Basal Metabolic Rate (BMR)", f"{bmr} kcal")
        
        if st.button("💾 Archive This Assessment"):
            st.session_state['health_data'].append({"Date": datetime.date.today().strftime("%Y-%m-%d"), "Weight": w, "BMI": bmi, "TDEE": tdee, "Conditions": ", ".join(diseases)})
            st.success("Saved to memory!")

    elif page == "Targets & Nutrition":
        st.title("🎯 Health Targets")
        c1, c2, c3 = st.columns(3)
        c1.metric("Daily Calories", f"{tdee} kcal")
        c2.metric("Protein Target", f"{prot_target}g")
        c3.metric("Hydration", f"{round(w*0.035, 2)}L")
        st.info(f"Targets adjusted for: {activity}")

    elif page == "Health Suggestions":
        st.title("💡 Personal Suggestions")
        # Logic to avoid the raw code error from your screenshot
        if status == "Overweight": st.warning("Weight Management: Aim for a 500kcal deficit and high fiber.")
        if prot_in < prot_target: st.warning(f"Protein Gap: You are {round(prot_target - prot_in, 1)}g short of your goal.")
        if "Diabetes" in diseases: st.error("Medical: Limit simple sugars and monitor glycemic load.")
        if status == "Normal" and not diseases: st.success("Everything looks great! Maintain your current routine.")

    elif page == "History & Export":
        st.title("📈 History & PDF")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.dataframe(df)
            if st.button("Generate Report"):
                pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "PROHEALTH REPORT", ln=True, align='C')
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("Download PDF", pdf_output, "Report.pdf")
        else: st.warning("No data archived yet.")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()
