import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v7.0 - Advanced", page_icon="🏥", layout="wide")

# --- Professional Custom Styling ---
st.markdown("""
    <style>
    /* Main Background and Font */
    .stApp { background-color: #fcfcfc; }
    
    /* Professional Card Styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #eee;
        text-align: center;
    }
    
    /* Header Styling */
    .main-header { 
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 2.8em; 
        color: #1b5e20; 
        text-align: center; 
        margin-bottom: 0px;
        font-weight: 800;
    }
    
    /* Custom Button */
    .stButton>button {
        border-radius: 8px;
        height: 3em;
        background: linear-gradient(45deg, #1b5e20, #2e7d32);
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Database Setup (Unchanged Logic) ---
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
                  hygiene_score INTEGER, conditions TEXT,
                  FOREIGN KEY(username) REFERENCES users(username))''')
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

def draw_gauge(value, title, color="#2e7d32"):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title, 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'bgcolor': "white",
            'steps': [
                {'range': [0, 40], 'color': '#ffedea'},
                {'range': [40, 70], 'color': '#fff9ea'},
                {'range': [70, 100], 'color': '#f1f8e9'}]
        }
    ))
    fig.update_layout(height=200, margin=dict(l=30, r=30, t=30, b=0))
    return fig

init_db()

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None
if 'health_data' not in st.session_state: st.session_state['health_data'] = pd.DataFrame()

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
    body_fat = 1.20 * bmi + 0.23 * a - 16.2 if g == "Male" else 1.20 * bmi + 0.23 * a - 5.4
    recovery_score = (sleep * 0.4 + steps/10000 * 0.3 + (w/ideal_weight)*0.3)
    return {
        'bmi': round(bmi, 1), 'bmr': round(bmr, 0), 'tdee': round(tdee, 0),
        'ideal_weight': round(ideal_weight, 1), 'body_fat': round(body_fat, 1),
        'recovery_score': min(100, round(recovery_score * 100, 0))
    }

# --- Login Interface ---
if not st.session_state['logged_in']:
    st.markdown('<h1 class="main-header">🏥 ProHealth Suite</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Enterprise Health Management System</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Secure Login", "📝 New Registration"])
        with tab1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if check_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = username
                    st.session_state['health_data'] = get_user_records(username)
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        with tab2:
            new_u = st.text_input("Choose Username")
            new_p = st.text_input("Choose Password", type="password")
            new_e = st.text_input("Email Address")
            if st.button("Register"):
                if add_user(new_u, new_p, new_e):
                    st.success("Account created!")
                else:
                    st.error("Username exists")

# --- Main Application ---
else:
    # Sidebar Organization
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state['current_user']}")
        
        with st.expander("📊 Body Profile", expanded=True):
            weight = st.number_input("Weight (kg)", 30.0, 200.0, 70.0)
            height = st.number_input("Height (m)", 1.0, 2.2, 1.70)
            age = st.number_input("Age", 12, 100, 25)
            gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
        
        with st.expander("🏃 Activity"):
            activity = st.selectbox("Level", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
            sleep_hours = st.slider("Sleep (hrs)", 0.0, 12.0, 7.0)
            daily_steps = st.number_input("Steps Today", 0, 30000, 8000)
            water_intake = st.number_input("Water (L)", 0.0, 10.0, 2.5)
            protein_intake = st.number_input("Protein (g)", 0, 300, 100)
            conditions = st.multiselect("Conditions", ["None", "Diabetes", "Hypertension", "Thyroid", "Asthma"])

        with st.expander("🧼 Hygiene"):
            teeth_brushed = st.checkbox("Teeth Brushed")
            shower_today = st.checkbox("Shower")
            hands_washed = st.number_input("Hand Washes", 0, 50, 10)
            room_clean = st.checkbox("Room Clean")
        
        if st.sidebar.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    hygiene_score = (teeth_brushed*25 + shower_today*25 + min(hands_washed/2, 25) + room_clean*25)
    metrics = calculate_advanced_metrics(weight, height, age, gender, activity, sleep_hours, daily_steps)

    # Top Navigation Tabs
    st.markdown('<h1 class="main-header">ProHealth Dashboard</h1>', unsafe_allow_html=True)
    page = st.tabs(["📊 Overview", "🎯 Goals", "📈 Analytics", "🤖 AI Assistant", "📋 Reports"])

    # PAGE: OVERVIEW
    with page[0]:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.plotly_chart(draw_gauge(metrics['bmi'], "BMI"), use_container_width=True)
        with c2: st.plotly_chart(draw_gauge(metrics['recovery_score'], "Recovery"), use_container_width=True)
        with c3: st.plotly_chart(draw_gauge(hygiene_score, "Hygiene"), use_container_width=True)
        with c4: 
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("TDEE", f"{metrics['tdee']} kcal")
            st.metric("Steps", f"{daily_steps}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        if st.button("💾 Log Daily Assessment", use_container_width=True):
            record_data = {'date': datetime.date.today().strftime("%Y-%m-%d"), 'weight': weight, 'height': height, 'age': age, 'gender': gender, 'activity': activity, 'protein_intake': protein_intake, 'sleep_hours': sleep_hours, 'water_intake': water_intake, 'steps': daily_steps, 'hygiene_score': hygiene_score, 'conditions': ', '.join(conditions)}
            save_health_record(st.session_state['current_user'], record_data)
            st.session_state['health_data'] = get_user_records(st.session_state['current_user'])
            st.success("Record Saved!")

    # PAGE: GOALS
    with page[1]:
        target_weight = st.number_input("🎯 Target Weight (kg)", 30.0, 150.0, metrics['ideal_weight'])
        st.markdown("---")
        st.subheader("🥗 Specialized Nutrition")
        diet_type = st.radio("Goal:", ["Weight Loss", "Maintain", "Muscle Gain"], horizontal=True)
        target_cal = metrics['tdee'] - 500 if diet_type == "Weight Loss" else metrics['tdee'] + 300 if diet_type == "Muscle Gain" else metrics['tdee']
        st.info(f"Daily Target: {target_cal:.0f} kcal/day")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("**🍳 Breakfast:** Oatmeal or Eggs | **🍱 Lunch:** Chicken Quinoa Bowl")
        with col_d2:
            st.markdown("**🍽️ Dinner:** Salmon & Greens | **🍎 Snacks:** Nuts & Greek Yogurt")

    # PAGE: ANALYTICS
    with page[2]:
        if not st.session_state['health_data'].empty:
            df = st.session_state['health_data'].copy()
            df['date'] = pd.to_datetime(df['date'])
            fig = px.area(df, x='date', y='weight', title="Weight Trend Line")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data logged yet.")

    # PAGE: AI ASSISTANT
    with page[3]:
        st.subheader("🤖 Health Concierge")
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Ask anything..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            # Simple Logic (Unchanged)
            resp = "I'm here to help with your health journey!"
            if "calorie" in prompt.lower(): resp = f"Your TDEE is {metrics['tdee']}. Aim for {metrics['tdee']-500} for weight loss."
            st.session_state.messages.append({"role": "assistant", "content": resp})
            st.rerun()

    # PAGE: REPORTS
    with page[4]:
        if not st.session_state['health_data'].empty:
            st.dataframe(st.session_state['health_data'])
            if st.button("📄 Export PDF Report"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"Health Report: {st.session_state['current_user']}", ln=True)
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"Average Hygiene: {st.session_state['health_data']['hygiene_score'].mean()}%", ln=True)
                st.download_button("Download Now", data=pdf.output(), file_name="report.pdf")
        else:
            st.warning("No records to export.")
