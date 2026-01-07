import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Checkout Survey", layout="centered", initial_sidebar_state="collapsed")

# --- CSS FOR COMPACT & CLEAR MOBILE UI ---
st.markdown("""
    <style>
        /* 1. Global Spacing Fixes */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* 2. STICKY CART HEADER */
        /* This keeps the cart value pinned to the top */
        .sticky-header {
            position: fixed;
            top: 40px; /* Adjust based on Streamlit header height */
            left: 0;
            right: 0;
            background-color: #ffffff;
            padding: 10px;
            z-index: 9999;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            border-bottom: 2px solid #4CAF50;
            text-align: center;
            max-width: 700px; /* Match centered layout */
            margin: 0 auto; 
        }
        .cart-total { font-size: 1.2rem; font-weight: 800; color: #111; margin: 0; }
        .cart-count { font-size: 0.8rem; color: #666; margin: 0; }
        
        /* Spacer to prevent content from hiding behind sticky header */
        .header-spacer { height: 80px; }

        /* 3. OPTION ROW STYLING */
        .option-row {
            border-bottom: 1px solid #f0f0f0;
            padding: 8px 0;
            margin-bottom: 0px;
        }
        
        /* 4. TYPOGRAPHY */
        .opt-title { font-size: 0.95rem; font-weight: 700; color: #000; line-height: 1.2; }
        .opt-meta  { font-size: 0.8rem; color: #555; margin-top: 2px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;}
        
        /* 5. BADGES */
        .badge-green {
            background-color: #e8f5e9;
            color: #1b5e20;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 1px 6px;
            border-radius: 4px;
            border: 1px solid #c8e6c9;
        }
        .badge-dist {
            background-color: #f5f5f5;
            color: #444;
            font-size: 0.7rem;
            padding: 1px 6px;
            border-radius: 4px;
        }

        /* 6. BUTTON COLOR OVERRIDE */
        /* Forces the "Primary" button to be Green/Teal instead of Red */
        button[kind="primary"] {
            background-color: #2e7d32 !important; /* Green */
            border-color: #2e7d32 !important;
            color: white !important;
        }
        button[kind="primary"]:hover {
            background-color: #1b5e20 !important;
            border-color: #1b5e20 !important;
        }
        /* Make buttons slightly smaller vertically */
        div.stButton > button {
            padding: 0.25rem 0.5rem;
            line-height: 1.2;
            min-height: 0px;
            height: auto;
        }
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
        
        rows = []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in answers:
            row = [
                ts, str(st.session_state.session_id),
                str(demographics.get('Gender', '')), str(demographics.get('Age', '')),
                str(demographics.get('Occupation', '')), str(demographics.get('Education', '')),
                str(demographics.get('Household_Size', '')), str(demographics.get('Income', '')),
                str(demographics.get('Urbanization', '')), str(demographics.get('Car_Owner', '')),
                str(demographics.get('Dist_Locker', '')), str(demographics.get('Dist_Pickup', '')),
                str(demographics.get('Dist_Shop', '')), str(demographics.get('Online_Freq', '')),
                str(demographics.get('Categories', '')),
                int(item['Scenario_ID']), str(item['Context']), str(item['Choice'])
            ]
            rows.append(row)
        sheet.append_rows(rows)
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
            # Only show "Add" option if the gap is reasonable
            if gap > (cart_value * 1.5): return text.split(" or")[0]
        except: pass
    return text

def is_true(val):
    return str(val).upper() == "TRUE"

# --- 4. APP LOGIC ---

# A. LOAD FILE
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
        st.error("⚠️ Design file missing!")
        st.stop()

# B. INTRO
if not st.session_state.survey_started:
    st.title("📦 Checkout Experiment")
    st.info("Imagine you are finalizing your online order.")
    st.markdown("**Instructions:**\n* Choose the shipping method you would actually use.\n* The survey takes 2-3 minutes.")
    
    if st.button("Start Now", type="primary", use_container_width=True):
        st.session_state.survey_started = True
        st.rerun()
    st.stop()

# --- 5. MAIN LOOP ---
df = st.session_state.design_df
q_idx = st.session_state.current_q

# C. DEMOGRAPHICS (At End)
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
                urban = st.selectbox("Living Area", ["Urban (Center)", "Suburban", "Rural"])
            with col2:
                car = st.radio("Car Owner?", ["Yes", "No"], horizontal=True)
                income = st.selectbox("Income (SEK)", ["<25k", "25k-45k", "45k-65k", ">65k"])
                hh_size = st.number_input("Household Size", 1, 10, 1)
                edu = st.selectbox("Education", ["High School", "Bachelor's", "Master's", "PhD", "Other"])
            
            st.markdown("---")
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
        st.success("🎉 Done! Thank you.")
        if st.button("New Session"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

else:
    # E. SCENARIO RENDERER
    row = df.iloc[q_idx]
    cart_val = row['Context_Cart_Value']
    home_disp = clean_display_text(row['Home_Display'], cart_val)
    
    # Attributes
    home_green = is_true(row['Home_Is_Green']) if 'Home_Is_Green' in df.columns else False
    locker_green = is_true(row['Locker_Is_Green']) if 'Locker_Is_Green' in df.columns else False
    shop_green = is_true(row['Shop_Is_Green']) if 'Shop_Is_Green' in df.columns else False

    # 1. VISIBLE STICKY CART BANNER
    st.markdown(f"""
    <div class="sticky-header">
        <p class="cart-total">Cart Total: {cart_val} SEK</p>
        <p class="cart-count">Scenario {q_idx + 1}/{len(df)}</p>
    </div>
    <div class="header-spacer"></div>
    """, unsafe_allow_html=True)

    # 2. CLEAR COMPACT RENDERER
    def render_compact(title, time, display_text, col_key, label_base, context, s_id, green=False, express=False, dist=None):
        
        # Build Metadata HTML
        icon = "⚡" if express else ""
        meta_html = f"<span>⏱️ {time}</span>"
        if dist: meta_html += f" <span class='badge-dist'>📍 {dist}</span>"
        if green: meta_html += f" <span class='badge-green'>🌿 Fossil Free</span>"
        
        # Parse Buttons
        pay_btn = None
        topup_btn = None
        
        if " or Add " in display_text:
            pay_txt, add_txt = display_text.split(" or ")
            val = add_txt.replace("Add ", "")
            pay_btn = pay_txt 
            topup_btn = f"+ Add {val} (Free)" # Simplified Text
        else:
            pay_btn = f"✅ FREE" if "FREE" in display_text.upper() else f"{display_text}"

        with st.container():
            st.markdown('<div class="option-row">', unsafe_allow_html=True)
            # Use columns for layout: Left is Text, Right is Button(s)
            c1, c2 = st.columns([1.6, 1]) 
            
            with c1:
                st.markdown(f"""
                    <div class="opt-title">{icon} {title}</div>
                    <div class="opt-meta">{meta_html}</div>
                """, unsafe_allow_html=True)
            
            with c2:
                if topup_btn:
                    # TOPUP button (Type=Primary -> CSS turns it Green)
                    if st.button(topup_btn, key=f"add_{col_key}", type="primary", use_container_width=True):
                        submit_answer(f"{label_base}_TOPUP", s_id, context)
                        st.rerun()
                    # Pay button (Type=Secondary -> Grey/White)
                    if st.button(pay_btn, key=f"pay_{col_key}", type="secondary", use_container_width=True):
                        submit_answer(f"{label_base}_PAID", s_id, context)
                        st.rerun()
                else:
                    # Single Button
                    btn_type = "secondary" # Always grey/white unless it's a special action
                    if st.button(pay_btn, key=f"std_{col_key}", type=btn_type, use_container_width=True):
                        submit_answer(f"{label_base}_FLAT", s_id, context)
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

    # RENDER ALL OPTIONS
    render_compact("Standard Home", "2-4 Days", home_disp, f"h_std_{q_idx}", "Home_Standard", row['Context_Label'], row['Scenario_ID'], green=home_green)
    
    render_compact("Express Home", "Next Day", row['Home_Exp_Display'], f"h_exp_{q_idx}", "Home_Express", row['Context_Label'], row['Scenario_ID'], express=True)
    
    l_dist = row['Locker_Distance'] if 'Locker_Distance' in row else None
    render_compact("Parcel Locker", "2-4 Days", row['Locker_Display'], f"l_std_{q_idx}", "Locker_Standard", row['Context_Label'], row['Scenario_ID'], green=locker_green, dist=l_dist)
    
    render_compact("Express Locker", "Next Day", row['Locker_Exp_Display'], f"l_exp_{q_idx}", "Locker_Express", row['Context_Label'], row['Scenario_ID'], express=True, dist=l_dist)
    
    s_dist = row['Shop_Distance'] if 'Shop_Distance' in row else None
    render_compact("Store Collect", "2-4 Days", row['Shop_Display'], f"s_col_{q_idx}", "Shop_Collect", row['Context_Label'], row['Scenario_ID'], green=shop_green, dist=s_dist)
