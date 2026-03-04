import streamlit as st
import pandas as pd
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# ============================================
# 1. CONFIG & SETUP
# ============================================
st.set_page_config(page_title="Checkout Survey", layout="wide")

# CSS for the "E-commerce" look
st.markdown("""
<style>
    .main { background-color: #f9f9f9; }
    .product-card {
        background: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center;
    }
    .price-tag { font-size: 24px; font-weight: bold; color: #333; }
    .total-row { border-top: 1px solid #eee; padding-top: 10px; margin-top: 20px; font-weight: bold; }
    
    /* Radio button custom styling */
    div.row-widget.stRadio > div { flex-direction: column; }
    div.row-widget.stRadio > div[role='radiogroup'] > label {
        background-color: white;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        border-radius: 8px;
        width: 100%;
        display: flex;
        justify-content: space-between;
    }
    div.row-widget.stRadio > div[role='radiogroup'] > label:hover {
        background-color: #f0f2f6;
        border-color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 2. THE 12 SCENARIOS (Verified)
# ============================================
scenarios = [
    {"id": 1, "h_s": 59, "h_e": 89, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 2, "h_s": 89, "h_e": 119, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 3, "h_s": 59, "h_e": 99, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 4, "h_s": 29, "h_e": 49, "l_d": "< 1 km", "l_s": 19, "l_e": 29, "s_d": "6-8 km", "s_p": 0},
    {"id": 5, "h_s": 89, "h_e": 109, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 6, "h_s": 29, "h_e": 69, "l_d": "< 1 km", "l_s": 19, "l_e": 29, "s_d": "4-6 km", "s_p": 0},
    {"id": 7, "h_s": 59, "h_e": 99, "l_d": "< 1 km", "l_s": 29, "l_e": 39, "s_d": "4-6 km", "s_p": 19},
    {"id": 8, "h_s": 89, "h_e": 129, "l_d": "1-2 km", "l_s": 19, "l_e": 29, "s_d": "6-8 km", "s_p": 0},
    {"id": 9, "h_s": 29, "h_e": 49, "l_d": "2-3 km", "l_s": 0, "l_e": 29, "s_d": "2-4 km", "s_p": 0},
    {"id": 10, "h_s": 89, "h_e": 129, "l_d": "1-2 km", "l_s": 29, "l_e": 39, "s_d": "4-6 km", "s_p": 19},
    {"id": 11, "h_s": 59, "h_e": 89, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "6-8 km", "s_p": 19},
    {"id": 12, "h_s": 29, "h_e": 59, "l_d": "2-3 km", "l_s": 0, "l_e": 19, "s_d": "2-4 km", "s_p": 0},
]

# ============================================
# 3. GOOGLE SHEETS FUNCTION
# ============================================
def save_to_google_sheets(answers, demographics):
    try:
        # Load credentials from .streamlit/secrets.toml
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Check if secrets exist
        if "gcp_service_account" not in st.secrets:
            st.error("Missing Google Secrets in .streamlit/secrets.toml")
            return False
            
        s_dict = st.secrets["gcp_service_account"]
        creds_dict = dict(s_dict)
        creds_dict["private_key"] = s_dict["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the specific sheet. Ensure 'Survey_Responses' exists in your Drive.
        sheet = client.open("Survey_greendelivery_nudging").sheet1 
        
        rows = []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item in answers:
            row = [
                ts, 
                str(st.session_state.session_id),
                str(item['group']), # The Experimental Group
                str(demographics.get('Gender', '')),
                str(demographics.get('Age', '')),
                str(demographics.get('Occupation', '')),
                str(demographics.get('Education', '')),
                str(demographics.get('Household_Size', '')),
                str(demographics.get('Income', '')),
                str(demographics.get('Urbanization', '')),
                str(demographics.get('Car_Owner', '')),
                str(demographics.get('Dist_Locker', '')),
                str(demographics.get('Dist_Pickup', '')),
                str(demographics.get('Dist_Shop', '')),
                str(demographics.get('Online_Freq', '')),
                str(demographics.get('freq_used_mode_tolocker', '')),
                str(demographics.get('mode_locker', '')),
                str(demographics.get('freq_used_mode_toshop', '')),
                str(demographics.get('mode_shop', '')),
                str(demographics.get('Categories', '')),
                int(item['scenario_id']),
                str(item['choice']),
                str(item['choice_price']),
                str(item['choice_dist'])
            ]
            rows.append(row)
            
        sheet.append_rows(rows)
        return True
        
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        return False

# ============================================
# 4. SESSION STATE & GROUP ASSIGNMENT
# ============================================
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(random.randint(100000, 999999))

if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
    st.session_state.answers = []
    
    # ASSIGN GROUP: Check URL first, then Random
    query_params = st.query_params
    if "group" in query_params:
        st.session_state.group = query_params["group"]
    else:
        # Randomly assign if no URL param
        st.session_state.group = random.choice(["control", "label", "co2"])

# ============================================
# 5. HELPER: NUDGE TEXT GENERATOR
# ============================================
def get_nudge_text(mode, group):
    """Returns the visual Nudge based on Group"""
    if group == "control":
        return ""
    
    if group == "label":
        # Green Leaf for Lockers and Store
        if mode in ["Parcel Locker", "Express Locker", "Store Collect"]:
            return "🌿 Eco Choice"
        return ""
    
    if group == "co2":
        # Specific CO2 values
        if mode == "Express Home": return "🔴 850g CO2e"
        if mode == "Standard Home": return "🟠 300g CO2e"
        if mode in ["Parcel Locker", "Express Locker", "Store Collect"]:
            return "🟢 50g CO2e"
            
    return ""

# ============================================
# 6. MAIN APP LOGIC
# ============================================

# --- PHASE 1: THE 12 SCENARIOS ---
if st.session_state.current_q < len(scenarios):

    q_data = scenarios[st.session_state.current_q]
    
    # Progress
    st.progress((st.session_state.current_q) / len(scenarios))
    st.write(f"Question {st.session_state.current_q + 1} of {len(scenarios)}")
    
    col1, col2 = st.columns([1, 2])
    
    # --- LEFT: PRODUCT IMAGE ---
    with col1:
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        
        # IMAGE CHECKER: Try local file, fallback to URL
        if os.path.exists("example.jpg"):
            st.image("example.jpg", use_column_width=True)
        else:
            # Fallback placeholder
            st.image("https://via.placeholder.com/300x350.png?text=RM+Hoodie", use_column_width=True)
            
        st.markdown(f"""
            <h3>RM Pullover Hoodie</h3>
            <p>Size: M | Color: Navy</p>
            <div class="price-tag">499 SEK</div>
            <div class="total-row">Subtotal: 499 SEK</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RIGHT: DELIVERY OPTIONS ---
    with col2:
        st.subheader("Select Delivery Method")
        
        # Define Options
        options = [
            {"name": "Standard Home", "time": "2-4 days", "dist": "Doorstep", "price": q_data['h_s']},
            {"name": "Express Home", "time": "Next Day", "dist": "Doorstep", "price": q_data['h_e']},
            {"name": "Parcel Locker", "time": "2-4 days", "dist": q_data['l_d'], "price": q_data['l_s']},
            {"name": "Express Locker", "time": "Next Day", "dist": q_data['l_d'], "price": q_data['l_e']},
            {"name": "Store Collect", "time": "2-4 days", "dist": q_data['s_d'], "price": q_data['s_p']},
        ]
        
        # Build Radio Labels
        radio_labels = []
        opt_lookup = {}
        
        for opt in options:
            nudge = get_nudge_text(opt['name'], st.session_state.group)
            price_str = "FREE" if opt['price'] == 0 else f"{opt['price']} SEK"
            
            # Markdown Label
            label = f"**{opt['name']}** |  {opt['time']}  |  {opt['dist']}  |  **{price_str}**"
            if nudge:
                label += f"  \n_{nudge}_" # New line for nudge
            
            radio_labels.append(label)
            opt_lookup[label] = opt

        # Render Radio
        choice = st.radio("Options:", radio_labels, key=f"q_{st.session_state.current_q}")
        
        st.markdown("---")
       # --- NEW NAVIGATION COLUMNS ---
        nav_col1, nav_col2 = st.columns(2)
        
        # BACK BUTTON (Only shows if it's NOT the first question)
        with nav_col1:
            if st.session_state.current_q > 0:
                if st.button("⬅️ Go Back", use_container_width=True):
                    # Reduce question counter by 1
                    st.session_state.current_q -= 1
                    # Remove the previous answer to avoid duplicates
                    if len(st.session_state.answers) > 0:
                        st.session_state.answers.pop()
                    st.rerun()
                    
        # NEXT BUTTON
        with nav_col2:
            if st.button("Confirm Selection ➡️", type="primary", use_container_width=True):
                selected = opt_lookup[choice]
                
                st.session_state.answers.append({
                    "scenario_id": q_data['id'],
                    "group": st.session_state.group,
                    "choice": selected['name'],
                    "choice_price": selected['price'],
                    "choice_dist": selected['dist']
                })
                
                st.session_state.current_q += 1
                st.rerun()

# --- PHASE 2: DEMOGRAPHICS FORM ---
else:
    st.subheader("Almost done! Please answer a few questions about yourself.")
    
    with st.form("demographics_form"):
        d_gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Prefer not to say"])
        d_age = st.selectbox("Age Group", ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
        d_educ = st.selectbox("Education Level", ["High School", "University (Bachelor)", "University (Master/PhD)", "Other"])
        d_occup = st.selectbox("Occupation", ["Student", "Employed", "Self-employed", "Unemployed", "Retired"])
        d_income = st.selectbox("Monthly Income (after Tax)", ["< 20k SEK", "20k-35k SEK", "35k-50k SEK", "> 50k SEK", "Prefer not to say"])
        d_urban = st.selectbox("Living Area", ["Urban (Center)", "Suburban", "Rural"])
        d_hh_size = st.number_input("Household Size", 1, 10, 1)
        d_car = st.radio("Do you have access to a car?", ["Yes", "No"])
        
        st.markdown("---")
        st.write("**Your Shopping Habits**")
        d_freq = st.selectbox("How often do you shop online?", ["Daily", "Weekly", "Monthly", "Rarely"])
        d_cat = st.multiselect("What do you usually buy online?", ["Clothing", "Electronics", "Beauty/Pharmacy", "Groceries", "Home Goods"])
        
        st.markdown("---")
        st.write("**Distance to Service Points**")
        d_dist_l = st.selectbox("Distance to nearest Parcel Locker from home", ["< 500m", "500m - 1km", "1-3 km", "> 3km"])
        d_dist_s = st.selectbox("Distance to nearest Shop Center", ["<1km", "1-3km", "3-6km", ">6km"])
        
        # New Transportation Mode Questions
        st.markdown("---")
        st.write("**Transportation Habits**")
        d_freq_tolocker = st.selectbox("How do you usually travel to pick up parcels (Locker)?", ["Walk", "Bike", "Car", "Public Transport", "N/A"])
        d_freq_toshop = st.selectbox("How do you usually travel to pick up parcels (Store)?", ["Walk", "Bike", "Car", "Public Transport", "N/A"])

        submitted = st.form_submit_button("Submit Survey")
        
        if submitted:
            # Gather Demographics
            demographics = {
                "Gender": d_gender, "Age": d_age, "Education": d_educ, 
                "Occupation": d_occup, "Income": d_income, "Urbanization": d_urban,
                "Household_Size": d_hh_size, "Car_Owner": d_car,
                "Online_Freq": d_freq, "Categories": ", ".join(d_cat),
                "Dist_Locker": d_dist_l, "Dist_Pickup": d_dist_s,
                "Dist_Shop": "N/A", 
                "freq_used_mode_tolocker": "Always/Often", # Simplified for now, mapped from selection
                "mode_locker": d_freq_tolocker,
                "freq_used_mode_toshop": "Always/Often", 
                "mode_shop": d_freq_toshop
            }
            
            # Save to Google Sheets
            success = save_to_google_sheets(st.session_state.answers, demographics)
            
            if success:
                st.success("Data saved successfully! Thank you for participating.")
                st.balloons()
            else:
                st.error("There was an error saving your data. Please check your internet connection.")
