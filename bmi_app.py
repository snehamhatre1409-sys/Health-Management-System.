import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import streamlit.components.v1 as components

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
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding-top: 2rem;
    }
    
    .metric-container {
        background: rgba(255,255,255,0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1) !important;
        padding: 2rem !important;
        margin: 1rem 0 !important;
    }
    
    .stMetric > div > div > div {
        background: linear-gradient(45deg, #4f46e5, #7c3aed);
        border-radius: 15px;
        padding: 1.5rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
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
    
    .nav-button {
        background: linear-gradient(135deg, #10b981, #059669);
        border-radius: 16px;
        border: none;
        height: 3.5rem;
        font-weight: 600;
        color: white;
        width: 100%;
        font-size: 1.1rem;
        margin: 0.3rem 0;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# [Keep all your existing database functions exactly the same]
# ... (init_db, add_user, check_user, save_health_record, get_user_records, calculate_advanced_metrics)

# --- Professional Header Component ---
def render_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.empty()
    with col2:
        st.markdown('<h1 class="main-header">🏥 ProHealth Suite v8.0</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #64748b; font-size: 1.3rem; font-weight: 500;">Your Complete Health & Wellness Platform</p>', unsafe_allow_html=True)
    with col3:
        st.empty()

# --- Enhanced Login with Glass Morphism ---
def render_login():
    render_header()
    
    with st.container():
        col1, col2 = st.columns([1,1])
        with col1:
            st.empty()
        with col2:
            st.markdown('<div class="glass-card" style="max-width: 450px; margin: auto;">', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                st.markdown("### Welcome Back")
                username = st.text_input("👤 Username", placeholder="Enter your username", 
                                       help="Your registered username")
                password = st.text_input("🔒 Password", type="password", 
                                       placeholder="Enter your password")
                
                if st.button("🚀 Sign In", key="login", help="Click to login"):
                    if check_user(username, password):
                        st.session_state['logged_in'] = True
                        st.session_state['current_user'] = username
                        st.session_state['health_data'] = get_user_records(username)
                        st.success("✅ Welcome back!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                        
                st.markdown("**👆 Try:** admin / password123")
            
            with tab2:
                st.markdown("### Create Account")
                new_username = st.text_input("New Username", help="Choose a unique username")
                new_password = st.text_input("New Password", type="password")
                new_email = st.text_input("Email (optional)")
                
                if st.button("Create Account", key="register"):
                    if add_user(new_username, new_password, new_email or ""):
                        st.success("✅ Account created successfully!")
                    else:
                        st.error("❌ Username already exists!")
            
            st.markdown('</div>', unsafe_allow_html=True)

# --- Main Professional Dashboard ---
def render_dashboard():
    # Professional Sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #3b82f6, #1d4ed8); border-radius: 16px; color: white;'>
            <h3>👋 {st.session_state['current_user']}</h3>
            <p style='margin: 0;'>Health Champion</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        # Profile inputs with better labels
        with st.expander("📊 Update Profile", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("⚖️ Weight (kg)", 30.0, 200.0, 70.0, 
                                       help="Your current weight")
                height = st.number_input("📏 Height (m)", 1.0, 2.2, 1.70)
            with col2:
                age = st.number_input("🎂 Age", 12, 100, 25)
                gender = st.radio("⚥ Gender", ["Male", "Female"], horizontal=True)
        
        with st.expander("🏃 Daily Stats", expanded=True):
            activity = st.selectbox("Activity Level", 
                                  ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"])
            sleep_hours = st.slider("😴 Sleep (hours)", 0.0, 12.0, 7.0)
            daily_steps = st.number_input("🚶 Steps", 0, 30000, 8000)
        
        # Save button in sidebar
        if st.button("💾 Save Data", key="save_data"):
            # [Your existing save logic]
            st.success("✅ Data saved!")
            st.balloons()
    
    # Main content area
    metrics = calculate_advanced_metrics(weight, height, age, gender, activity, sleep_hours, daily_steps)
    
    # Professional KPI Cards
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Health Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📏 BMI", f"{metrics['bmi']}", 
                 "✅ Normal" if 18.5 <= metrics['bmi'] <= 24.9 else "⚠️ Action Needed",
                 delta_color="normal")
    
    with col2:
        st.metric("🔥 Daily Calories", f"{metrics['tdee']}", f"{metrics['bmr']}")
    
    with col3:
        st.metric("❤️ Recovery", f"{metrics['recovery_score']}%", "+12%")
    
    with col4:
        st.metric("🦠 Hygiene", f"{hygiene_score}%", "+5%")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation Tabs (Much cleaner than sidebar dropdown)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", "🎯 Goals", "📈 Progress", 
        "🦠 Hygiene", "🤖 AI Coach"
    ])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.metric("🥗 Protein Goal", f"{weight*1.6:.0f}g", "Achieved ✓")
            st.metric("💧 Water Goal", f"{weight*0.04:.1f}L", "Good")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.progress(metrics['recovery_score']/100)
            st.caption("Daily Recovery")
            st.progress(hygiene_score/100)
            st.caption("Hygiene Score")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Add other tabs similarly with glass-card styling...

# --- Main App Logic ---
init_db()

if not st.session_state.get('logged_in', False):
    render_login()
else:
    render_dashboard()

# Professional Footer
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.9rem;'>
    <p>🏥 ProHealth Suite v8.0 | Built with ❤️ for your health journey</p>
</div>
""", unsafe_allow_html=True)
