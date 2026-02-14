import streamlit as st  # ✅ KEEP THIS
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px 
import plotly.graph_objects as go
from datetime import timedelta

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v7.0 - Advanced", page_icon="🏥", layout="wide")

# --- Enhanced Database Setup ---
def init_db():
    conn = sqlite3.connect('prohealth.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, created_date TEXT)''')
    c.execute('INSERT OR IGNORE INTO users VALUES ("admin", "password123", "admin@prohealth.com", ?)', 
              (datetime.datetime.now().isoformat(),))
    
    # Health records table (per user)
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

init_db()

# --- Enhanced Custom Styling ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; 
                       background: linear-gradient(45deg, #1b5e20, #2e7d32); 
                       color: white; font-weight: bold; font-size: 16px; }
    .main-header { font-size: 2.5em; color: #1b5e20; text-align: center; margin-bottom: 0.5em; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white; padding: 20px; border-radius: 15px; margin: 10px 0; }
    [data-testid="stMetricValue"] { color: white !important; font-size: 2em; }
    [data-testid="stMetricLabel"] { color: #f0f0f0 !important; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #4caf50, #8bc34a); }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None
if 'health_data' not in st.session_state: st.session_state['health_data'] = pd.DataFrame()

# --- Enhanced Metrics Calculation ---
def calculate_advanced_metrics(w, h, a, g, activity, sleep, steps):
    # BMI
    bmi = w / (h**2)
    
    # BMR (Harris-Benedict)
    if g == "Male": 
        bmr = 88.362 + (13.397 * w) + (4.799 * h * 100) - (5.677 * a)
    else: 
        bmr = 447.593 + (9.247 * w) + (3.098 * h * 100) - (4.330 * a)
    
    multipliers = {"Sedentary": 1.2, "Lightly Active": 1.375, "Moderately Active": 1.55, "Very Active": 1.725}
    tdee = bmr * multipliers[activity]
    
    # Advanced metrics
    ideal_weight = 22.5 * (h**2)
    body_fat_male = 1.20 * bmi + 0.23 * a - 16.2 if g == "Male" else 1.20 * bmi + 0.23 * a - 5.4
    recovery_score = (sleep * 0.4 + steps/10000 * 0.3 + (w/ideal_weight)*0.3)
    
    return {
        'bmi': round(bmi, 1), 'bmr': round(bmr, 0), 'tdee': round(tdee, 0),
        'ideal_weight': round(ideal_weight, 1), 'body_fat': round(body_fat_male, 1),
        'recovery_score': min(100, round(recovery_score * 100, 0))
    }

# --- Authentication ---
if not st.session_state['logged_in']:
    st.markdown('<h1 class="main-header">🏥 ProHealth Suite v7.0 - Advanced</h1>', unsafe_allow_html=True)
    st.markdown("**Your Complete Health & Hygiene Management System**")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        col1, col2 = st.columns([3,1])
        with col1:
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        with col2:
            st.empty()
            if st.button("🚀 Login", use_container_width=True):
                if check_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = username
                    st.session_state['health_data'] = get_user_records(username)
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")
    
    with tab2:
        st.info("👆 Default admin account: **admin** / **password123**")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        new_email = st.text_input("Email (optional)")
        
        if st.button("Create Account", use_container_width=True):
            if new_username and new_password:
                if add_user(new_username, new_password, new_email or ""):
                    st.success("✅ Account created! Please login.")
                else:
                    st.error("❌ Username already exists!")
            else:
                st.warning("⚠️ Please fill username and password.")

# --- Main Application ---
else:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👋 **Welcome, {st.session_state['current_user']}**")
    st.sidebar.markdown("---")
    
    # Enhanced Sidebar Inputs
    st.sidebar.header("📊 Personal Profile")
    weight = st.sidebar.number_input("⚖️ Weight (kg)", 30.0, 200.0, 70.0)
    height = st.sidebar.number_input("📏 Height (m)", 1.0, 2.2, 1.70)
    age = st.sidebar.number_input("🎂 Age", 12, 100, 25)
    gender = st.sidebar.radio("⚥ Gender", ["Male", "Female"])
    
    st.sidebar.header("🏃 Activity & Lifestyle")
    activity = st.sidebar.selectbox("Activity Level", 
                                   ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
    sleep_hours = st.sidebar.slider("😴 Sleep (hours)", 0.0, 12.0, 7.0)
    daily_steps = st.sidebar.number_input("🚶 Steps Today", 0, 30000, 8000)
    water_intake = st.sidebar.number_input("💧 Water (liters)", 0.0, 10.0, 2.5)
    protein_intake = st.sidebar.number_input("🍗 Protein (g)", 0, 300, 100)
    
    st.sidebar.header("🦠 Daily Hygiene")
    hygiene_items = st.sidebar.columns(2)
    teeth_brushed = hygiene_items[0].checkbox("🦷 Teeth Brushed")
    shower_today = hygiene_items[0].checkbox("🚿 Shower")
    hands_washed = hygiene_items[1].number_input("🧼 Hand Washes", 0, 50, 10)
    room_clean = hygiene_items[1].checkbox("🧹 Room Clean")
    
    hygiene_score = (teeth_brushed*25 + shower_today*25 + min(hands_washed/2, 25) + room_clean*25)
    
    conditions = st.sidebar.multiselect("🏥 Medical Conditions", 
                                       ["None", "Diabetes", "Hypertension", "Thyroid", "Asthma"])
    
    # Calculate metrics
    metrics = calculate_advanced_metrics(weight, height, age, gender, activity, sleep_hours, daily_steps)
    
    # Navigation
    page = st.sidebar.selectbox("📱 Navigate", 
                               ["📊 Health Dashboard", "🎯 Targets & Goals", "🩺 Health Insights", 
                                "📈 Progress Tracker", "🦠 Hygiene Monitor", "📋 Records & Reports", "🚪 Logout"])
    
    st.markdown(f'<h2 class="main-header">{{"📊 Health Dashboard" if page=="📊 Health Dashboard" else page}}</h2>', 
                unsafe_allow_html=True)
    
    if page == "📊 Health Dashboard":
        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📏 BMI", f"{metrics['bmi']}", "Normal" if 18.5 <= metrics['bmi'] <= 24.9 else "⚠️ Check")
        col2.metric("🔥 BMR", f"{metrics['bmr']} kcal", f"{metrics['tdee']} TDEE")
        col3.metric("❤️ Recovery", f"{metrics['recovery_score']}%", f"+{min(daily_steps/1000, 20)}%")
        col4.metric("🦠 Hygiene", f"{hygiene_score}%", "Great!")
        
        # Progress bars
        col1, col2 = st.columns(2)
        with col1:
            st.progress(metrics['recovery_score']/100)
            st.caption("Daily Recovery Score")
        with col2:
            st.progress(hygiene_score/100)
            st.caption("Hygiene Compliance")
        
        if st.button("💾 Save Current Assessment", use_container_width=True):
            record_data = {
                'date': datetime.date.today().strftime("%Y-%m-%d"),
                'weight': weight, 'height': height, 'age': age, 'gender': gender,
                'activity': activity, 'protein_intake': protein_intake,
                'sleep_hours': sleep_hours, 'water_intake': water_intake,
                'steps': daily_steps, 'hygiene_score': hygiene_score,
                'conditions': ', '.join(conditions)
            }
            save_health_record(st.session_state['current_user'], record_data)
            st.session_state['health_data'] = get_user_records(st.session_state['current_user'])
            st.success("✅ Data saved to your health profile!")
            st.balloons()
    
    elif page == "🎯 Targets & Goals":
        target_weight = st.number_input("🎯 Target Weight (kg)", 30.0, 150.0, metrics['ideal_weight'])
        col1, col2, col3 = st.columns(3)
        col1.metric("🍽️ Daily Calories", f"{metrics['tdee']} kcal")
        col2.metric("🍗 Protein Goal", f"{weight*1.6:.0f}g", f"{protein_intake}g ✓" if protein_intake >= weight*1.6 else f"{protein_intake}g")
        col3.metric("💧 Hydration", f"{weight*0.04:.1f}L", f"{water_intake}L")
        
        st.info(f"💡 **Weekly Goal Progress**: Weight difference to target: {abs(weight-target_weight):.1f}kg")
    
    elif page == "🩺 Health Insights":
        if metrics['bmi'] < 18.5:
            st.error("⚠️ **Underweight**: Consider increasing calorie intake with healthy fats & proteins")
        elif metrics['bmi'] > 24.9:
            st.warning("⚠️ **Overweight**: Aim for 500kcal deficit + cardio 4x/week")
        else:
            st.success("✅ **Healthy BMI range** - Excellent!")
        
        if sleep_hours < 6:
            st.error("😴 **Sleep Deficit**: Aim for 7-9 hours for optimal recovery")
        if daily_steps < 7000:
            st.warning("🚶 **Low Activity**: Target 10,000 steps daily")
            
        if hygiene_score < 70:
            st.error("🦠 **Hygiene Alert**: Improve daily hygiene routine")
    
    elif page == "📈 Progress Tracker":
        if not st.session_state['health_data'].empty:
            df = st.session_state['health_data'].copy()
            df['date'] = pd.to_datetime(df['date'])
            
            fig = px.line(df, x='date', y='weight', title="Weight Progress Over Time")
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Records", len(df))
                st.metric("Avg Weight", f"{df['weight'].mean():.1f}kg")
            with col2:
                st.metric("Best Hygiene", f"{df['hygiene_score'].max()}%")
                st.metric("Avg Steps", f"{df['steps'].mean():.0f}")
        else:
            st.info("👆 Save your first assessment from the Dashboard to see progress!")
    
    elif page == "🦠 Hygiene Monitor":
        st.info("🧼 **Daily Hygiene Score**: " + str(hygiene_score) + "%")
        
        hygiene_chart_data = pd.DataFrame({
            'Tasks': ['Teeth', 'Shower', 'Hand Wash', 'Room Clean'],
            'Score': [teeth_brushed*100, shower_today*100, min(hands_washed/15*100, 100), room_clean*100]
        })
        
        fig = px.bar(hygiene_chart_data, x='Tasks', y='Score', title="Today's Hygiene Breakdown")
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **Hygiene Tips:**
        - 🦷 Brush 2x daily (2 minutes each)
        - 🚿 Shower daily with antibacterial soap
        - 🧼 Wash hands 15+ times daily
        - 🧹 Keep living space clutter-free
        """)
    
    elif page == "📋 Records & Reports":
        if not st.session_state['health_data'].empty:
            st.dataframe(st.session_state['health_data'], use_container_width=True)
            
            if st.button("📄 Generate Professional PDF Report", use_container_width=True):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 20)
                pdf.cell(0, 15, "ProHealth Suite - Health Report", ln=True, align='C')
                pdf.ln(10)
                
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"User: {st.session_state['current_user']}", ln=True)
                pdf.cell(0, 10, f"Report Date: {datetime.date.today()}", ln=True)
                pdf.ln(10)
                
                # Summary stats
                df = st.session_state['health_data']
                pdf.cell(0, 10, f"Average Weight: {df['weight'].mean():.1f}kg", ln=True)
                pdf.cell(0, 10, f"Average Hygiene: {df['hygiene_score'].mean():.0f}%", ln=True)
                pdf.cell(0, 10, f"Total Records: {len(df)}", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("⬇️ Download Report", pdf_output, f"prohealth_report_{st.session_state['current_user']}.pdf", "application/pdf")
        else:
            st.warning("📭 No health records yet. Save assessments from Dashboard!")
    
    elif page == "🚪 Logout":
        st.session_state['logged_in'] = False
        st.session_state['current_user'] = None
        st.session_state['health_data'] = pd.DataFrame()
        st.success("👋 Logged out successfully!")
        st.rerun()

