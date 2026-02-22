import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px
from datetime import timedelta

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v7.0 - Professional", page_icon="🏥", layout="wide")

# --- Custom Light Theme CSS ---
st.markdown("""
<style>
body {
    font-family: 'Poppins', sans-serif;
    background-color: #F9F9F9;
}
h1 {
    font-weight: 700;
}
.stButton>button {
    background-color: #1976D2;
    color: white;
    padding: 12px;
    border-radius: 8px;
    font-weight: bold;
}
.stProgress > div > div > div > div {
    background: #1976D2;
}
</style>
""", unsafe_allow_html=True)

# --- Enhanced Database Setup ---
def init_db():
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, created_date TEXT)''')
    c.execute('INSERT OR IGNORE INTO users VALUES ("admin", "password123", "admin@prohealth.com", ?)',
              (datetime.datetime.now().isoformat(),))
    # Health records
    c.execute('''CREATE TABLE IF NOT EXISTS health_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT, date TEXT, weight REAL, height REAL, age INTEGER,
                  gender TEXT, activity TEXT, protein_intake REAL,
                  sleep_hours REAL, water_intake REAL, steps INTEGER,
                  hygiene_score INTEGER, conditions TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- Helpers ---
def add_user(u, p, e):
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, email, created_date) VALUES (?, ?, ?, ?)',
                  (u, p, e, datetime.datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

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

def calculate_advanced_metrics(w, h, a, g, activity, sleep, steps):
    bmi = w / (h**2)
    if g == "Male":
        bmr = 88.362 + (13.397 * w) + (4.799 * h * 100) - (5.677 * a)
    else:
        bmr = 447.593 + (9.247 * w) + (3.098 * h * 100) - (4.330 * a)
    multipliers = {"Sedentary":1.2, "Lightly Active":1.375, "Moderately Active":1.55, "Very Active":1.725}
    tdee = bmr * multipliers[activity]
    ideal_weight = 22.5 * (h**2)
    body_fat = 1.20*bmi + 0.23*a - (16.2 if g=="Male" else 5.4)
    recovery_score = (sleep*0.4 + steps/10000*0.3 + (w/ideal_weight)*0.3)
    return {
        'bmi': round(bmi, 1),
        'bmr': round(bmr, 0),
        'tdee': round(tdee, 0),
        'ideal_weight': round(ideal_weight, 1),
        'body_fat': round(body_fat, 1),
        'recovery_score': min(100, round(recovery_score*100, 0))
    }

# --- Session Init ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None
if 'health_data' not in st.session_state: st.session_state['health_data'] = pd.DataFrame()

# --- Header ---
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 15px">
    <img src="YOUR_LOGO_URL_HERE" width="58" />
    <h1 style="margin:0; color: #1976D2;">ProHealth Suite v7.0</h1>
</div>
""", unsafe_allow_html=True)

# --- Authentication ---
if not st.session_state['logged_in']:
    st.markdown("## 🔐 Login or Register")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = username
                st.session_state['health_data'] = get_user_records(username)
                st.experimental_rerun()
            else:
                st.error("Invalid credentials!")

    with tab2:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        new_email = st.text_input("Email (optional)")
        if st.button("Create Account"):
            if add_user(new_username, new_password, new_email or ""):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists!")

else:
    st.sidebar.header(f"👋 Hello, {st.session_state['current_user']}")
    st.sidebar.markdown("---")

    # Sidebar Inputs
    with st.sidebar.expander("📊 Personal Profile"):
        weight = st.number_input("Weight (kg)", 30.0, 200.0, 70.0)
        height = st.number_input("Height (m)", 1.0, 2.2, 1.70)
        age = st.number_input("Age", 12, 100, 25)
        gender = st.radio("Gender", ["Male","Female"])

    with st.sidebar.expander("🏃 Activity & Lifestyle"):
        activity = st.selectbox("Activity Level",
                                ["Sedentary","Lightly Active","Moderately Active","Very Active"])
        sleep_hours = st.slider("Sleep (hrs)", 0.0, 12.0, 7.0)
        daily_steps = st.number_input("Steps Today", 0, 30000, 8000)
        water_intake = st.number_input("Water (L)", 0.0, 10.0, 2.5)
        protein_intake = st.number_input("Protein (g)", 0, 300, 100)

    with st.sidebar.expander("🦠 Hygiene"):
        teeth_brushed = st.checkbox("Teeth Brushed")
        shower_today = st.checkbox("Shower")
        hands_washed = st.number_input("Hand Washes", 0, 50, 10)
        room_clean = st.checkbox("Room Clean")
        hygiene_score = (teeth_brushed*25 + shower_today*25 + min(hands_washed/2,25) + room_clean*25)

    metrics = calculate_advanced_metrics(weight, height, age, gender,
                                         activity, sleep_hours, daily_steps)

    page = st.sidebar.radio("Navigate", [
        "Dashboard","Goals","Progress","Insights","Hygiene","Records","AI Assistant","Logout"
    ])

    st.markdown(f"## {page}")

    # --- Pages ---
    if page == "Dashboard":
        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("BMI", metrics['bmi'])
        col2.metric("BMR (kcal)", metrics['bmr'], f"{metrics['tdee']} TDEE")
        col3.metric("Recovery", f"{metrics['recovery_score']}%")
        col4.metric("Hygiene Score", f"{hygiene_score}%")

        if st.button("Save Assessment"):
            record = {
                'date': datetime.date.today().strftime("%Y-%m-%d"),
                'weight': weight, 'height': height, 'age': age, 'gender': gender,
                'activity': activity, 'protein_intake': protein_intake,
                'sleep_hours': sleep_hours, 'water_intake': water_intake,
                'steps': daily_steps, 'hygiene_score': hygiene_score,
                'conditions': ""
            }
            save_health_record(st.session_state['current_user'], record)
            st.success("Saved!")
            st.session_state['health_data'] = get_user_records(st.session_state['current_user'])

    elif page == "Progress":
        df = st.session_state['health_data']
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            fig = px.line(df, x='date', y='weight', title="Weight Progress")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No records yet.")

    elif page == "Records":
        if not st.session_state['health_data'].empty:
            st.dataframe(st.session_state['health_data'])
        else:
            st.info("No records yet.")

    elif page == "Logout":
        st.session_state.clear()
        st.experimental_rerun()
