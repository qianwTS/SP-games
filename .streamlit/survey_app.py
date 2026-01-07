import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Checkout Survey", layout="centered")

# --- CUSTOM CSS FOR COMPACT MOBILE VIEW ---
st.markdown("""
    <style>
        /* 1. Shrink the main page padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* 2. Reduce gap between elements */
        div[data-testid="stVerticalBlock"] {
            gap: 0.3rem !important;
        }
        div[data-testid="column"] {
            gap: 0 !important;
        }
        /* 3. Make buttons compact */
        div.stButton > button {
            height: 2.2rem !important; /* Smaller height */
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            font-size: 0.9rem !important;
            margin-top: 5px !important;
        }
        /* 4. Compact Sticky Header */
        .sticky-header {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: white;
            padding: 10px 0;
            border-bottom: 2px solid #f0f2f6;
            margin-bottom: 10px;
        }
        /* 5. Card Styling */
        .compact-card {
            border-bottom: 1px solid #e6e6e6;
            padding-bottom: 8px;
            margin-bottom: 5px;
        }
        .option-title { font-size: 0.95rem; font-weight: 700; margin: 0; color: #31333F; }
        .option-meta { font-size: 0.8rem; color: #666; margin: 0; line-height: 1.2; }
        .badge-green { font-size: 0.75rem; color: #2e7d32; font-weight: 600; background: #edf7ed; padding: 2px 6px; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

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
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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
                str(timestamp), str(st.session_state.session_id),
                str(demographics.get('Gender', '')), str(demographics.get('Age', '')),
                str(demographics.get('Occupation', '')), str(demographics.get('Education', '')),
                str(demographics.get('Household_Size', '')), str(demographics.get('Income', '')),
                str(demographics.get('Urbanization', '')), str(demographics.get('Car_Owner', '')),
                str(demographics.get('Dist_Locker', '')), str(demographics.get('Dist_Pickup', '')),
                str(demographics.get('Dist_Shop', '')), str(demographics.get('Online_Freq', '')),
                str(demographics.get('Categories', '')),
                int(item['Scenario_ID']), str(item['Context']), str(item['Choice'])
            ]
            rows_to_append.append(row)
        sheet.append_rows(rows_to_append)
        return True
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        return False

# --- 3. HELPER FUNCTIONS ---
def submit_answer(choice_label, scenario_id, context_label):
    st.session_state.answers.append({
        "Scenario_ID": int(scenario_id),
        "Context": str(context_label),
        "Choice": str(choice_label)
    })
    st.session_state.current_q += 1

def clean_display_text(text, cart_value):
    if "Add" in str(text):
        try:
            parts = text.split("Add ")
            gap = int(parts[1])
            if gap > (cart_value * 1.5): return text.split(" or")[0]
        except: pass
    return text

def is_true(val):
    return str(val).upper() == "TRUE"

# --- 4. APP LOGIC ---

# A. FILE LOAD
if st.session_state.design_df is None:
    try:
        df = pd.read_csv("shipping_topup_design.csv")
        if 'Context_Cart_Value' in df.columns:
            st.session_state.design_df = df
            st.rerun()
        else:
            st.error("Error: CSV columns missing.")
            st.stop()
    except FileNotFoundError:
        st.error("⚠️ Design file missing!")
        st.stop()

# B. INTRO
if not st.session_state.survey_started:
    st.title("📦 Checkout Experiment")
    st.write("Imagine you are at the **Checkout Page**.")
    st.write("Choose the shipping option that fits you best.")
    if st.button("Start Experiment", type="primary", use_container_width=True):
        st.session_state.survey_started = True
        st.rerun()
    st.stop()

# --- 5. MAIN LOOP ---
df = st.session_state.design_df
q_idx = st.session_state.current_q

# C. DEMOGRAPHICS (Post-Survey)
if q_idx >= len(df):
    if not st.session_state.data_saved:
        st.success("✅ Scenarios Complete!")
        st.write("### Final Step: About You")
        with st.form("demographics_form"):
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Other"])
                age = st.selectbox("Age", ["18-24", "25-34", "35-44", "45-54", "55+"])
                occ = st.selectbox("Occupation", ["Student", "Employed", "Retired", "Other"])
            with col2:
                urban = st.selectbox("Living Area", ["Urban (Center)", "Suburban", "Rural"])
                car = st.radio("Car Owner?", ["Yes", "No"], horizontal=True)
                income = st.selectbox("Income (SEK)", ["<25k", "25k-45k", "45k-65k", ">65k"])
            
            st.markdown("---")
            edu = st.selectbox("Education", ["High School", "Bachelor's", "Master's", "PhD", "Other"])
            hh_size = st.number_input("Household Size", 1, 10, 1)
            dist_locker = st.selectbox("Distance to Locker", ["<500m", "500m-1km", "1-3km", ">3km"])
            dist_pickup = st.selectbox("Distance to Service Point", ["<500m", "500m-1km", "1-3km", ">3km"])
            dist_shop = st.selectbox("Distance to Shop Center", ["<1km", "1-5km", "5-10km", ">10km"])
            
            st.markdown("---")
            freq = st.selectbox("Online Shop Freq", ["Daily", "Weekly", "Monthly", "Rarely"])
            cats = st.multiselect("Categories", ["Fashion", "Electronics", "Kids/Toys", "Groceries", "Home", "Other"])
            
            if st.form_submit_button("Submit & Finish", type="primary", use_container_width=True):
                demographics = {
                    "Gender": gender, "Age": age, "Education": edu, "Occupation": occ,
                    "Household_Size": hh_size, "Income": income, "Urbanization": urban,
                    "Car_Owner": car, "Dist_Locker": dist_locker, "Dist_Pickup": dist_pickup,
                    "Dist_Shop": dist_shop, "Online_Freq": freq, "Categories": ", ".join(cats)
                }
                save_to_google_sheets(st.session_state.answers, demographics)
                st.session_state.data_saved = True
                st.rerun()

    if st.session_state.data_saved:
        st.balloons()
        st.success("🎉 Done! You can close this tab.")
        if st.button("New Session"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

else:
    # E. COMPACT SCENARIOS
    row = df.iloc[q_idx]
    cart_val = row['Context_Cart_Value']
    home_disp = clean_display_text(row['Home_Display'], cart_val)
    
    # Attributes
    home_green = is_true(row['Home_Is_Green']) if 'Home_Is_Green' in df.columns else False
    locker_green = is_true(row['Locker_Is_Green']) if 'Locker_Is_Green' in df.columns else False
    shop_green = is_true(row['Shop_Is_Green']) if 'Shop_Is_Green' in df.columns else False

    # 1. STICKY HEADER (Saves Space)
    st.markdown(f"""
    <div class="sticky-header">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.1rem; font-weight:bold;">🛒 Cart: {cart_val} SEK</span>
            <span style="font-size:0.8rem; color:#888;">{q_idx + 1}/{len(df)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. COMPACT RENDERER (Single HTML Block)
    def render_compact(title, time, display_text, col_key, label_base, context, s_id, green=False, express=False, dist=None):
        # Build the HTML String
        icon = "⚡" if express else ""
        green_html = '<span class="badge-green">🌿 Fossil Free</span>' if green else ""
        dist_html = f"• 📍 {dist}" if dist else ""
        
        # Determine button labels
        pay_btn = None
        topup_btn = None
        
        if " or Add " in display_text:
            pay_txt, add_txt = display_text.split(" or ")
            val = add_txt.replace("Add ", "")
            pay_btn = pay_txt # "Pay 59"
            topup_btn = f"➕ Add {val} (Free Ship)"
        else:
            if "FREE" in display_text.upper():
                pay_btn = f"✅ FREE"
            else:
                pay_btn = f"{display_text}"

        with st.container():
            # Use columns to separate Text (Left) from Buttons (Right)
            # 65% Text / 35% Buttons works well on mobile
            c1, c2 = st.columns([2, 1.2]) 
            
            with c1:
                # Dense HTML Block
                st.markdown(f"""
                <div class="compact-card">
                    <p class="option-title">{icon} {title}</p>
                    <p class="option-meta">⏱️ {time} {dist_html}</p>
                    {green_html}
                </div>
                """, unsafe_allow_html=True)
            
            with c2:
                # Buttons
                if topup_btn:
                    if st.button(topup_btn, key=f"add_{col_key}", type="primary", use_container_width=True):
                        submit_answer(f"{label_base}_TOPUP", s_id, context)
                        st.rerun()
                    if st.button(pay_btn, key=f"pay_{col_key}", use_container_width=True):
                        submit_answer(f"{label_base}_PAID", s_id, context)
                        st.rerun()
                else:
                    # Single Button (Vertical align it to look nice)
                    st.write("") # Spacer
                    btn_type = "secondary"
                    if "FREE" in str(pay_btn): btn_type = "secondary"
                    
                    if st.button(pay_btn, key=f"std_{col_key}", type=btn_type, use_container_width=True):
                        submit_answer(f"{label_base}_FLAT", s_id, context)
                        st.rerun()

    # RENDER ROWS
    render_compact("Standard Home", "2-4 Days", home_disp, f"h_std_{q_idx}", "Home_Standard", row['Context_Label'], row['Scenario_ID'], green=home_green)
    
    render_compact("Express Home", "Next Day", row['Home_Exp_Display'], f"h_exp_{q_idx}", "Home_Express", row['Context_Label'], row['Scenario_ID'], express=True)
    
    l_dist = row['Locker_Distance'] if 'Locker_Distance' in row else None
    render_compact("Parcel Locker", "2-4 Days", row['Locker_Display'], f"l_std_{q_idx}", "Locker_Standard", row['Context_Label'], row['Scenario_ID'], green=locker_green, dist=l_dist)
    
    render_compact("Express Locker", "Next Day", row['Locker_Exp_Display'], f"l_exp_{q_idx}", "Locker_Express", row['Context_Label'], row['Scenario_ID'], express=True, dist=l_dist)
    
    s_dist = row['Shop_Distance'] if 'Shop_Distance' in row else None
    render_compact("Store Collect", "2-4 Days", row['Shop_Display'], f"s_col_{q_idx}", "Shop_Collect", row['Context_Label'], row['Scenario_ID'], green=shop_green, dist=s_dist)
