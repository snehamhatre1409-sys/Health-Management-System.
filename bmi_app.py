import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v6.0", page_icon="⚖️", layout="wide")

# --- Custom Styling ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .main { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_db' not in st.session_state: st.session_state['user_db'] = {"admin": "password123"}
if 'health_data' not in st.session_state: st.session_state['health_data'] = []

# --- Logic Functions ---
def calculate_metrics(w, h, a, g, activity):
    # Basal Metabolic Rate (Mifflin-St Jeor)
    if g == "Male": bmr = 10 * w + 6.25 * (h*100) - 5 * a + 5
    else: bmr = 10 * w + 6.25 * (h*100) - 5 * a - 161
    
    # Activity Multipliers
    multipliers = {
        "Sedentary (Little/No Exercise)": 1.2,
        "Lightly Active (1-3 days/week)": 1.375,
        "Moderately Active (3-5 days/week)": 1.55,
        "Very Active (6-7 days/week)": 1.725
    }
    tdee = bmr * multipliers[activity]
    return round(bmr, 2), round(tdee, 2)

def calculate_macros(tdee, goal):
    # Adjust calories based on goal
    if goal == "Lose Weight": 
        target_cal = tdee - 500
        p_ratio, f_ratio, c_ratio = 0.30, 0.25, 0.45 
    elif goal == "Build Muscle": 
        target_cal = tdee + 300
        p_ratio, f_ratio, c_ratio = 0.25, 0.25, 0.50
    else: 
        target_cal = tdee
        p_ratio, f_ratio, c_ratio = 0.20, 0.30, 0.50

    # Grams calculation (P:4kcal, C:4kcal, F:9kcal)
    prot_g = (target_cal * p_ratio) / 4
    fat_g = (target_cal * f_ratio) / 9
    carb_g = (target_cal * c_ratio) / 4
    return round(target_cal), round(prot_g), round(fat_g), round(carb_g)

def get_suggestions(bmi_status, prot_diff, diseases):
    tips = []
    if bmi_status == "Overweight": tips.append("Focus on a 500kcal deficit and increase fiber intake.")
    if prot_diff < 0: tips.append(f"You are short by {abs(round(prot_diff))}g of protein for your goal.")
    if "Diabetes" in diseases: tips.append("⚠️ Limit simple sugars; focus on whole grains.")
    if "Hypertension" in diseases: tips.append("⚠️ Reduce sodium intake and monitor blood pressure.")
    if not tips: tips.append("Your metrics look balanced! Keep it up.")
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
            else: st.error("Incorrect username or password.")
    with tab2:
        new_u = st.text_input("Choose Username")
        new_p = st.text_input("Choose Password", type="password")
        if st.button("Register"):
            if new_u and new_p:
                st.session_state['user_db'][new_u] = new_p
                st.success("Registration successful! Switch to Login tab.")

# --- MAIN APPLICATION ---
else:
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}!")
    page = st.sidebar.selectbox("Go To:", ["Dashboard", "Analytics & History", "Export Report", "Logout"])

    if page == "Dashboard":
        st.title("📊 Personal Health Dashboard")
        col_input, col_res = st.columns([1, 1.2])
        
        with col_input:
            st.subheader("Physical Profile")
            w = st.number_input("Weight (kg)", 10.0, 250.0, 70.0)
            h = st.number_input("Height (m)", 0.5, 2.5, 1.70)
            age = st.number_input("Age", 5, 110, 25)
            gender = st.radio("Gender", ["Male", "Female"], horizontal=True)
            
            st.subheader("Lifestyle & Goals")
            activity = st.selectbox("Activity Level", ["Sedentary (Little/No Exercise)", "Lightly Active (1-3 days/week)", "Moderately Active (3-5 days/week)", "Very Active (6-7 days/week)"])
            goal = st.selectbox("Health Goal", ["Maintain Weight", "Lose Weight", "Build Muscle"])
            prot_in = st.number_input("Current Daily Protein Intake (g)", 0, 300, 60)
            diseases = st.multiselect("Medical Conditions", ["None", "Diabetes", "Hypertension", "Thyroid", "Kidney Disease"])

        with col_res:
            st.subheader("Analysis Results")
            bmi = round(w / (h**2), 2)
            bmr, tdee = calculate_metrics(w, h, age, gender, activity)
            target_cal, p_g, f_g, c_g = calculate_macros(tdee, goal)
            
            if bmi < 18.5: status, col = "Underweight", "blue"
            elif 18.5 <= bmi < 24.9: status, col = "Normal", "green"
            else: status, col = "Overweight", "red"
            
            st.metric("Body Mass Index (BMI)", f"{bmi}", f"{status}", delta_color="normal" if status=="Normal" else "inverse")
            st.metric("Daily Target Calories", f"{target_cal} kcal", f"TDEE: {tdee}")
            
            st.write("### 🥗 Nutrient Targets (grams)")
            st.table(pd.DataFrame({"Protein": [p_g], "Carbs": [c_g], "Fats": [f_g]}))

            st.write("### 💡 Suggestions")
            for tip in get_suggestions(status, (prot_in - p_g), diseases):
                st.info(tip)
            
        if st.button("💾 Save to Records"):
            st.session_state['health_data'].append({
                "Date": datetime.date.today().strftime("%Y-%m-%d"),
                "Weight": w, "BMI": bmi, "Status": status, "Conditions": ", ".join(diseases)
            })
            st.success("Record saved!")

    elif page == "Analytics & History":
        st.title("📈 Health Trends")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.line_chart(df.set_index("Date")["Weight"])
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Data as CSV", data=csv, file_name='health_records.csv', mime='text/csv')
        else: st.warning("No records found.")

    elif page == "Export Report":
        st.title("📄 Generate Medical PDF")
        if st.session_state['health_data']:
            data = st.session_state['health_data'][-1]
            if st.button("Generate Professional Report"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 20)
                pdf.cell(200, 15, "PROHEALTH MEDICAL SUMMARY", ln=True, align='C')
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(200, 10, f"User: {st.session_state['current_user']} | Date: {data['Date']}", ln=True)
                pdf.cell(200, 10, f"Conditions: {data['Conditions']}", ln=True)
                pdf.line(10, 60, 200, 60)
                pdf.ln(10)
                pdf.cell(100, 10, f"BMI: {data['BMI']} ({data['Status']})")
                pdf.cell(100, 10, f"Weight: {data['Weight']} kg", ln=True)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("📩 Download PDF", pdf_output, "ProHealth_Report.pdf", "application/pdf")
        else: st.error("Nothing to export!")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()
