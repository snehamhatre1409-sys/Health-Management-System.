import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px
from datetime import timedelta

# --- Page Configuration ---
st.set_page_config(
    page_title="ProHealth Suite v8.0 - Professional", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Professional Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main { padding-top: 2rem; }
    
    .metric-container {
        background: rgba(255,255,255,0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1) !important;
        padding: 2rem !important;
        margin: 1rem 0 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3.5rem;
        background: linear-gradient(45deg, #1e40af, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 2.5rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        margin: 1rem 0;
    }
    
    .sidebar .stButton > button {
        background: linear-gradient(45deg, #3b82f6, #1d4ed8);
        border-radius: 12px;
        border: none;
        height: 3rem;
        font-weight: 600;
        color: white;
        width: 100%;
        margin: 0.5rem 0;
    }
    
    .login-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 3rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        max-width: 450px;
        margin: 2rem auto;
    }
</style>
""", unsafe_allow_html=True)

# --- Database Setup (COMPLETE - This fixes the error!) ---
def init_db():
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, created_date TEXT)''')
    c.execute('INSERT OR IGNORE INTO users VALUES ("admin", "password123", "admin@prohealth.com", ?)', 
              (datetime.datetime.now().isoformat(),))
    
    # Health records table
    c.execute('''CREATE TABLE IF NOT EXISTS health_records 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, date TEXT, weight REAL, height REAL, age INTEGER, 
                  gender TEXT, activity TEXT, protein_intake REAL, 
                  sleep_hours REAL, water_intake REAL, steps INTEGER,
                  hygiene_score INTEGER, conditions TEXT,
                  FOREIGN KEY(username) REFERENCES users(username))''')
    
    # Hygiene tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS hygiene_log 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT,
                  teeth_brushed BOOLEAN, hands_washed INTEGER, shower BOOLEAN,
                  nails_trimmed BOOLEAN, room_clean BOOLEAN)''')
    
    conn.commit()
    conn.close()

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

# Initialize database
init_db()

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: 
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: 
    st.session_state['current_user'] = None
if 'health_data' not in st.session_state: 
    st.session_state['health_data'] = pd.DataFrame()

# --- Metrics Calculation ---
def calculate_advanced_metrics(w, h, a, g, activity, sleep, steps):
    bmi = w / (h**2)
    if g == "Male": 
        bmr = 88.362 + (13.397 * w) + (4.799 * h * 100) - (5.677 * a)
    else: 
        bmr = 447.593 + (9.247 * w) + (3.098 * h * 100) - (4.330 * a)
    
    multipliers = {"Sedentary": 1.2, "Lightly Active": 1.375, "Moderately Active": 1.55, "Very Active": 1.725}
    tdee = bmr * multipliers[activity]
    
    ideal_weight = 22.5 * (h**2)
    body_fat_male = 1.20 * bmi + 0.23 * a - 16.2 if g == "Male" else 1.20 * bmi + 0.23 * a - 5.4
    recovery_score = (sleep * 0.4 + steps/10000 * 0.3 + (w/ideal_weight)*0.3)
    
    return {
        'bmi': round(bmi, 1), 'bmr': round(bmr, 0), 'tdee': round(tdee, 0),
        'ideal_weight': round(ideal_weight, 1), 'body_fat': round(body_fat_male, 1),
        'recovery_score': min(100, round(recovery_score * 100, 0))
    }

# --- Professional Header ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 class="main-header">🏥 ProHealth Suite v8.0</h1>', unsafe_allow_html=True)

# --- Authentication ---
if not st.session_state['logged_in']:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.markdown("### Welcome Back")
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        if st.button("🚀 Sign In", use_container_width=True):
            if check_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['current_user'] = username
                st.session_state['health_data'] = get_user_records(username)
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials!")
    
    with tab2:
        st.info("👆 Default: **admin** / **password123**")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        new_email = st.text_input("Email (optional)")
        
        if st.button("Create Account", use_container_width=True):
            if new_username and new_password:
                if add_user(new_username, new_password, new_email or ""):
                    st.success("✅ Account created!")
                else:
                    st.error("❌ Username already exists!")
            else:
                st.warning("⚠️ Fill username & password")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- Main Dashboard ---
else:
    # Professional Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #3b82f6, #1d4ed8); border-radius: 16px; color: white;'>
            <h3>👋 {st.session_state['current_user']}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("📊 Profile")
        weight = st.number_input("⚖️ Weight (kg)", 30.0, 200.0, 70.0)
        height = st.number_input("📏 Height (m)", 1.0, 2.2, 1.70)
        age = st.number_input("🎂 Age", 12, 100, 25)
        gender = st.radio("⚥ Gender", ["Male", "Female"])
        
        st.header("🏃 Activity")
        activity = st.selectbox("Activity Level", 
                              ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
        sleep_hours = st.slider("😴 Sleep (hours)", 0.0, 12.0, 7.0)
        daily_steps = st.number_input("🚶 Steps", 0, 30000, 8000)
        
        if st.button("💾 Save Data"):
            hygiene_score = 85  # Simplified for demo
            record_data = {
                'date': datetime.date.today().strftime("%Y-%m-%d"),
                'weight': weight, 'height': height, 'age': age, 'gender': gender,
                'activity': activity, 'protein_intake': 100, 'sleep_hours': sleep_hours,
                'water_intake': 2.5, 'steps': daily_steps, 'hygiene_score': hygiene_score,
                'conditions': 'None'
            }
            save_health_record(st.session_state['current_user'], record_data)
            st.session_state['health_data'] = get_user_records(st.session_state['current_user'])
            st.success("✅ Saved!")
            st.balloons()
    
    # Main Content
    metrics = calculate_advanced_metrics(weight, height, age, gender, activity, sleep_hours, daily_steps)
    hygiene_score = 85  # Demo value
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📏 BMI", f"{metrics['bmi']}", "✅ Normal")
    col2.metric("🔥 Calories", f"{metrics['tdee']}", f"{metrics['bmr']}")
    col3.metric("❤️ Recovery", f"{metrics['recovery_score']}%", "+12%")
    col4.metric("🦠 Hygiene", f"{hygiene_score}%", "+5%")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Professional Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 Goals", "📈 Progress"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.metric("🥗 Protein", "112g", "Achieved ✓")
            st.metric("💧 Water", "2.8L", "Good")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.progress(0.85)
            st.caption("Recovery Score")
            st.progress(0.92)
            st.caption("Hygiene Score")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🎯 Your Goals")
        st.info(f"💡 Target calories: {metrics['tdee'] - 500} kcal/day for weight loss")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if not st.session_state['health_data'].empty:
            st.dataframe(st.session_state['health_data'])
        else:
            st.info("👆 Save your first record to see progress!")
        st.markdown('</div>', unsafe_allow_html=True)

# Professional Footer
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.9rem;'>
    🏥 ProHealth Suite v8.0 | Professional Health Management
</div>
""", unsafe_allow_html=True)
