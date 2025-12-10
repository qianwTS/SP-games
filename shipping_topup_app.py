import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION & STATE ---
# changed layout="centered" to make the single column look like a mobile app
st.set_page_config(page_title="Checkout Survey", layout="centered") 

# Initialize Session State
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'design_df' not in st.session_state:
    st.session_state.design_df = None

# --- 2. HELPER FUNCTIONS ---
def submit_answer(choice_label, scenario_id, context_label):
    st.session_state.answers.append({
        "Scenario_ID": scenario_id,
        "Context": context_label,
        "Choice": choice_label
    })
    st.session_state.current_q += 1

def go_back():
    """Removes the last answer and goes back one step."""
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

# --- 3. APP HEADER & FILE UPLOAD ---
st.title("🛍️ Checkout Experiment")

if st.session_state.design_df is None:
    st.info("Please upload the 'shipping_topup_design.csv' file.")
    uploaded_file = st.file_uploader("Upload Design CSV", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = ['Context_Cart_Value', 'Home_Display', 'Locker_Display']
            if all(col in df.columns for col in required_cols):
                st.session_state.design_df = df
                st.rerun()
            else:
                st.error("Error: CSV is missing required columns.")
        except Exception as e:
            st.error(f"Error loading file: {e}")
            
    if st.checkbox("Or use Demo Data (for testing)"):
        data = {
            'Scenario_ID': [1, 2],
            'Context_Cart_Value': [240, 750],
            'Context_Label': ['Small Basket (240kr)', 'Big Basket (750kr)'],
            'Home_Display': ['Pay 59 or Add 559', 'Pay 59 or Add 149'],
            'Home_Exp_Display': ['Pay 129', 'Pay 129'],
            'Locker_Display': ['FREE', 'FREE'],
            'Locker_Exp_Display': ['Pay 49', 'Pay 49'],
            'Shop_Display': ['Pay 19 or Add 9', 'FREE']
        }
        st.session_state.design_df = pd.DataFrame(data)
        st.rerun()

    st.stop()

# --- 4. THE SURVEY INTERFACE ---
df = st.session_state.design_df
q_idx = st.session_state.current_q

# CHECK: Are we done?
if q_idx >= len(df):
    st.balloons()
    st.success("✅ Survey Complete! Thank you.")
    
    results_df = pd.DataFrame(st.session_state.answers)
    st.dataframe(results_df)
    
    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results", csv, "survey_results.csv", "text/csv")
    
    if st.button("Start Over"):
        st.session_state.current_q = 0
        st.session_state.answers = []
        st.rerun()

else:
    # --- NAVIGATION (BACK BUTTON) ---
    if q_idx > 0:
        if st.button("⬅️ Back"):
            go_back()
            st.rerun()

    # GET CURRENT SCENARIO
    row = df.iloc[q_idx]
    cart_val = row['Context_Cart_Value']
    home_disp = clean_display_text(row['Home_Display'], cart_val)
    
    # Progress
    st.progress((q_idx) / len(df))
    st.caption(f"Question {q_idx + 1} of {len(df)}")

    # CONTEXT HEADER
    st.markdown(f"""
    <div style="background-color:#e8f4f8; padding:20px; border-radius:10px; margin-bottom:25px; border-left: 5px solid #0099cc;">
        <h3 style="margin:0; color:#005f80;">🛒 Cart Total: {cart_val} SEK</h3>
        <p style="margin:0; color:#555;">Select your shipping method.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- BUTTON RENDERER ---
    def render_split_choice(label_base, display_text, col_key, context_label, scenario_id):
        if " or Add " in display_text:
            pay_text, add_text = display_text.split(" or ")
            
            # Use columns to put Pay vs TopUp side-by-side inside the card
            # This makes the decision clearer even in a vertical list
            b1, b2 = st.columns([1, 1.5]) 
            
            with b1:
                if st.button(f"💰 {pay_text}", key=f"btn_pay_{col_key}", use_container_width=True):
                    submit_answer(f"{label_base}_PAID", scenario_id, context_label)
                    st.rerun()
            
            with b2:
                val_only = add_text.replace("Add ", "")
                if st.button(f"➕ {val_only} (to 🛒 for Free Ship)", key=f"btn_add_{col_key}", type="primary", use_container_width=True):
                    submit_answer(f"{label_base}_TOPUP", scenario_id, context_label)
                    st.rerun()
                
        else:
            if "FREE" in display_text.upper():
                btn_label = f"✅ {display_text}"
            else:
                btn_label = f"💰 {display_text}"
            
            if st.button(btn_label, key=f"btn_std_{col_key}", use_container_width=True):
                submit_answer(f"{label_base}_FLAT", scenario_id, context_label)
                st.rerun()

    # --- LIST LAYOUT (VERTICAL STACK) ---
    
    # 1. HOME DELIVERY SECTION
    st.subheader("🏠 Home Delivery")
    
    st.info("**Standard Home** (2-4 Days)")
    render_split_choice("Home_Standard", home_disp, f"h_std_{q_idx}", row['Context_Label'], row['Scenario_ID'])
    
    st.write("") # Spacer

    st.warning("**Express Home** (Next Day)")
    render_split_choice("Home_Express", row['Home_Exp_Display'], f"h_exp_{q_idx}", row['Context_Label'], row['Scenario_ID'])

    st.markdown("---")

    # 2. LOCKER SECTION
    st.subheader("📦 Parcel Lockers")

    st.success("**Standard Locker** (2-4 Days)")
    render_split_choice("Locker_Standard", row['Locker_Display'], f"l_std_{q_idx}", row['Context_Label'], row['Scenario_ID'])

    st.write("") # Spacer

    st.warning("**Express Locker** (Next Day)")
    render_split_choice("Locker_Express", row['Locker_Exp_Display'], f"l_exp_{q_idx}", row['Context_Label'], row['Scenario_ID'])
            
    st.markdown("---")

    # 3. STORE SECTION
    st.subheader("🏬 Pick Up In-Store")
    
    st.info("**Store Collect** (2-4 Days)")
    render_split_choice("Shop_Collect", row['Shop_Display'], f"s_col_{q_idx}", row['Context_Label'], row['Scenario_ID'])
