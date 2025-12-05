import streamlit as st
import pandas as pd
import uuid
import random

# --- FIXED EXPERIMENTAL DESIGN (16 EFFICIENT PROFILES) ---
# These are the 16 rows selected using D-Efficiency criteria.
FIXED_DESIGN = [
    {"Location": "Home Delivery",   "Speed": "Standard (2-4 days)", "Threshold": "None",             "Price": 69},
    {"Location": "Collect at Shop", "Speed": "Standard (2-4 days)", "Threshold": "Free at ≥699 SEK", "Price": 49},
    {"Location": "Service Point",   "Speed": "Express (Next Day)",  "Threshold": "None",             "Price": 99},
    {"Location": "Service Point",   "Speed": "Express (Next Day)",  "Threshold": "None",             "Price": 0},
    {"Location": "Collect at Shop", "Speed": "Express (Next Day)",  "Threshold": "Free at ≥399 SEK", "Price": 69},
    {"Location": "Service Point",   "Speed": "Standard (2-4 days)", "Threshold": "None",             "Price": 49},
    {"Location": "Home Delivery",   "Speed": "Express (Next Day)",  "Threshold": "Free at ≥699 SEK", "Price": 69},
    {"Location": "Collect at Shop", "Speed": "Standard (2-4 days)", "Threshold": "None",             "Price": 99},
    {"Location": "Service Point",   "Speed": "Standard (2-4 days)", "Threshold": "Free at ≥399 SEK", "Price": 99},
    {"Location": "Collect at Shop", "Speed": "Express (Next Day)",  "Threshold": "Free at ≥699 SEK", "Price": 0},
    {"Location": "Home Delivery",   "Speed": "Standard (2-4 days)", "Threshold": "Free at ≥399 SEK", "Price": 0},
    {"Location": "Collect at Shop", "Speed": "Standard (2-4 days)", "Threshold": "Free at ≥399 SEK", "Price": 49},
    {"Location": "Service Point",   "Speed": "Standard (2-4 days)", "Threshold": "Free at ≥699 SEK", "Price": 69},
    {"Location": "Home Delivery",   "Speed": "Express (Next Day)",  "Threshold": "Free at ≥399 SEK", "Price": 49},
    {"Location": "Home Delivery",   "Speed": "Express (Next Day)",  "Threshold": "None",             "Price": 99},
    {"Location": "Home Delivery",   "Speed": "Standard (2-4 days)", "Threshold": "Free at ≥699 SEK", "Price": 0},
]

SCENARIO_TEXT = """
**Imagine you are buying a pair of sneakers online for 500 SEK.**
You are at the checkout. Please look at the options below and choose 
the delivery method you would actually pay for in real life.
"""

def initialize_session():
    """Sets up the user's session variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
        
        # Shuffle the design so every user sees pairs in a different order
        # We work with a copy to avoid messing up the global constant
        design_copy = FIXED_DESIGN.copy()
        random.shuffle(design_copy)
        st.session_state.user_design = design_copy
        
    if 'data' not in st.session_state:
        st.session_state.data = []
    if 'round' not in st.session_state:
        st.session_state.round = 0 # Start at 0 index

def get_current_options():
    """Gets the next 2 profiles from the shuffled user_design list."""
    # Index for Option A is round * 2
    # Index for Option B is round * 2 + 1
    idx = st.session_state.round * 2
    
    # Check if we have run out of designs (8 rounds x 2 profiles = 16)
    if idx >= len(st.session_state.user_design):
        return None, None
        
    opt_a = st.session_state.user_design[idx]
    opt_b = st.session_state.user_design[idx+1]
    return opt_a, opt_b

def save_choice(choice_label, options):
    """Saves the user's choice and the attributes."""
    row = {
        "user_id": st.session_state.user_id,
        "round_number": st.session_state.round + 1,
        "choice": choice_label,
        # Option A Attributes
        "optA_loc": options[0]["Location"],
        "optA_spd": options[0]["Speed"],
        "optA_thr": options[0]["Threshold"],
        "optA_prc": options[0]["Price"],
        # Option B Attributes
        "optB_loc": options[1]["Location"],
        "optB_spd": options[1]["Speed"],
        "optB_thr": options[1]["Threshold"],
        "optB_prc": options[1]["Price"],
    }
    st.session_state.data.append(row)
    st.session_state.round += 1

# --- UI LAYOUT ---
st.set_page_config(page_title="Delivery Choice Experiment", layout="wide")

initialize_session()

st.title("🛒 Delivery Choice Game")
st.markdown(SCENARIO_TEXT)

# Logic to check if game is finished
opt_a, opt_b = get_current_options()

if opt_a:
    # Game in progress
    progress = (st.session_state.round) / 8 # 8 rounds total
    st.progress(progress)
    st.write(f"Question {st.session_state.round + 1} of 8")

    col1, col2, col3 = st.columns([1, 1, 0.5])

    # OPTION A CARD
    with col1:
        st.info("### Option A")
        st.metric(label="Price", value=f"{opt_a['Price']} SEK")
        st.write(f"**Location:** {opt_a['Location']}")
        st.write(f"**Speed:** {opt_a['Speed']}")
        st.write(f"**Free Ship Rule:** {opt_a['Threshold']}")
        if st.button("Choose Option A", use_container_width=True):
            save_choice("A", [opt_a, opt_b])
            st.rerun()

    # OPTION B CARD
    with col2:
        st.success("### Option B")
        st.metric(label="Price", value=f"{opt_b['Price']} SEK")
        st.write(f"**Location:** {opt_b['Location']}")
        st.write(f"**Speed:** {opt_b['Speed']}")
        st.write(f"**Free Ship Rule:** {opt_b['Threshold']}")
        if st.button("Choose Option B", use_container_width=True):
            save_choice("B", [opt_a, opt_b])
            st.rerun()

    # OPTION NONE
    with col3:
        st.warning("### None")
        st.write("I would not choose either.")
        st.write("- Cancel Purchase")
        st.write(" ") 
        st.write(" ") 
        if st.button("Choose None", use_container_width=True):
            save_choice("None", [opt_a, opt_b])
            st.rerun()

else:
    # Game Finished
    st.progress(1.0)
    st.balloons()
    st.success("## Thank you! You have completed the survey.")
    
    # --- ADMIN / DATA DOWNLOAD ---
    st.write("Please download your response data below:")
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download CSV",
            csv,
            "experiment_data.csv",
            "text/csv",
            key='download-csv'
        )
