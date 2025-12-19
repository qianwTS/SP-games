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
    home_prices = st.multiselect("Home Prices", [69, 79], default=[69, 79])
    home_thresh = st.multiselect("Home Free Thresholds", [799, 899], default=[799, 899])
    home_exp_prices = st.multiselect("Home Express Prices", [99, 129], default=[99, 129])
    
    st.subheader("Nest C: Shop Collect")
    shop_prices = st.multiselect("Shop Prices", [19, 29], default=[19, 29])
    shop_thresh = st.multiselect("Shop Free Thresholds", [149, 249], default=[149, 249])

    # --- NEW SUSTAINABILITY SECTION ---
    st.subheader("🌿 Sustainability Attributes")
    st.caption("Randomly assign 'Fossil Free' badges to test Willingness to Pay.")
    home_green_opts = st.multiselect("Home is Fossil Free?", [True, False], default=[True, False])
    locker_green_opts = st.multiselect("Locker is Fossil Free?", [True, False], default=[True, False])

    st.header("2. Experiment Settings")
    n_small = st.number_input("Scenarios for Small Basket", value=8, min_value=1)
    n_big = st.number_input("Scenarios for Big Basket", value=8, min_value=1)
    seed = st.number_input("Random Seed (for reproducibility)", value=42)

    # --- NEW SECTION ON DISTANCE TRADE-OFF ---   
    st.subheader("📍 Distance Attributes")
    # Define realistic distances. 
    # "Closest" usually implies <500m. "Far" implies driving might be needed.
    locker_dist_opts = st.multiselect("Locker Distances", ["<1 km", "1-2 km", "2-3 km"], default=["<1 km", "1-2 km"])
    shop_dist_opts = st.multiselect("Shop Distances", ["2-4 km", "4-6 km", ">6 km"], default=["2-4 km", "4-6 km"])

# --- 2. GENERATION LOGIC ---

def generate_full_factorial():
    """Generates all possible combinations of attributes."""
    # Create the Cartesian product of all selected levels
    combinations = list(itertools.product(
        locker_prices, locker_thresh,
        locker_exp_prices, locker_green_opts, locker_dist_opts, # Added Green and distance
        home_prices, home_thresh,
        home_exp_prices, home_green_opts,     # Added Green
        shop_prices, shop_thresh, shop_dist_opts # Added Distance
    ))
    
    cols = [
        "Locker_Price", "Locker_Threshold",
        "Locker_Exp_Price", "Locker_Is_Green", "Locker_Distance", # Column Name
        "Home_Price", "Home_Threshold",
        "Home_Exp_Price", "Home_Is_Green",     # Column Name
        "Shop_Price", "Shop_Threshold", "Shop_Distance"
    ]
    
    return pd.DataFrame(combinations, columns=cols)

def calculate_scenario_logic(df, cart_value):
    """
    Applies Top-Up Logic AND Filtering.
    """
    res = df.copy()
    
    # Logic Helper
    def get_offer(price, threshold, cart):
        if cart >= threshold:
            return 0, 0, "FREE"
        else:
            gap = threshold - cart
            return price, gap, f"Pay {price} or Add {gap}"

    # 1. Calculate Costs & Gaps
    res['Locker_Final_Cost'], res['Locker_TopUp_Gap'], res['Locker_Display'] = zip(*res.apply(
        lambda x: get_offer(x['Locker_Price'], x['Locker_Threshold'], cart_value), axis=1
    ))
    res['Home_Final_Cost'], res['Home_TopUp_Gap'], res['Home_Display'] = zip(*res.apply(
        lambda x: get_offer(x['Home_Price'], x['Home_Threshold'], cart_value), axis=1
    ))
    res['Shop_Final_Cost'], res['Shop_TopUp_Gap'], res['Shop_Display'] = zip(*res.apply(
        lambda x: get_offer(x['Shop_Price'], x['Shop_Threshold'], cart_value), axis=1
    ))
    
    # Express Displays
    res['Locker_Exp_Display'] = res['Locker_Exp_Price'].apply(lambda x: f"Pay {x}")
    res['Home_Exp_Display'] = res['Home_Exp_Price'].apply(lambda x: f"Pay {x}")

    # ==========================================
    # LOGIC FILTERS
    # ==========================================
    
    # Filter 1: Eliminate Double Free (Home vs Locker)
    mask_double_free = (res['Home_TopUp_Gap'] == 0) & (res['Locker_TopUp_Gap'] == 0)
    
    # Filter 2: Enforce Hierarchy (Locker vs Shop)
    mask_illogical_shop = (res['Locker_TopUp_Gap'] == 0) & (res['Shop_TopUp_Gap'] > 0)

    # Filter 3: Enforce Hierarchy (Home vs Locker)
    mask_illogical_locker = (res['Home_TopUp_Gap'] == 0) & (res['Locker_TopUp_Gap'] > 0)

    # Apply Filters
    mask_bad = mask_double_free | mask_illogical_shop | mask_illogical_locker
    res_filtered = res[~mask_bad].copy()

    return res_filtered

