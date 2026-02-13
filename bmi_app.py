import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v6.0", page_icon="🏥", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #1b5e20; color: white; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_db' not in st.session_state: st.session_state['user_db'] = {"admin": "password123"}
if 'health_data' not in st.session_state: st.session_state['health_data'] = []

# --- Logic Functions ---
def calculate_macros(tdee, goal, weight):
    # Adjust calories based on goal
    if goal == "Lose Weight": 
        target_cal = tdee - 500
        p_ratio, f_ratio, c_ratio = 0.30, 0.25, 0.45 # Higher protein for satiety
    elif goal == "Build Muscle": 
        target_cal = tdee + 300
        p_ratio, f_ratio, c_ratio = 0.25, 0.25, 0.50
    else: 
        target_cal = tdee
        p_ratio, f_ratio, c_ratio = 0.20, 0.30, 0.50

    # Calculate Grams (Protein/Carbs = 4 kcal/g, Fat = 9 kcal/g)
    prot_g = (target_cal * p_ratio) / 4
    fat_g = (target_cal * f_ratio) / 9
    carb_g = (target_cal * c_ratio) / 4
    
    return round(target_cal), round(prot_g), round(fat_g), round(carb_g)

# --- Inside your Dashboard Logic ---
with col_input:
    st.subheader("🎯 Health Goal")
    goal = st.selectbox("What is your primary goal?", ["Maintain Weight", "Lose Weight", "Build Muscle"])

with col_res:
    target_cal, p_g, f_g, c_g = calculate_macros(tdee, goal, w)
    
    st.write(f"### 🎯 Daily Target for {goal}")
    st.success(f"**{target_cal} Calories / Day**")
    
    # Visualizing Macros as a Table
    macro_df = pd.DataFrame({
        "Nutrient": ["Protein (g)", "Fats (g)", "Carbs (g)"],
        "Target": [p_g, f_g, c_g],
        "Current": [prot_in, "-", "-"] # You can track others if you add inputs
    })
    st.table(macro_df)

    st.write("### 🍱 Sample Meal Structure")
    st.caption(f"To hit your protein goal of {p_g}g, try to eat:")
    st.info(f"Standard: 3 meals of **{round(p_g/3)}g** protein each + 1 snack.")

def get_suggestions(bmi_status, prot_diff, diseases):
    tips = []
    if bmi_status == "Overweight": tips.append("Focus on a 500kcal deficit and increase fiber intake.")
    if prot_diff < 0: tips.append(f"You are short by {abs(prot_diff)}g of protein. Consider adding Greek yogurt, lean meats, or lentils.")
    if "Diabetes" in diseases: tips.append("⚠️ Limit simple sugars and monitor Glycemic Index (GI) of carbs.")
    if "Hypertension" in diseases: tips.append("⚠️ Reduce sodium intake to under 2,300mg per day.")
    if not tips: tips.append("Your metrics look balanced! Maintain your current routine.")
    return tips

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
            else: st.error("Incorrect credentials.")
    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if new_u and new_p:
                st.session_state['user_db'][new_u] = new_p
                st.success("Success! Please Login.")

# --- MAIN APPLICATION ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}!")
    page = st.sidebar.selectbox("Go To:", ["Dashboard", "Analytics & History", "Export Report", "Logout"])

    if page == "Dashboard":
        st.title("📊 Health & Nutrition Intelligence")
        
        col_input, col_res = st.columns([1, 1.2])
        
        with col_input:
            st.subheader("Physical Profile")
            w = st.number_input("Weight (kg)", 10.0, 250.0, 70.0)
            h = st.number_input("Height (m)", 0.5, 2.5, 1.70)
            age = st.number_input("Age", 5, 110, 25)
            gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
            
            st.subheader("Lifestyle & Diet")
            activity = st.selectbox("Activity Level", [
                "Sedentary (Little/No Exercise)", 
                "Lightly Active (1-3 days/week)", 
                "Moderately Active (3-5 days/week)", 
                "Very Active (6-7 days/week)"
            ])
            prot_in = st.number_input("Current Daily Protein Intake (grams)", 0, 300, 50)
            diseases = st.multiselect("Existing Medical Conditions", ["None", "Diabetes", "Hypertension", "Thyroid", "Kidney Disease"])

        with col_res:
            st.subheader("Analysis Results")
            bmi = round(w / (h**2), 2)
            bmr, tdee, prot_target = calculate_metrics(w, h, age, gender, activity)
            prot_diff = prot_in - prot_target
            
            if bmi < 18.5: status, col = "Underweight", "blue"
            elif 18.5 <= bmi < 24.9: status, col = "Normal", "green"
            else: status, col = "Overweight", "red"
            
            # Metrics Row 1
            m1, m2 = st.columns(2)
            m1.metric("BMI Status", f"{bmi}", status)
            m2.metric("Maintenance Calories (TDEE)", f"{tdee} kcal")
            
            # Metrics Row 2
            m3, m4 = st.columns(2)
            m3.metric("Protein Target", f"{prot_target}g", f"{prot_diff}g diff")
            m4.metric("Water Target", f"{round(w*0.035, 2)}L")

            st.write("### 💡 Professional Suggestions")
            suggestions = get_suggestions(status, prot_diff, diseases)
            for s in suggestions:
                st.info(s)

        if st.button("💾 Archive Assessment"):
            st.session_state['health_data'].append({
                "Date": datetime.date.today().strftime("%Y-%m-%d"),
                "Weight": w, "BMI": bmi, "TDEE": tdee, 
                "Protein_Gap": prot_diff, "Conditions": ", ".join(diseases)
            })
            st.success("Assessment Saved!")

    elif page == "Analytics & History":
        st.title("📈 Longitudinal Health Data")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.line_chart(df.set_index("Date")["Weight"])
            st.dataframe(df, use_container_width=True)
        else: st.warning("No records found.")

    elif page == "Export Report":
        st.title("📄 Clinical Summary PDF")
        if st.session_state['health_data']:
            data = st.session_state['health_data'][-1]
            if st.button("Generate Final PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "PROHEALTH DIAGNOSTIC REPORT", ln=True, align='C')
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(200, 10, f"Patient: {st.session_state['current_user']} | Date: {data['Date']}", ln=True)
                pdf.cell(200, 10, f"BMI: {data['BMI']} | Maintenance: {data['TDEE']} kcal", ln=True)
                pdf.cell(200, 10, f"Medical History: {data['Conditions']}", ln=True)
                pdf.cell(200, 10, f"Protein Intake Gap: {data['Protein_Gap']}g", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("📩 Download PDF", pdf_output, "Health_Report.pdf", "application/pdf")
        else: st.error("No data to export.")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

