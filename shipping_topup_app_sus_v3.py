import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Checkout Survey", layout="centered")

# Initialize Session State
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'design_df' not in st.session_state:
    st.session_state.design_df = None
if 'survey_started' not in st.session_state:
    st.session_state.survey_started = False

# --- 2. HELPER FUNCTIONS ---
def submit_answer(choice_label, scenario_id, context_label):
    st.session_state.answers.append({
        "Scenario_ID": scenario_id,
        "Context": context_label,
        "Choice": choice_label
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

# --- 3. APP LOGIC ---

# A. FILE UPLOAD & SETUP (Runs first)
if st.session_state.design_df is None:
    st.title("🛍️ Setup Experiment")
    st.info("Please upload the 'shipping_topup_design.csv' file.")
    uploaded_file = st.file_uploader("Upload Design CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if 'Context_Cart_Value' in df.columns:
                st.session_state.design_df = df
                st.rerun()
            else:
                st.error("CSV format incorrect.")
        except Exception as e:
            st.error(f"Error: {e}")
            
    # Demo Data Logic
    if st.checkbox("Or use Demo Data"):
        data = {
            'Scenario_ID': [1, 2],
            'Context_Cart_Value': [240, 750],
            'Context_Label': ['Small Basket', 'Big Basket'],
            'Home_Display': ['Pay 59 or Add 559', 'Pay 59 or Add 149'],
            'Home_Exp_Display': ['Pay 129', 'Pay 129'],
            'Locker_Display': ['FREE', 'FREE'],
            'Locker_Exp_Display': ['Pay 49', 'Pay 49'],
            'Shop_Display': ['Pay 19 or Add 9', 'FREE'],
            'Home_Is_Green': [True, False],
            'Locker_Is_Green': [False, True],
            'Locker_Distance': ['<1 km', '1-2 km'],
            'Shop_Distance': ['2-4 km', '4-6 km']
        }
        st.session_state.design_df = pd.DataFrame(data)
        st.rerun()
    st.stop()

# B. INTRODUCTION PAGE (Runs before survey starts)
if not st.session_state.survey_started:
    st.title("📦 Welcome to the Survey")
    st.markdown("""
    ### Imagine you are shopping online...
    
    You have finished adding items to your cart and are now at the **Checkout Page**.
    
    In the following screens, you will see different **Shipping Options** (Home Delivery, Lockers, etc.).
    Your goal is to choose the option that fits you best.
    
    **Look out for:**
    * **💰 Shipping Cost:** Some options are free, some cost money.
    * **➕ Top-Up Offers:** Sometimes, buying a little more (e.g., adding socks) makes shipping **FREE**.
    * **🌿 Sustainability:** Some options are Fossil Free.
    
    The survey will take about **2 minutes**.
    """)
    
    if st.button("Start Checkout Experiment", type="primary"):
        st.session_state.survey_started = True
        st.rerun()
    st.stop()

# --- 4. MAIN SURVEY INTERFACE ---
df = st.session_state.design_df
q_idx = st.session_state.current_q

if q_idx >= len(df):
    st.balloons()
    st.success("✅ Survey Complete!")
    st.write("Thank you for your participation.")
    
    results_df = pd.DataFrame(st.session_state.answers)
    # st.dataframe(results_df) # Optional: Hide table if you don't want users to see it
    
    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download My Responses", csv, "results.csv", "text/csv")
    
    if st.button("Restart"):
        st.session_state.current_q = 0
        st.session_state.answers = []
        st.session_state.survey_started = False
        st.rerun()
else:
    # Top Navigation
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
    
    # Attributes
    home_is_green = row['Home_Is_Green'] if 'Home_Is_Green' in row else False
    locker_is_green = row['Locker_Is_Green'] if 'Locker_Is_Green' in row else False

    # Sticky Header
    st.markdown(f"""
    <div style="background-color:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px; border: 1px solid #ddd;">
        <h3 style="margin:0; color:#333;">🛒 Cart Total: <b>{cart_val} SEK</b></h3>
        <p style="margin:0; color:#666;">Select your preferred delivery method below.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- RENDER FUNCTION (HIGH VISIBILITY) ---
    def render_option_row(title, subtitle, display_text, col_key, label_base, context_label, scenario_id, 
                          is_green=False, is_express=False, distance=None):
        with st.container():
            c1, c2 = st.columns([1.6, 1])
            
            # --- LEFT: INFO (Bold & Clear) ---
            with c1:
                # 1. Title (Larger)
                if is_express:
                    st.markdown(f"#### ⚡ {title}")
                else:
                    st.markdown(f"#### {title}")
                
                # 2. Details (Bold)
                details = f"**⏱️ {subtitle}**"
                if distance:
                    details += f" &nbsp;•&nbsp; **📍 {distance}**"
                
                st.markdown(details, unsafe_allow_html=True)
                
                # 3. Green Badge
                if is_green:
                    st.markdown("🌿 <span style='color:#2e7d32; font-weight:bold;'>Fossil Free Delivery</span>", unsafe_allow_html=True)

            # --- RIGHT: BUTTONS (Explicit Actions) ---
            with c2:
                # Add spacing to align buttons with text better
                st.write("") 
                
                if " or Add " in display_text:
                    pay_text, add_text = display_text.split(" or ")
                    val_only = add_text.replace("Add ", "")
                    
                    # TOP-UP BUTTON: Very Explicit
                    # Uses \n for line break to make it fit better if needed, or just clear text
                    btn_label = f"➕ Add {val_only} SEK\nGet FREE Delivery"
                    
                    if st.button(btn_label, key=f"btn_add_{col_key}", use_container_width=True):
                        submit_answer(f"{label_base}_TOPUP", scenario_id, context_label)
                        st.rerun()
                    
                    # PAY BUTTON
                    if st.button(f"Pay {pay_text}", key=f"btn_pay_{col_key}", use_container_width=True):
                        submit_answer(f"{label_base}_PAID", scenario_id, context_label)
                        st.rerun()

                else:
                    # STANDARD BUTTONS
                    if "FREE" in display_text.upper():
                        btn_label = f"✅ FREE Shipping" # Clear confirmation
                        style_type = "secondary"
                    else:
                        btn_label = f"Pay {display_text}" # Explicit "Pay"
                        style_type = "secondary"
                    
                    if st.button(btn_label, key=f"btn_std_{col_key}", type=style_type, use_container_width=True):
                        submit_answer(f"{label_base}_FLAT", scenario_id, context_label)
                        st.rerun()
            
            st.divider()

    # --- RENDER ROWS ---
    
    # 1. HOME STANDARD
    render_option_row(
        "Standard Home", "2-4 Days", home_disp, f"h_std_{q_idx}", 
        "Home_Standard", row['Context_Label'], row['Scenario_ID'], 
        is_green=home_is_green
    )

    # 2. HOME EXPRESS
    render_option_row(
        "Express Home", "Next Day", row['Home_Exp_Display'], f"h_exp_{q_idx}", 
        "Home_Express", row['Context_Label'], row['Scenario_ID'], 
        is_express=True
    )

    # 3. LOCKER STANDARD
    locker_dist = row['Locker_Distance'] if 'Locker_Distance' in row else None
    render_option_row(
        "Parcel Locker", "2-4 Days", row['Locker_Display'], f"l_std_{q_idx}", 
        "Locker_Standard", row['Context_Label'], row['Scenario_ID'], 
        is_green=locker_is_green,
        distance=locker_dist
    )

    # 4. LOCKER EXPRESS
    render_option_row(
        "Express Locker", "Next Day", row['Locker_Exp_Display'], f"l_exp_{q_idx}", 
        "Locker_Express", row['Context_Label'], row['Scenario_ID'], 
        is_express=True,
        distance=locker_dist
    )

    # 5. STORE COLLECT
    shop_dist = row['Shop_Distance'] if 'Shop_Distance' in row else None
    render_option_row(
        "Store Collect", "2-4 Days", row['Shop_Display'], f"s_col_{q_idx}", 
        "Shop_Collect", row['Context_Label'], row['Scenario_ID'],
        distance=shop_dist
    )
