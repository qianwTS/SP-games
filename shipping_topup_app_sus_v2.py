import streamlit as st
import pandas as pd

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(page_title="Checkout Survey", layout="centered")

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

# --- 3. APP HEADER & UPLOAD ---
st.title("🛍️ Checkout Experiment")

if st.session_state.design_df is None:
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
            'Locker_Is_Green': [False, True]
        }
        st.session_state.design_df = pd.DataFrame(data)
        st.rerun()
    st.stop()

# --- 4. SURVEY INTERFACE ---
df = st.session_state.design_df
q_idx = st.session_state.current_q

if q_idx >= len(df):
    st.balloons()
    st.success("✅ Survey Complete!")
    results_df = pd.DataFrame(st.session_state.answers)
    st.dataframe(results_df)
    csv = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results", csv, "results.csv", "text/csv")
    if st.button("Restart"):
        st.session_state.current_q = 0
        st.session_state.answers = []
        st.rerun()
else:
    if q_idx > 0:
        if st.button("⬅️ Back"):
            go_back()
            st.rerun()

    row = df.iloc[q_idx]
    cart_val = row['Context_Cart_Value']
    home_disp = clean_display_text(row['Home_Display'], cart_val)
    
    # Attributes
    home_is_green = row['Home_Is_Green'] if 'Home_Is_Green' in row else False
    locker_is_green = row['Locker_Is_Green'] if 'Locker_Is_Green' in row else False

    st.progress((q_idx) / len(df))
    st.caption(f"Question {q_idx + 1} of {len(df)}")

    st.markdown(f"""
    <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:20px;">
        <h3 style="margin:0; color:#31333F;">🛒 Cart Total: {cart_val} SEK</h3>
    </div>
    """, unsafe_allow_html=True)

    # --- NEW RENDER FUNCTION (One Row Layout) ---
    def render_option_row(title, subtitle, display_text, col_key, label_base, context_label, scenario_id, is_green=False, is_express=False):
        """
        Renders a single delivery option as one row:
        [Text Info]  ---  [Button(s)]
        """
        # Create a container for visual separation
        with st.container():
            # Create two columns: Left (Text) gets 3 parts, Right (Buttons) gets 2 parts
            c1, c2 = st.columns([1.5, 1])
            
            # --- LEFT COLUMN: INFO ---
            with c1:
                # Title styling based on type
                if is_express:
                    st.markdown(f"**{title}** ⚡")
                else:
                    st.markdown(f"**{title}**")
                
                st.caption(subtitle)
                
                # Green Badge
                if is_green:
                    st.markdown("🌿 <span style='color:green; font-weight:bold; font-size:0.9em;'>Fossil Free</span>", unsafe_allow_html=True)

            # --- RIGHT COLUMN: BUTTONS ---
            with c2:
                # 1. Split Button Logic (Pay vs Top-up)
                if " or Add " in display_text:
                    pay_text, add_text = display_text.split(" or ")
                    val_only = add_text.replace("Add ", "")
                    
                    # Top-Up Button (Primary Action)
                    if st.button(f"➕ {val_only} (to 🛒)", key=f"btn_add_{col_key}", type="primary", use_container_width=True):
                        submit_answer(f"{label_base}_TOPUP", scenario_id, context_label)
                        st.rerun()
                    
                    # Pay Button (Secondary Action - below Top-up to save width, or use nested columns)
                    if st.button(f"💰 {pay_text}", key=f"btn_pay_{col_key}", use_container_width=True):
                        submit_answer(f"{label_base}_PAID", scenario_id, context_label)
                        st.rerun()

                # 2. Standard Logic
                else:
                    if "FREE" in display_text.upper():
                        btn_label = f"✅ {display_text}"
                        style_type = "secondary" # Or primary if you want free to pop
                    else:
                        btn_label = f"💰 {display_text}"
                        style_type = "secondary"
                    
                    if st.button(btn_label, key=f"btn_std_{col_key}", type=style_type, use_container_width=True):
                        submit_answer(f"{label_base}_FLAT", scenario_id, context_label)
                        st.rerun()
            
            st.divider() # Adds a nice line between rows

    # --- RENDER THE ROWS ---
    
    st.subheader("Choose Shipping Method")
    
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
    render_option_row(
        "Parcel Locker", "2-4 Days", row['Locker_Display'], f"l_std_{q_idx}", 
        "Locker_Standard", row['Context_Label'], row['Scenario_ID'], 
        is_green=locker_is_green
    )

    # 4. LOCKER EXPRESS
    render_option_row(
        "Express Locker", "Next Day", row['Locker_Exp_Display'], f"l_exp_{q_idx}", 
        "Locker_Express", row['Context_Label'], row['Scenario_ID'], 
        is_express=True
    )

    # 5. STORE COLLECT
    render_option_row(
        "Store Collect", "2-4 Days", row['Shop_Display'], f"s_col_{q_idx}", 
        "Shop_Collect", row['Context_Label'], row['Scenario_ID']
    )
