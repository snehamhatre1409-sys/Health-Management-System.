import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- Page Configuration ---
st.set_page_config(page_title="ProHealth Suite v6.0", page_icon="🏥", layout="wide")

# --- Custom Styling ---
.stMetric { 
    background-color: #ffffff; 
    padding: 15px; 
    border-radius: 10px; 
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
/* This forces the text inside the white boxes to be dark gray */
[data-testid="stMetricValue"] {
    color: #31333F !important;
}
[data-testid="stMetricLabel"] {
    color: #555555 !important;
}

# --- Initialize Session States ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'user_db' not in st.session_state: st.session_state['user_db'] = {"admin": "password123"}
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
    if prot_diff < 0: tips.append(f"You are short by {abs(round(prot_diff, 1))}g of protein. Consider adding Greek yogurt or lean meats.")
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
    # Sidebar Input (Available across all pages)
    st.sidebar.title(f"Welcome, {st.session_state['current_user']}!")
    
    st.sidebar.subheader("📋 Your Vitals")
    w = st.sidebar.number_input("Weight (kg)", 10.0, 250.0, 70.0)
    h = st.sidebar.number_input("Height (m)", 0.5, 2.5, 1.70)
    age = st.sidebar.number_input("Age", 5, 110, 25)
    gender = st.sidebar.radio("Gender", ["Male", "Female"])
    activity = st.sidebar.selectbox("Activity Level", ["Sedentary (Little/No Exercise)", "Lightly Active (1-3 days/week)", "Moderately Active (3-5 days/week)", "Very Active (6-7 days/week)"])
    prot_in = st.sidebar.number_input("Daily Protein Intake (g)", 0, 300, 50)
    diseases = st.sidebar.multiselect("Medical Conditions", ["None", "Diabetes", "Hypertension", "Thyroid", "Kidney Disease"])

    # Perform Calculations once
    bmi = round(w / (h**2), 2)
    bmr, tdee, prot_target = calculate_metrics(w, h, age, gender, activity)
    prot_diff = prot_in - prot_target
    if bmi < 18.5: status = "Underweight"
    elif 18.5 <= bmi < 24.9: status = "Normal"
    else: status = "Overweight"

    st.sidebar.divider()
    page = st.sidebar.selectbox("Go To Page:", ["1. Analysis Dashboard", "2. Target & Nutrition", "3. Health Suggestions", "4. History & Analytics", "5. Export Report", "Logout"])

    # --- PAGE 1: ANALYSIS ---
    if page == "1. Analysis Dashboard":
        st.title("📊 Physical Analysis")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Body Mass Index (BMI)", f"{bmi}", status)
            st.write("BMI is a measure of body fat based on height and weight.")
        with c2:
            st.metric("Basal Metabolic Rate (BMR)", f"{bmr} kcal")
            st.write("This is the energy your body needs at complete rest.")
        
        if st.button("💾 Save Current Metrics to History"):
            st.session_state['health_data'].append({
                "Date": datetime.date.today().strftime("%Y-%m-%d"),
                "Weight": w, "BMI": bmi, "TDEE": tdee, "Conditions": ", ".join(diseases)
            })
            st.success("Assessment Saved!")

    # --- PAGE 2: TARGETS ---
    elif page == "2. Target & Nutrition":
        st.title("🎯 Daily Health Targets")
        c1, c2, c3 = st.columns(3)
        c1.metric("Calories (TDEE)", f"{tdee} kcal")
        c2.metric("Protein Goal", f"{prot_target}g")
        c3.metric("Water Goal", f"{round(w*0.035, 2)}L")
        
        st.write("### Macronutrient Breakdown")
        st.info(f"Based on your activity level (**{activity}**), you need **{tdee}** calories to maintain your current weight.")
        
    # --- PAGE 3: SUGGESTIONS ---
    elif page == "3. Health Suggestions":
        st.title("💡 Personal Suggestions")
        suggestions = get_suggestions(status, prot_diff, diseases)
        for s in suggestions:
            st.success(s) if "Normal" in s else st.warning(s)

    # --- PAGE 4: HISTORY ---
    elif page == "4. History & Analytics":
        st.title("📈 Longitudinal Health Data")
        if st.session_state['health_data']:
            df = pd.DataFrame(st.session_state['health_data'])
            st.line_chart(df.set_index("Date")["Weight"])
            st.dataframe(df, use_container_width=True)
        else: st.warning("No records found. Save data from the Dashboard.")

    # --- PAGE 5: EXPORT ---
    elif page == "5. Export Report":
        st.title("📄 Clinical Summary PDF")
        if st.session_state['health_data']:
            data = st.session_state['health_data'][-1]
            if st.button("Generate Final PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "PROHEALTH DIAGNOSTIC REPORT", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(200, 10, f"Patient: {st.session_state['current_user']} | Date: {data['Date']}", ln=True)
                pdf.cell(200, 10, f"BMI: {data['BMI']} | Maintenance: {data['TDEE']} kcal", ln=True)
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button("📩 Download PDF", pdf_output, "Health_Report.pdf", "application/pdf")
        else: st.error("No data to export.")

    elif page == "Logout":
        st.session_state['logged_in'] = False
        st.rerun()

