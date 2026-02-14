import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v7.0", page_icon="🏥", layout="wide")

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, created_date TEXT)''')
    c.execute('INSERT OR IGNORE INTO users VALUES ("admin", "password123", "admin@prohealth.com", ?)', 
              (datetime.datetime.now().isoformat(),))
    
    c.execute('''CREATE TABLE IF NOT EXISTS health_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, date TEXT, weight REAL, height REAL, age INTEGER, 
                  gender TEXT, activity TEXT, protein_intake REAL, 
                  sleep_hours REAL, water_intake REAL, steps INTEGER,
                  hygiene_score INTEGER, conditions TEXT)''')
    conn.commit()
    conn.close()

def add_user(u, p, e):
    try:
        conn = sqlite3.connect('prohealth.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password, email, created_date) VALUES (?, ?, ?, ?)',
                  (u, p, e, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def check_user(u, p):
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (u, p))
    data = c.fetchone()
    conn.close()
    return data

def save_health_record(username, data):
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    c.execute('''INSERT INTO health_records 
                 (username, date, weight, height, age, gender, activity, protein_intake,
                  sleep_hours, water_intake, steps, hygiene_score, conditions)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (username, data['date'], data['weight'], data['height'], data['age'],
               data['gender'], data['activity'], data['protein_intake'], data['sleep_hours'],
               data['water_intake'], data['steps'], data['hygiene_score'], data['conditions']))
    conn.commit()
    conn.close()

def get_user_records(username):
    conn = sqlite3.connect('prohealth.db')
    df = pd.read_sql_query("SELECT * FROM health_records WHERE username=?", conn, params=(username,))
    conn.close()
    return df

init_db()

# --- Custom Styling ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; 
                       background: linear-gradient(45deg, #1b5e20, #2e7d32); 
                       color: white; font-weight: bold; }
    .main-header { font-size: 2.5em; color: #1b5e20; text-align: center; margin-bottom: 0.5em; }
    </style>
    """, unsafe_allow_html=True)

# --- Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None

# --- Advanced Metrics Calculation ---
def calculate_advanced_metrics(w, h, a, g, activity, sleep, steps):
    bmi = w / (h**2)
    # BMR (Harris-Benedict)
    if g == "Male": 
        bmr = 88.362 + (13.397 * w) + (4.799 * h * 100) - (5.677 * a)
    else: 
        bmr = 447.593 + (9.247 * w) + (3.098 * h * 100) - (4.330 * a)
    
    multipliers = {"Sedentary": 1.2, "Lightly Active": 1.375, "Moderately Active": 1.55, "Very Active": 1.725}
    tdee = bmr * multipliers[activity]
    
    ideal_weight = 22.5 * (h**2)
    recovery_score = (sleep * 0.4 + (steps/10000) * 0.3 + (1 - abs(w-ideal_weight)/ideal_weight)*0.3)
    
    return {
        'bmi': round(bmi, 1), 'bmr': round(bmr, 0), 'tdee': round(tdee, 0),
        'ideal_weight': round(ideal_weight, 1),
        'recovery_score': max(0, min(100, round(recovery_score * 100, 0)))
    }

# --- Login Logic ---
if not st.session_state['logged_in']:
    st.markdown('<h1 class="main-header">🏥 ProHealth Suite v7.0</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_user(u, p):
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        new_e = st.text_input("Email")
        if st.button("Register"):
            if add_user(new_u, new_p, new_e):
                st.success("Account created!")
            else:
                st.error("Username exists")

# --- Main App ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}")
    
    # Sidebar Inputs
    weight = st.sidebar.number_input("Weight (kg)", 30.0, 200.0, 70.0)
    height = st.sidebar.number_input("Height (m)", 1.0, 2.5, 1.75)
    age = st.sidebar.number_input("Age", 1, 120, 25)
    gender = st.sidebar.radio("Gender", ["Male", "Female"])
    activity = st.sidebar.selectbox("Activity", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
    sleep_hours = st.sidebar.slider("Sleep", 0.0, 12.0, 8.0)
    daily_steps = st.sidebar.number_input("Steps", 0, 50000, 5000)
    water_intake = st.sidebar.number_input("Water (L)", 0.0, 10.0, 2.0)
    protein_intake = st.sidebar.number_input("Protein (g)", 0, 300, 80)
    
    # Hygiene
    st.sidebar.subheader("Hygiene")
    h1 = st.sidebar.checkbox("Brushed Teeth")
    h2 = st.sidebar.checkbox("Showered")
    h3 = st.sidebar.checkbox("Room Clean")
    hygiene_score = (h1*33 + h2*33 + h3*34)

    conditions = st.sidebar.multiselect("Conditions", ["None", "Diabetes", "Hypertension", "Asthma"])
    
    metrics = calculate_advanced_metrics(weight, height, age, gender, activity, sleep_hours, daily_steps)

    page = st.sidebar.selectbox("Navigate", ["Dashboard", "Insights", "Progress", "Reports", "Logout"])

    if page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown(f'<h2 class="main-header">{page}</h2>', unsafe_allow_html=True)

    if page == "Dashboard":
        col1, col2, col3 = st.columns(3)
        col1.metric("BMI", metrics['bmi'])
        col2.metric("TDEE (Calories)", f"{metrics['tdee']} kcal")
        col3.metric("Hygiene", f"{hygiene_score}%")
        
        st.progress(metrics['recovery_score']/100)
        st.write(f"Recovery Score: {metrics['recovery_score']}%")

        if st.button("Save Daily Record"):
            record = {
                'date': datetime.date.today().isoformat(),
                'weight': weight, 'height': height, 'age': age, 'gender': gender,
                'activity': activity, 'protein_intake': protein_intake,
                'sleep_hours': sleep_hours, 'water_intake': water_intake,
                'steps': daily_steps, 'hygiene_score': hygiene_score,
                'conditions': ", ".join(conditions)
            }
            save_health_record(st.session_state['current_user'], record)
            st.success("Record saved!")

    elif page == "Insights":
        

[Image of body mass index scale]

        if metrics['bmi'] > 25:
            st.warning("Your BMI is high. Focus on a calorie deficit and consistent movement.")
        elif metrics['bmi'] < 18.5:
            st.info("Your BMI is low. Ensure you are getting enough protein and healthy fats.")
        else:
            st.success("You are in a healthy weight range!")

    elif page == "Progress":
        df = get_user_records(st.session_state['current_user'])
        if not df.empty:
            fig = px.line(df, x='date', y='weight', title="Weight Trend")
            st.plotly_chart(fig)
            st.dataframe(df)
        else:
            st.info("No records found. Save data in the Dashboard.")

    elif page == "Reports":
        df = get_user_records(st.session_state['current_user'])
        if not df.empty:
            if st.button("Generate PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Health Report for {st.session_state['current_user']}", ln=True, align='C')
                pdf.cell(200, 10, txt=f"Average Weight: {df['weight'].mean():.2f} kg", ln=True)
                
                # Output as bytes for Streamlit download
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button("Download Report", data=pdf_bytes, file_name="report.pdf")
        else:
            st.error("No data available to generate report.")
