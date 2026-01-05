import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Checkout Survey", layout="centered")

# Initialize Session State
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'design_df' not in st.session_state:
    st.session_state.design_df = None
if 'survey_started' not in st.session_state:
    st.session_state.survey_started = False
if 'data_saved' not in st.session_state:
    st.session_state.data_saved = False

# --- 2. GOOGLE SHEETS CONNECTION ---
def save_to_google_sheets(answers, demographics):
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        s_dict = st.secrets["gcp_service_account"]
        creds_dict = dict(s_dict)
        creds_dict["private_key"] = s_dict["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open("Survey_Responses").sheet1 
        
        rows_to_append = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item in answers:
            row = [
                str(timestamp),
                str(st.session_state.session_id),
                
                # Demographics
                str(demographics.get('Gender', '')),
                str(demographics.get('Age', '')),
                str(demographics.get('Occupation', '')),
                str(demographics.get('Education', '')),
                str(demographics.get('Household_Size', '')),
                str(demographics.get('Income', '')),
                str(demographics.get('Urbanization', '')),
                str(demographics.get('Car_Owner', '')),
                
                # Distances
                str(demographics.get('Dist_Locker', '')),
                str(demographics.get('Dist_Pickup', '')),
                str(demographics.get('Dist_Shop', '')),
                
                # Habits
                str(demographics.get('Online_Freq', '')),
                str(demographics.get('Categories', '')),
                
                # Experiment Data
                int(item['Scenario_ID']),
                str(item['Context']),
                str(item['Choice'])
            ]
            rows_to_append.append(row)
            
        sheet.append_rows(rows_to_append)
        return True
        
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        return False

# --- 3. HELPER FUNCTIONS ---
def submit_answer(choice_label, scenario_id, context_label):
    clean_id = int(scenario_id) 
    st.session_state.answers.append({
        "Scenario_ID": clean_id,
        "Context": str(context_label),
        "Choice": str(choice_label)
    })
    st.session_state.current_q += 1

def go_back():
    if st.session_state.current_q > 0:
        st.session_state.current_q -= 1
        if st.session_state.answers:
            st.session_state.answers.pop()

def clean_display_text(text, cart_value):
    if "Add" in str(text):
        try:
            parts = text.split("Add ")
            gap = int(parts[1])
            if gap > (cart_value * 1.5):
                 return text.split(" or")[0]
        except:
            pass
    return text

# --- 4. APP LOGIC ---

# A. AUTOMATIC FILE LOAD
if st.session_state.design_df is None:
    try:
        df = pd.read_csv("shipping_topup_design_2.csv")
        if 'Context_Cart_Value' in df.columns:
            st.session_state.design_df = df
            st.rerun()
        else:
            st.error("Error: CSV columns missing.")
            st.stop()
    except FileNotFoundError:
        st.error("⚠️ Design file missing! Upload 'shipping_topup_design_2.csv' to GitHub.")
        st.stop()

# B. INTRO
if not st.session_state.survey_started:
    st.title("📦 Checkout Experiment")
    st.markdown("""
    ### Welcome!
    Imagine you are shopping online and have reached the **Checkout Page**.
    
    You will see **16 different shipping scenarios**. 
    Please choose the option that fits you best for each one.
    
    The survey takes about **2-3 minutes**.
    """)
    
    if st.button("Start Experiment", type="primary"):
        st.session_state.survey_started = True
        st.rerun()
    st.stop()

# --- 5. MAIN SURVEY LOOP ---
df = st.session_state.design_df
q_idx = st.session_state.current_q

# C. SCENARIOS COMPLETE -> SHOW DEMOGRAPHICS FORM
if q_idx >= len(df):
    
    st.success("✅ Scenarios Complete!")
    st.markdown("### Final Step: About You")
    st.markdown("Please answer these quick questions to finish the study.")
    
    if not st.session_state.data_saved:
        with st.form("demographics_form"):
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Prefer not to say"])
                age = st.selectbox("Age Group", ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
                edu = st.selectbox("Education", ["High School", "Bachelor's", "Master's", "PhD", "Other"])
                occ = st.selectbox("Occupation", ["Student", "Employed", "Self-employed", "Unemployed", "Retired"])
            with col2:
                hh_size = st.number_input("Household Size", min_value=1, max_value=10, step=1)
                income = st.selectbox("Monthly Household Income (SEK)", ["< 25,000", "25,000 - 45,000", "45,000 - 65,000", "> 65,000", "Prefer not to say"])
                urban = st.selectbox("Living Area", ["Urban (inside cordon)", "Suburban", "Rural"])
                car = st.radio("Do you own a car?", ["Yes", "No"], horizontal=True)

            st.markdown("---")
            st.markdown("**Your Location Context**")
            dist_locker = st.selectbox("Distance to nearest Parcel Locker", ["< 500 m", "500 m - 1 km", "1 - 3 km", "> 3 km"])
            dist_pickup = st.selectbox("Distance to nearest Service Point (Ombud)", ["< 500 m", "500 m - 1 km", "1 - 3 km", "> 3 km"])
            dist_shop = st.selectbox("Distance to nearest Shopping Center", ["< 1 km", "1 - 5 km", "5 - 10 km", "> 10 km"])

            st.markdown("---")
            st.markdown("**Shopping Habits**")
            freq = st.selectbox("Frequency of Online Shopping", [
                "Daily or almost daily", 
                "Several times a week", 
                "Once a week", 
                "2-3 times a month", 
                "Once a month", 
                "Less than once a month"
            ])
            cats = st.multiselect("What do you usually buy online?", [
                "Clothing/Fashion", 
                "Electronics", 
                "Barnprodukter & leksaker", 
                "Groceries", 
                "Home & Decor", 
                "Beauty/Health", 
                "Books/Media", 
                "Other"
            ])

            st.markdown("---")
            submitted = st.form_submit_button("Submit & Finish", type="primary")
            
            if submitted:
                demographics = {
                    "Gender": gender, "Age": age, "Education": edu,
                    "Occupation": occ, "Household_Size": hh_size, "Income": income,
                    "Urbanization": urban, "Car_Owner": car, 
                    "Dist_Locker": dist_locker, "Dist_Pickup": dist_pickup, "Dist_Shop": dist_shop,
                    "Online_Freq": freq, "Categories": ", ".join(cats)
                }
                
                with st.spinner("Saving your responses..."):
                    success = save_to_google_sheets(st.session_state.answers, demographics)
                    if success:
                        st.session_state.data_saved = True
                        st.rerun() 
                    else:
                        st.error("⚠️ Connection Error. Please download the backup CSV.")

    # D. SUCCESS SCREEN
    if st.session_state.data_saved:
        st.balloons()
        st.success("🎉 Thank you! Your responses have been saved.")
        st.write("You can close this tab now.")
        
        if st.button("Start New Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

else:
    # E. EXPERIMENT SCENARIOS
    col_back, col_prog = st.columns([1, 4])
    with col_back:
        if q_idx > 0:
            if st.button("⬅️ Back"):
                go_back()
                st.rerun()
    with col_prog:
        st.progress((q_idx) / len(df))
        st.caption(f"Question {q_idx + 1} of {len(df)}")

    row = df.iloc[q_idx]
    cart_val = row['Context_Cart_Value']
    home_disp = clean_display_text(row['Home_Display'], cart_val)
    
    # 🌿 SUSTAINABILITY FLAGS
    home_is_green = row['Home_Is_Green'] if 'Home_Is_Green' in row else False
    locker_is_green = row['Locker_Is_Green'] if 'Locker_Is_Green' in row else False

    st.markdown(f"""
    <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px; border: 1px solid #ddd;">
        <h3 style="margin:0; color:#333;">🛒 Cart Total: <b>{cart_val} SEK</b></h3>
        <p style="margin:0; color:#666;">Select your preferred delivery method below.</p>
    </div>
    """, unsafe_allow_html=True)

    def render_option_row(title, subtitle, display_text, col_key, label_base, context_label, scenario_id, 
                          is_green=False, is_express=False, distance=None):
        with st.container():
            c1, c2 = st.columns([1.6, 1])
            with c1:
                if is_express:
                    st.markdown(f"#### ⚡ {title}")
                else:
                    st.markdown(f"#### {title}")
                
                details = f"**⏱️ {subtitle}**"
                if distance:
                    details += f" &nbsp;•&nbsp; **📍 {distance}**"
                st.markdown(details, unsafe_allow_html=True)
                
                # 🌿 GREEN BADGE RENDERER
                if is_green:
                    st.markdown("🌿 <span style='color:#2e7d32; font-weight:bold;'>Fossil Free Delivery</span>", unsafe_allow_html=True)

            with c2:
                st.write("") 
                if " or Add " in display_text:
                    pay_text, add_text = display_text.split(" or ")
                    val_only = add_text.replace("Add ", "")
                    
                    btn_label = f"➕ Add {val_only} SEK\nGet FREE Delivery"
                    if st.button(btn_label, key=f"btn_add_{col_key}", use_container_width=True):
                        submit_answer(f"{label_base}_TOPUP", scenario_id, context_label)
                        st.rerun()
                    
                    if st.button(f"{pay_text}", key=f"btn_pay_{col_key}", use_container_width=True):
                        submit_answer(f"{label_base}_PAID", scenario_id, context_label)
                        st.rerun()

                else:
                    if "FREE" in display_text.upper():
                        btn_label = f"✅ FREE Shipping"
                        style_type = "secondary"
                    else:
                        btn_label = f"{display_text}"
                        style_type = "secondary"
                    
                    if st.button(btn_label, key=f"btn_std_{col_key}", type=style_type, use_container_width=True):
                        submit_answer(f"{label_base}_FLAT", scenario_id, context_label)
                        st.rerun()
            st.divider()

    # RENDER ROWS WITH SUSTAINABILITY FLAGS
    
    # 1. Standard Home (Can be Green)
    render_option_row("Standard Home", "2-4 Days", home_disp, f"h_std_{q_idx}", "Home_Standard", row['Context_Label'], row['Scenario_ID'], is_green=home_is_green)
    
    # 2. Express Home (Never Green)
    render_option_row("Express Home", "Next Day", row['Home_Exp_Display'], f"h_exp_{q_idx}", "Home_Express", row['Context_Label'], row['Scenario_ID'], is_express=True)
    
    # 3. Standard Locker (Can be Green + Has Distance)
    locker_dist = row['Locker_Distance'] if 'Locker_Distance' in row else None
    render_option_row("Parcel Locker", "2-4 Days", row['Locker_Display'], f"l_std_{q_idx}", "Locker_Standard", row['Context_Label'], row['Scenario_ID'], is_green=locker_is_green, distance=locker_dist)
    
    # 4. Express Locker (Never Green + Has Distance)
    render_option_row("Express Locker", "Next Day", row['Locker_Exp_Display'], f"l_exp_{q_idx}", "Locker_Express", row['Context_Label'], row['Scenario_ID'], is_express=True, distance=locker_dist)
    
    # 5. Store Collect (Has Distance)
    shop_dist = row['Shop_Distance'] if 'Shop_Distance' in row else None
    render_option_row("Store Collect", "2-4 Days", row['Shop_Display'], f"s_col_{q_idx}", "Shop_Collect", row['Context_Label'], row['Scenario_ID'], distance=shop_dist)
