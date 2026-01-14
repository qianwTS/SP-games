import streamlit as st
import pandas as pd
import random

# ============================================
# 1. SETUP & CONFIGURATION
# ============================================
st.set_page_config(page_title="Checkout - RM Hoodie", layout="wide")

# --- CSS STYLING FOR "ECOMMERCE FEEL" ---
st.markdown("""
<style>
    .main { background-color: #f9f9f9; }
    .product-card {
        background: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center;
    }
    .price-tag { font-size: 24px; font-weight: bold; color: #333; }
    .total-row { border-top: 1px solid #eee; padding-top: 10px; margin-top: 20px; font-weight: bold; }
    .option-card {
        padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 10px;
        background: white; display: flex; justify-content: space-between; align-items: center;
    }
    .option-card:hover { border-color: #2c3e50; background-color: #f8faff; }
    .green-label { color: #27ae60; font-weight: bold; font-size: 0.9em; }
    .co2-text { color: #7f8c8d; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)

# ============================================
# 2. EXPERIMENTAL DATA (The 12 Scenarios)
# ============================================
# We paste the final balanced design here
scenarios = [
    {"id": 1, "h_s": 89, "h_e": 129, "l_d": "2-3 km", "l_s": 0, "l_e": 19, "s_d": "6-8 km", "s_p": 0},
    {"id": 2, "h_s": 59, "h_e": 79, "l_d": "1-2 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 3, "h_s": 29, "h_e": 69, "l_d": "< 1 km", "l_s": 19, "l_e": 29, "s_d": "4-6 km", "s_p": 19},
    {"id": 4, "h_s": 59, "h_e": 99, "l_d": "< 1 km", "l_s": 19, "l_e": 39, "s_d": "2-4 km", "s_p": 0},
    {"id": 5, "h_s": 89, "h_e": 119, "l_d": "1-2 km", "l_s": 29, "l_e": 39, "s_d": "4-6 km", "s_p": 19},
    {"id": 6, "h_s": 29, "h_e": 49, "l_d": "2-3 km", "l_s": 0, "l_e": 29, "s_d": "6-8 km", "s_p": 0},
    {"id": 7, "h_s": 89, "h_e": 119, "l_d": "< 1 km", "l_s": 29, "l_e": 39, "s_d": "4-6 km", "s_p": 29},
    {"id": 8, "h_s": 59, "h_e": 79, "l_d": "2-3 km", "l_s": 19, "l_e": 39, "s_d": "2-4 km", "s_p": 19},
    {"id": 9, "h_s": 29, "h_e": 49, "l_d": "1-2 km", "l_s": 0, "l_e": 29, "s_d": "6-8 km", "s_p": 0},
    {"id": 10, "h_s": 89, "h_e": 109, "l_d": "< 1 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 11, "h_s": 59, "h_e": 79, "l_d": "2-3 km", "l_s": 19, "l_e": 39, "s_d": "6-8 km", "s_p": 19},
    {"id": 12, "h_s": 29, "h_e": 59, "l_d": "1-2 km", "l_s": 0, "l_e": 19, "s_d": "4-6 km", "s_p": 0},
]

# ============================================
# 3. SESSION STATE MANAGEMENT
# ============================================
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
    st.session_state.answers = []
    # Assign a random group if not provided in URL
    query_params = st.query_params
    if "group" in query_params:
        st.session_state.group = query_params["group"]
    else:
        st.session_state.group = random.choice(["control", "label", "co2"])

# ============================================
# 4. HELPER FUNCTIONS FOR NUDGES
# ============================================
def get_nudge_text(mode, group):
    """Returns the subtitle string based on the experimental group"""
    if group == "control":
        return ""
    
    if group == "label":
        # Green Leaf for Lockers and Store
        if mode in ["Locker Std", "Locker Exp", "Store"]:
            return "🌿 Eco Choice"
        return ""
    
    if group == "co2":
        # Specific CO2 values
        if mode == "Home Exp": return "🔴 850g CO2e"
        if mode == "Home Std": return "🟠 300g CO2e"
        if mode in ["Locker Std", "Locker Exp", "Store"]:
            return "🟢 50g CO2e"
            
    return ""

# ============================================
# 5. MAIN APP INTERFACE
# ============================================

# Progress Bar
progress = (st.session_state.current_q / len(scenarios))
st.progress(progress)

if st.session_state.current_q < len(scenarios):
    
    # Get current scenario data
    q_data = scenarios[st.session_state.current_q]
    
    # --- LAYOUT: 2 Columns ---
    col1, col2 = st.columns([1, 2])
    
    # --- LEFT COLUMN: PRODUCT ---
    with col1:
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        # Placeholder image of a hoodie
        st.image("https://via.placeholder.com/300x350.png?text=RM+Pullover+Hoodie", use_column_width=True) 
        st.markdown(f"""
            <h3>RM Pullover Hoodie</h3>
            <p>Size: M | Color: Navy</p>
            <div class="price-tag">499 SEK</div>
            <div class="total-row">Subtotal: 499 SEK</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RIGHT COLUMN: DELIVERY OPTIONS ---
    with col2:
        st.subheader("Select Delivery Method")
        st.markdown("Please choose how you would like to receive your order.")
        
        # Define the 5 options for this specific question
        options_list = [
            {"code": "home_std", "name": "Standard Home", "time": "2-4 days", "dist": "Doorstep", "price": q_data['h_s']},
            {"code": "home_exp", "name": "Express Home", "time": "Next Day", "dist": "Doorstep", "price": q_data['h_e']},
            {"code": "locker_std", "name": "Parcel Locker", "time": "2-4 days", "dist": q_data['l_d'], "price": q_data['l_s']},
            {"code": "locker_exp", "name": "Express Locker", "time": "Next Day", "dist": q_data['l_d'], "price": q_data['l_e']},
            {"code": "store", "name": "Store Collect", "time": "2-4 days", "dist": q_data['s_d'], "price": q_data['s_p']},
        ]
        
        # Build the formatting for the Radio Button
        # We use a helper dict to store the full object to retrieve later
        radio_options = []
        option_map = {}
        
        for opt in options_list:
            nudge = get_nudge_text(opt['name'], st.session_state.group)
            
            # Formatting the Price String
            price_str = "FREE" if opt['price'] == 0 else f"{opt['price']} SEK"
            
            # Formatting the Label (What the user sees)
            # We use Markdown-like spacing to align things somewhat
            label = f"**{opt['name']}** |  {opt['time']}  |  {opt['dist']}  |  **{price_str}**"
            if nudge:
                label += f"  \n_{nudge}_" # Add nudge on new line
                
            radio_options.append(label)
            option_map[label] = opt

        # RENDER THE SELECTION
        choice_label = st.radio(
            "Available Options:",
            radio_options,
            label_visibility="collapsed",
            key=f"q_{st.session_state.current_q}"
        )

        st.markdown("---")
        
        # Confirm Button
        if st.button("Confirm & Continue >", type="primary"):
            # Save Data
            selected_opt = option_map[choice_label]
            st.session_state.answers.append({
                "scenario_id": q_data['id'],
                "group": st.session_state.group,
                "choice": selected_opt['name'],
                "choice_price": selected_opt['price'],
                "choice_dist": selected_opt['dist']
            })
            
            # Move to next question
            st.session_state.current_q += 1
            st.rerun()

else:
    # --- END SCREEN ---
    st.balloons()
    st.success("Thank you! The survey is complete.")
    
    # Convert results to DataFrame for download
    df_results = pd.DataFrame(st.session_state.answers)
    st.write("### Your Data (Debug View)")
    st.dataframe(df_results)
    
    # Download Button
    csv = df_results.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "survey_results.csv", "text/csv")
