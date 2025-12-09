import streamlit as st
import pandas as pd
import itertools
import numpy as np

# --- 1. CONFIGURATION & SIDEBAR ---
st.set_page_config(layout="wide", page_title="Shipping Choice Experiment Designer")

st.title("📦 Top-Up Experiment Design Generator")
st.markdown("""
This tool generates an experimental design for a **Shipping Choice Study**. 
It calculates the "Top-Up Gap" (how much extra a user must buy to get free shipping) 
based on their current cart value.
""")

with st.sidebar:
    st.header("1. Define Attribute Levels (SEK)")
    
    st.subheader("Nest A: Service Point / Locker")
    locker_prices = st.multiselect("Locker Prices", [29, 39], default=[29, 39])
    locker_thresh = st.multiselect("Locker Free Thresholds", [199, 299], default=[199, 299])
    locker_exp_prices = st.multiselect("Locker Express Prices", [49, 59], default=[49, 59])
    
    st.subheader("Nest B: Home Delivery")
    home_prices = st.multiselect("Home Prices", [59, 79], default=[59, 79])
    home_thresh = st.multiselect("Home Free Thresholds", [799, 999], default=[799, 999])
    home_exp_prices = st.multiselect("Home Express Prices", [99, 129], default=[99, 129])
    
    st.subheader("Nest C: Shop Collect")
    shop_prices = st.multiselect("Shop Prices", [19, 29], default=[19, 29])
    shop_thresh = st.multiselect("Shop Free Thresholds", [149, 249], default=[149, 249])

    st.header("2. Experiment Settings")
    n_small = st.number_input("Scenarios for Small Basket", value=8, min_value=1)
    n_big = st.number_input("Scenarios for Big Basket", value=8, min_value=1)
    seed = st.number_input("Random Seed (for reproducibility)", value=42)

# --- 2. GENERATION LOGIC ---

def generate_full_factorial():
    """Generates all possible combinations of attributes."""
    # Create the Cartesian product of all selected levels
    combinations = list(itertools.product(
        locker_prices, locker_thresh,
        locker_exp_prices,
        home_prices, home_thresh,
        home_exp_prices,
        shop_prices, shop_thresh
    ))
    
    cols = [
        "Locker_Price", "Locker_Threshold",
        "Locker_Exp_Price",
        "Home_Price", "Home_Threshold",
        "Home_Exp_Price",
        "Shop_Price", "Shop_Threshold"
    ]
    
    return pd.DataFrame(combinations, columns=cols)

def calculate_scenario_logic(df, cart_value):
    """
    Applies the Top-Up Logic:
    If Cart Value < Threshold: User sees Price OR Top-Up Gap.
    If Cart Value >= Threshold: User sees FREE.
    """
    # Create a copy to avoid SettingWithCopy warnings
    res = df.copy()
    
    # Define the Logic Function
    def get_offer(price, threshold, cart):
        if cart >= threshold:
            return 0, 0, "FREE" # Cost is 0, Gap is 0
        else:
            gap = threshold - cart
            return price, gap, f"Pay {price} or Add {gap}"

    # Apply to Locker
    res['Locker_Final_Cost'], res['Locker_TopUp_Gap'], res['Locker_Display'] = zip(*res.apply(
        lambda x: get_offer(x['Locker_Price'], x['Locker_Threshold'], cart_value), axis=1
    ))

    # Apply to Home
    res['Home_Final_Cost'], res['Home_TopUp_Gap'], res['Home_Display'] = zip(*res.apply(
        lambda x: get_offer(x['Home_Price'], x['Home_Threshold'], cart_value), axis=1
    ))

    # Apply to Shop
    res['Shop_Final_Cost'], res['Shop_TopUp_Gap'], res['Shop_Display'] = zip(*res.apply(
        lambda x: get_offer(x['Shop_Price'], x['Shop_Threshold'], cart_value), axis=1
    ))
    
    # Express Options (Never Free)
    res['Locker_Exp_Display'] = res['Locker_Exp_Price'].apply(lambda x: f"Pay {x}")
    res['Home_Exp_Display'] = res['Home_Exp_Price'].apply(lambda x: f"Pay {x}")

    # If Home is Free (Gap=0) AND Locker is Free (Gap=0), DROP IT.
    mask_double_free = (res['Home_TopUp_Gap'] == 0) & (res['Locker_TopUp_Gap'] == 0)
    
    # Keep only rows where mask is False
    res_filtered = res[~mask_double_free].copy()

    return res_filtered

# --- 3. EXECUTION ---

# 1. Generate Full Matrix
full_design = generate_full_factorial()

if full_design.empty:
    st.error("Please select at least one level for every attribute in the sidebar.")
else:
    # 2. Define Contexts (The Baskets)
    small_basket_val = 240 # SEK
    big_basket_val = 750   # SEK

    # 3. Sample Balanced Sets
    # We use random sampling with a seed to simulate an orthogonal selection 
    # (True orthogonality requires complex library support, but random sampling 
    # from the full factorial is statistically robust for this sample size).
    
    np.random.seed(seed)
    
    # Sample indices for Small Basket
    idx_small = np.random.choice(full_design.index, n_small, replace=False)
    df_small = full_design.loc[idx_small].copy()
    df_small['Context_Cart_Value'] = small_basket_val
    df_small['Context_Label'] = "Small Basket (240kr)"
    
    # Sample indices for Big Basket (try to pick different ones if possible)
    remaining_idx = full_design.index.difference(idx_small)
    if len(remaining_idx) < n_big:
        # Fallback if we run out of unique rows (unlikely here)
        idx_big = np.random.choice(full_design.index, n_big, replace=False) 
    else:
        idx_big = np.random.choice(remaining_idx, n_big, replace=False)
        
    df_big = full_design.loc[idx_big].copy()
    df_big['Context_Cart_Value'] = big_basket_val
    df_big['Context_Label'] = "Big Basket (750kr)"

    # 4. Calculate Logic
    final_small = calculate_scenario_logic(df_small, small_basket_val)
    final_big = calculate_scenario_logic(df_big, big_basket_val)
    
    # Combine
    final_design = pd.concat([final_small, final_big]).reset_index(drop=True)
    final_design.index.name = "Scenario_ID"
    final_design.index += 1 # Start ID at 1

    # --- 4. DISPLAY ---

    st.subheader(f"Generated Design ({len(final_design)} Scenarios)")
    st.caption("The table below shows exactly what to display to the respondent.")

    # Create a simplified view for the user
    display_cols = [
        'Context_Label', 
        'Shop_Display', 
        'Locker_Display', 
        'Locker_Exp_Display',
        'Home_Display', 
        'Home_Exp_Display'
    ]
    
    st.dataframe(final_design[display_cols], use_container_width=True)

    # --- 5. DETAILED DATA & EXPORT ---
    
    with st.expander("View Underlying Data (Prices & Gaps)"):
        st.write("This data contains the raw numbers for your analysis.")
        st.dataframe(final_design)

    st.download_button(
        label="Download Design as CSV",
        data=final_design.to_csv().encode('utf-8'),
        file_name='shipping_topup_design.csv',
        mime='text/csv',
    )
    
    st.info("""
    **How to read the results:**
    * **Display Columns:** Use these strings in your survey text (e.g., "Pay 59 or Add 149").
    * **Gap Columns:** Use these in your analysis to see the 'Price of Free Shipping'.
    * **Small Basket:** Note how Shop/Locker are the main tests here.
    * **Big Basket:** Note how Home Delivery is the main test here (Shop/Locker usually Free).
    """)
