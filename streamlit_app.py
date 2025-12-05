import streamlit as st
import pandas as pd
import uuid
import random

# --- CONFIGURATION OF LEVELS ---
LEVELS = {
    # Nest A: Pickup Standard
    "Pickup Standard": {
        "labels": ["Service Point", "Parcel Locker"], 
        "prices": [29, 39],
        "thresholds": [199, 249, 299],
        "speed": "2-4 days"
    },
    # Nest A: Pickup Express
    "Pickup Express": {
        "labels": ["Service Point", "Parcel Locker"], 
        "prices": [39, 49],
        "thresholds": [9999], # 9999 denotes "Not Free"
        "speed": "Express (Next Day)"
    },
    # Nest B: Home Standard
    "Home Standard": {
        "labels": ["Home Delivery"],
        "prices": [59, 79],
        "thresholds": [799, 899, 999],
        "speed": "2-4 days"
    },
    # Nest B: Home Express
    "Home Express": {
        "labels": ["Home Delivery"],
        "prices": [99, 129],
        "thresholds": [9999],
        "speed": "Express (Next Day)"
    },
    # Nest C: Shop
    "Shop Collect": {
        "labels": ["Collect in Shop"],
        "prices": [19, 29],
        "thresholds": [199, 249, 299],
        "speed": "2-4 days"
    }
}

def generate_scenario():
    """
    1. Randomizes the User's Cart Value (to test thresholds).
    2. Generates the 5 options based on your levels.
    """
    # Random cart value between 150 and 950 (rounded to nearest 10)
    cart_value = random.randint(15, 95) * 10
    
    menu_options = {}
    
    for key, attrs in LEVELS.items():
        # 1. Randomize Attributes
        label_text = random.choice(attrs["labels"])
        base_price = random.choice(attrs["prices"])
        threshold = random.choice(attrs["thresholds"])
        
        # 2. Calculate Final Price (The Logic)
        if cart_value >= threshold:
            final_price = 0
            is_free = True
        else:
            final_price = base_price
            is_free = False
            
        menu_options[key] = {
            "display_label": label_text,
            "speed": attrs["speed"],
            "base_price": base_price,
            "threshold": threshold,
            "final_price": final_price,
            "is_free": is_free
        }
        
    return cart_value, menu_options

def initialize_session():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'data' not in st.session_state:
        st.session_state.data = []
    if 'round' not in st.session_state:
        st.session_state.round = 1
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = generate_scenario()

def save_choice(choice_key):
    cart, menu = st.session_state.current_scenario
    
    row = {
        "user_id": st.session_state.user_id,
        "round": st.session_state.round,
        "cart_value": cart,
        "choice": choice_key, # This is the dependent variable (Y)
    }
    
    # Save the attributes of ALL alternatives (Independent variables X)
    # We need to know what the prices were for the options NOT chosen too.
    for key, data in menu.items():
        row[f"{key}_label"] = data['display_label'] # Was it Locker or Service Point?
        row[f"{key}_price"] = data['final_price']
        row[f"{key}_base_price"] = data['base_price']
        row[f"{key}_threshold"] = data['threshold']
    
    st.session_state.data.append(row)
    st.session_state.round += 1
    st.session_state.current_scenario = generate_scenario()

# --- UI LAYOUT ---
st.set_page_config(page_title="H&M Delivery Study", layout="centered")
initialize_session()

cart_val, menu = st.session_state.current_scenario

st.title("📦 Checkout Simulation")
st.markdown(f"""
You have added items to your cart worth **{cart_val} SEK**.
Based on this amount, review your delivery options below.
""")
st.progress(st.session_state.round / 10)

# --- DISPLAY THE 5 OPTIONS ---
st.write("---")

selection = st.radio(
    "Select your delivery method:",
    options=list(menu.keys()),
    format_func=lambda x: f"TEMP_LABEL", # Placeholder, we use custom logic below
    label_visibility="collapsed"
)

# Custom formatting for the radio buttons is hard in Streamlit, 
# so we visualize the options above and use the radio just for selection.

# 1. PICKUP STANDARD
p1 = menu["Pickup Standard"]
st.info(f"**1. {p1['display_label']}** ({p1['speed']})")
if p1['is_free']:
    st.markdown(f"**Cost: 0 kr** (Free because cart > {p1['threshold']} kr)")
else:
    st.markdown(f"**Cost: {p1['final_price']} kr** (Free at {p1['threshold']} kr)")

# 2. PICKUP EXPRESS
p2 = menu["Pickup Express"]
st.info(f"**2. {p2['display_label']}** ({p2['speed']})")
st.markdown(f"**Cost: {p2['final_price']} kr**")

# 3. HOME STANDARD
p3 = menu["Home Standard"]
st.success(f"**3. {p3['display_label']}** ({p3['speed']})")
if p3['is_free']:
    st.markdown(f"**Cost: 0 kr** (Free because cart > {p3['threshold']} kr)")
else:
    st.markdown(f"**Cost: {p3['final_price']} kr** (Free at {p3['threshold']} kr)")

# 4. HOME EXPRESS
p4 = menu["Home Express"]
st.success(f"**4. {p4['display_label']}** ({p4['speed']})")
st.markdown(f"**Cost: {p4['final_price']} kr**")

# 5. SHOP
p5 = menu["Shop Collect"]
st.warning(f"**5. {p5['display_label']}** ({p5['speed']})")
if p5['is_free']:
    st.markdown(f"**Cost: 0 kr** (Free because cart > {p5['threshold']} kr)")
else:
    st.markdown(f"**Cost: {p5['final_price']} kr** (Free at {p5['threshold']} kr)")

st.write("---")

# Selection Buttons
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("Select Opt 1"):
    save_choice("Pickup Standard")
    st.rerun()
if c2.button("Select Opt 2"):
    save_choice("Pickup Express")
    st.rerun()
if c3.button("Select Opt 3"):
    save_choice("Home Standard")
    st.rerun()
if c4.button("Select Opt 4"):
    save_choice("Home Express")
    st.rerun()
if c5.button("Select Opt 5"):
    save_choice("Shop Collect")
    st.rerun()

st.write(" ")
if st.button("🚫 I would not buy (Abandon Cart)"):
    save_choice("None")
    st.rerun()

# --- ADMIN ---
if st.session_state.data:
    with st.expander("Show Data (For Analysis)"):
        st.dataframe(pd.DataFrame(st.session_state.data))
