import streamlit as st
import pandas as pd
import uuid
import random

# --- CONFIGURATION ---
ROUNDS_PER_USER = 10
CART_RANGE = (15, 95) # 150 to 950 SEK

# Define the levels for randomization
# We categorize them into "Nests" for your later analysis
LEVELS = {
    # NEST A: PICKUP
    "PickupStandard": {
        "labels": ["Service Point", "Parcel Locker"], 
        "speed": "2-4 days",
        "prices": [29, 39, 49], 
        "thresholds": [199, 299, 399]
    },
    "PickupExpress": {
        "labels": ["Service Point", "Parcel Locker"], 
        "speed": "Next Day",
        "prices": [49, 59, 79], 
        "thresholds": [9999] # Never free
    },
    
    # NEST B: HOME
    "HomeStandard": {
        "labels": ["Home Delivery"],
        "speed": "2-4 days",
        "prices": [49, 69, 79], 
        "thresholds": [599, 799, 999]
    },
    "HomeExpress": {
        "labels": ["Home Delivery"],
        "speed": "Next Day",
        "prices": [99, 129, 149], 
        "thresholds": [9999]
    },
    
    # NEST C: SHOP
    "ShopCollect": {
        "labels": ["Collect in Shop"],
        "speed": "2-4 days",
        "prices": [0, 19], 
        "thresholds": [0, 199]
    }
}

def get_effective_price(base, threshold, cart):
    """Returns 0 if cart meets threshold, else returns base price."""
    return 0 if cart >= threshold else base

def generate_round():
    """Generates a single choice task (Menu)."""
    # 1. Randomize Cart Value
    cart_value = random.randint(CART_RANGE[0], CART_RANGE[1]) * 10
    
    menu = {}
    for key, attrs in LEVELS.items():
        # Randomize attributes
        lbl = random.choice(attrs["labels"])
        base = random.choice(attrs["prices"])
        thr = random.choice(attrs["thresholds"])
        
        # Calculate final cost
        cost = get_effective_price(base, thr, cart_value)
        
        menu[key] = {
            "label": lbl,
            "speed": attrs["speed"],
            "base_price": base,
            "threshold": thr,
            "final_cost": cost,
            "is_free": (cost == 0)
        }
    
    return cart_value, menu

def initialize_session():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'data' not in st.session_state:
        st.session_state.data = []
    if 'round' not in st.session_state:
        st.session_state.round = 1
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = generate_round()
    if 'finished' not in st.session_state:
        st.session_state.finished = False

def save_choice(choice_code):
    cart_val, menu = st.session_state.current_scenario
    
    # Prepare row data
    row = {
        "user_id": st.session_state.user_id,
        "round": st.session_state.round,
        "cart_value": cart_val,
        "choice": choice_code
    }
    
    # Log details of ALL options (even unchosen ones) for the Logit Model
    for k, v in menu.items():
        row[f"{k}_label"] = v['label']
        row[f"{k}_cost"] = v['final_cost']
        row[f"{k}_threshold"] = v['threshold']
    
    st.session_state.data.append(row)
    
    # Advance Round
    if st.session_state.round >= ROUNDS_PER_USER:
        st.session_state.finished = True
    else:
        st.session_state.round += 1
        st.session_state.current_scenario = generate_round()

# --- APP UI ---
st.set_page_config(page_title="Delivery Choice Game", layout="centered")
initialize_session()

if st.session_state.finished:
    # --- END SCREEN ---
    st.balloons()
    st.success("## Experiment Complete!")
    st.write("Thank you for your participation.")
    
    # Download Button
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Data (CSV)", csv, "survey_data.csv", "text/csv", key='dl-csv'
        )

else:
    # --- GAME SCREEN ---
    cart_val, menu = st.session_state.current_scenario
    
    st.title("🛍️ Checkout")
    st.markdown(f"Your cart total is **{cart_val} SEK**.")
    st.markdown("Choose your delivery method:")
    
    # Progress Bar
    progress = (st.session_state.round - 1) / ROUNDS_PER_USER
    st.progress(progress)
    st.caption(f"Question {st.session_state.round} of {ROUNDS_PER_USER}")

    # --- RENDER BUTTONS (The Menu) ---
    
    def render_option(key, description):
        # Helper to format the button text cleanly
        opt = menu[key]
        price_display = "FREE" if opt['is_free'] else f"{opt['final_cost']} SEK"
        
        # Structure: "1. Service Point (Next Day) | 49 SEK"
        label = f"{description}. {opt['label']} ({opt['speed']}) | {price_display}"
        
        # If the user clicks this button
        if st.button(label, use_container_width=True):
            save_choice(key)
            st.rerun()

    # 1. Shop
    render_option("ShopCollect", "1")
    
    # 2. Pickup Standard
    render_option("PickupStandard", "2")
    
    # 3. Pickup Express
    render_option("PickupExpress", "3")
    
    # 4. Home Standard
    render_option("HomeStandard", "4")
    
    # 5. Home Express
    render_option("HomeExpress", "5")
    
    st.divider()
    
    # None Option
    if st.button("🚫 I would not buy (Abandon Cart)", use_container_width=True):
        save_choice("None")
        st.rerun()

    # --- DEBUG/ADMIN VIEW (Optional) ---
    # with st.expander("Show Logic (Debug)"):
    #     st.write(menu)
