import streamlit as st
import pandas as pd
import random
import uuid

# --- CONFIGURATION (EDIT THIS SECTION TO CHANGE YOUR GAME) ---
# You can change these lists to update the options in your game
ATTRIBUTES = {
    "location": ["Home Delivery", "Service Point", "Collect at Shop"],
    "speed": ["Standard (2-4 days)", "Express (Next Day)"],
    "threshold": ["None", "Free at ≥399 SEK", "Free at ≥699 SEK"],
    "price": [0, 49, 69, 99]
}

SCENARIO_TEXT = """
**Imagine you are buying a pair of sneakers online for 500 SEK.**
You are at the checkout. Please look at the options below and choose 
the delivery method you would actually pay for in real life.
"""

# --- APP LOGIC ---

def generate_option():
    """Generates a random product profile based on attributes."""
    return {
        "Location": random.choice(ATTRIBUTES["location"]),
        "Speed": random.choice(ATTRIBUTES["speed"]),
        "Threshold": random.choice(ATTRIBUTES["threshold"]),
        "Price": random.choice(ATTRIBUTES["price"])
    }

def initialize_session():
    """Sets up the user's session variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'data' not in st.session_state:
        st.session_state.data = []
    if 'round' not in st.session_state:
        st.session_state.round = 1
    if 'current_options' not in st.session_state:
        st.session_state.current_options = [generate_option(), generate_option()]

def save_choice(choice_label, options):
    """Saves the user's choice and the attributes of what they saw."""
    row = {
        "user_id": st.session_state.user_id,
        "round": st.session_state.round,
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
    # Generate new options for the next round
    st.session_state.current_options = [generate_option(), generate_option()]

# --- UI LAYOUT ---
st.set_page_config(page_title="Delivery Choice Experiment", layout="wide")

initialize_session()

st.title("🛒 Delivery Choice Game")
st.markdown(SCENARIO_TEXT)
st.progress(min(st.session_state.round / 10, 1.0))
st.write(f"Question {st.session_state.round} of 10")

# Get current options
opt_a, opt_b = st.session_state.current_options

# Create Columns for the Choice Cards
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
    st.write("- Go to competitor")
    st.write(" ") # Spacer
    st.write(" ") # Spacer
    if st.button("Choose None", use_container_width=True):
        save_choice("None", [opt_a, opt_b])
        st.rerun()

st.divider()

# --- ADMIN / DATA DOWNLOAD ---
with st.expander("Admin: Download Data"):
    st.write("When you have finished testing, download your choices here.")
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
    else:
        st.write("No data yet.")
