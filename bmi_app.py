import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import streamlit.components.v1 as components

# --- Professional Page Configuration ---
st.set_page_config(
    page_title="ProHealth Suite v8.0 Pro",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3.2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .metric-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        height: 3.5rem !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        border: none !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4) !important;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #10b981, #34d399) !important;
        border-radius: 10px !important;
    }
    
    .stSelectbox > div > div > select {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Database (Same as before) ---
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

# --- Session State ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'current_user' not in st.session_state: st.session_state['current_user'] = None
if 'health_data' not in st.session_state: st.session_state['health_data'] = pd.DataFrame()

# --- Professional Metrics Calculation ---
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
        'ideal_weight': round(ideal_weight