# --- 3. EXECUTION ---

# 1. Generate Full Matrix
full_design = generate_full_factorial()

if full_design.empty:
    st.error("Please select at least one level for every attribute in the sidebar.")
else:
    # 2. Define Contexts (The Baskets)
    # We use 750 SEK for Big Basket to avoid the "Home Double Free" issue.
    contexts = [
        {"val": 240, "label": "Small Basket (240kr)", "n": n_small},
        {"val": 750, "label": "Big Basket (750kr)",   "n": n_big}
    ]

    final_dfs = []
    
    # We loop through both contexts (Small & Big) to apply the same cleaning logic
    for ctx in contexts:
        # A. Apply Logic to the WHOLE universe of combinations first
        temp_df = full_design.copy()
        temp_df['Context_Cart_Value'] = ctx['val']
        temp_df['Context_Label'] = ctx['label']
        
        # Calculate the display strings for all 512+ combinations
        calculated_df = calculate_scenario_logic(temp_df, ctx['val'])
        
        # B. Define what columns constitute a "Unique Visual Scenario"
        # UPDATED: We added 'Locker_Is_Green' and 'Home_Is_Green'.
        # This ensures that "Home 79 (Green)" and "Home 79 (Not Green)" 
        # are seen as DIFFERENT scenarios and not duplicates.
        display_cols = [
            'Shop_Display', 'Shop_Distance',
            'Locker_Display', 'Locker_Exp_Display', 'Locker_Is_Green','Locker_Distance',
            'Home_Display', 'Home_Exp_Display', 'Home_Is_Green'
        ]
        
        # C. Remove "Visual Duplicates"
        unique_visuals = calculated_df.drop_duplicates(subset=display_cols)
        
        # D. Sample from the UNIQUE list
        if len(unique_visuals) >= ctx['n']:
            sampled_df = unique_visuals.sample(n=ctx['n'], random_state=seed)
        else:
            st.warning(f"Note: Only {len(unique_visuals)} unique scenarios exist for {ctx['label']}. Returning all of them.")
            sampled_df = unique_visuals
            
        final_dfs.append(sampled_df)

    # Combine both baskets into one final design
    final_design = pd.concat(final_dfs).reset_index(drop=True)
    final_design.index.name = "Scenario_ID"
    final_design.index += 1 # Start ID at 1 for readability
    
    # --- 4. DISPLAY ---

    st.subheader(f"Generated Design ({len(final_design)} Scenarios)")
    st.caption("The table below shows exactly what to display to the respondent.")

    # Create a simplified view for the user
    display_view_cols = [
        'Context_Label', 
        'Shop_Display', 
        'Locker_Display', 'Locker_Is_Green',
        'Home_Display', 'Home_Is_Green'
    ]
    
    st.dataframe(final_design[display_view_cols], use_container_width=True)

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
    * **Display Columns:** Use these strings in your survey text.
    * **Is_Green Columns:** Use these to toggle the 🌿 Fossil Free Badge in the survey.
    * **Gap Columns:** Use these in your analysis to see the 'Price of Free Shipping'.
    """)
