import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3  # New: For permanent storage

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v6.0", page_icon="🏥", layout="wide")

# --- Database Setup (Permanent Storage) ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    # Add default admin if not exists
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

# Initialize the database on startup
init_db()

# --- Custom Styling ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #1b5e20; color: white; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricValue"] { color: #31333F !important; }
    [data-testid="stMetricLabel"] { color: #555555 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'health_data' not in st.session_state: st.session_state['health_data'] = []

# --- Logic Functions ---
def calculate_metrics(w, h, a, g, activity):
    if g == "Male": bmr = 10 * w + 6.25 * (h*100) - 5 * a + 5
    else: bmr = 10 * w + 6.25 * (h*100) - 5 * a - 161
    multipliers = {
        "Sedentary (Little/No Exercise)": 1.2,
        "Lightly Active (1-3 days/week)": 1.375,
        "Moderately Active (3-5 days/week)": 1.55,
        "Very Active (6-7 days/week)": 1.725
    }
    tdee = bmr * multipliers[activity]
    prot_target = w * 1.6
    return round(bmr, 2), round(tdee, 2), round(prot_target, 2)

def get_suggestions(bmi_status, prot_diff, diseases):
    tips = []
    if bmi_status == "Overweight": tips.append("Focus on a 500kcal deficit and increase fiber intake.")
    if prot_diff < 0: tips.append(f"Short by {abs(round(prot_diff, 1))}g of protein. Add Greek yogurt or eggs.")
    if "Diabetes" in diseases: tips.append("⚠️ Limit simple sugars; focus on high-fiber carbs.")
    if "Hypertension" in diseases: tips.append("⚠️ Reduce sodium (salt) intake.")
    if not tips: tips.append("Metrics look balanced! Maintain current routine.")
    return tips

# --- AUTHENTICATION GATE ---
if not st.session_state['logged_in']:
    st.title("🏥 ProHealth Suite Access")
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register New Account"])
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Log In"):
            if check_user(u, p):
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else: st.error("Invalid username or password.")
    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if new_u and new_p:
                if add_user(new_u, new_p):
                    st.success("Registration successful! You can now Login.")
                else: st.error("Username already exists!")

# --- MAIN APPLICATION ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}!")
    st.sidebar.subheader("📋 Your Vitals")
    w = st.sidebar.number_input("Weight (kg)", 10.0, 250.0, 70.0)
    h = st.sidebar.number_input("Height (m)", 0.5, 2.5, 1.70)
    age = st.sidebar.number_input("Age", 5, 110, 25)
    gender = st.sidebar.radio("Gender", ["Male", "Female"])
    activity = st.sidebar.selectbox("Activity Level", ["Sedentary (Little/No Exercise)", "Lightly Active (1-3 days/week)", "Moderately Active (3-5 days/week)", "Very Active (6-7 days/week)"])
    prot_in = st.sidebar.number_input("Daily Protein Intake (g)", 0, 300, 50)
    diseases = st.sidebar.multiselect("Medical Conditions", ["None", "Diabetes", "Hypertension", "Thyroid", "Kidney Disease"])

    bmi = round(w / (h**2), 2)
    bmr, tdee, prot_target = calculate_metrics(w, h, age, gender, activity)
    prot_diff = prot_in - prot_target
    status = "Underweight" if bmi < 18.5 else "Normal" if bmi < 24.9 else "Overweight"

    st.sidebar.divider()
    page = st.sidebar.selectbox("Go To Page:", ["1. Analysis Dashboard", "2. Target & Nutrition", "3. Health Suggestions", "4. History & Analytics", "5. Export Report", "Logout"])

    if page == "1. Analysis Dashboard":
        st.title("📊 Physical Analysis")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("BMI Status", f"{bmi}", status)
        with c2:
            st.metric("Basal Metabolic Rate (BMR)", f"{bmr} kcal")
        
        if st.button("💾 Save to History"):
            st.session_state['health_data'].append({
                "Date": datetime.date.today().strftime("%Y-%m-%d"),
                "Weight": w, "BMI": bmi, "TDEE": tdee, "Conditions": ", ".join(diseases)
            })
            st.success("Assessment Saved!")

    elif page == "2. Target & Nutrition":
        st.title("🎯 Daily Health Targets")
        c1, c2, c3 = st.columns(3)
        c1.metric("Calories (TDEE)", f"{tdee} kcal")
        c2.metric("Protein Goal", f"{prot_target}g")
        c3.metric("Water Goal", f"{round(w*0.035, 2)}L")
        st.info(f"Lifestyle: {activity}")

    elif page == "3. Health Suggestions":
        st.title("💡 Personal Suggestions")
        for s in get_suggestions(status, prot_diff, diseases):
            st.warning(s) if "⚠️" in s else st.success(s)

    elif page == "4. History & Analytics":
        st.title("📈 History Log")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.dataframe(df, use_container_width=True)
        else: st.warning("No saved data.")

    elif page == "5. Export Report":
        st.title("📄 Export PDF")
        if st.session_state['health_data']:
            data = st.session_state['health_data'][-1]
            if st.button("Download Final Report"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, f"Health Summary for {st.session_state['current_user']}", ln=True, align='C')
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("Download", pdf_output, "Report.pdf")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()
