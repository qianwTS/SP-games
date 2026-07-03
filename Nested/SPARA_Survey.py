import streamlit as st
import pandas as pd
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# ============================================
# 1. CONFIG & SETUP
# ============================================
st.set_page_config(page_title="SPARA Undersökning", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f9f9f9; }
    .product-card {
        background: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center;
    }
    .price-tag { font-size: 24px; font-weight: bold; color: #333; }
    .total-row { border-top: 1px solid #eee; padding-top: 10px; margin-top: 20px; font-weight: bold; }
    div.row-widget.stRadio > div { flex-direction: column; }
    div.row-widget.stRadio > div[role='radiogroup'] > label {
        background-color: white; padding: 15px; margin-bottom: 10px;
        border: 1px solid #ddd; border-radius: 8px; width: 100%;
        display: flex; justify-content: space-between;
    }
    div.row-widget.stRadio > div[role='radiogroup'] > label:hover {
        background-color: #f0f2f6; border-color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 2. B2C SCENARIOS (Från check_out.py)
# ============================================
scenarios = [
    {"id": 1, "h_s": 59, "h_e": 89, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 2, "h_s": 89, "h_e": 119, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 3, "h_s": 59, "h_e": 99, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 4, "h_s": 29, "h_e": 49, "l_d": "< 1 km", "l_s": 19, "l_e": 29, "s_d": "6-8 km", "s_p": 0},
    {"id": 5, "h_s": 89, "h_e": 109, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "2-4 km", "s_p": 29},
    {"id": 6, "h_s": 29, "h_e": 69, "l_d": "< 1 km", "l_s": 19, "l_e": 29, "s_d": "4-6 km", "s_p": 0},
    {"id": 7, "h_s": 59, "h_e": 99, "l_d": "< 1 km", "l_s": 29, "l_e": 39, "s_d": "4-6 km", "s_p": 19},
    {"id": 8, "h_s": 89, "h_e": 129, "l_d": "1-2 km", "l_s": 19, "l_e": 29, "s_d": "6-8 km", "s_p": 0},
    {"id": 9, "h_s": 29, "h_e": 49, "l_d": "2-3 km", "l_s": 0, "l_e": 29, "s_d": "2-4 km", "s_p": 0},
    {"id": 10, "h_s": 89, "h_e": 129, "l_d": "1-2 km", "l_s": 29, "l_e": 39, "s_d": "4-6 km", "s_p": 19},
    {"id": 11, "h_s": 59, "h_e": 89, "l_d": "2-3 km", "l_s": 29, "l_e": 39, "s_d": "6-8 km", "s_p": 19},
    {"id": 12, "h_s": 29, "h_e": 59, "l_d": "2-3 km", "l_s": 0, "l_e": 19, "s_d": "2-4 km", "s_p": 0},
]

# ============================================
# 3. GOOGLE SHEETS FUNCTIONS
# ============================================
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" not in st.secrets:
        st.error("Missing Google Secrets in .streamlit/secrets.toml")
        return None
    s_dict = st.secrets["gcp_service_account"]
    creds_dict = dict(s_dict)
    creds_dict["private_key"] = s_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def save_b2c_to_google_sheets(answers, demographics):
    try:
        client = get_gspread_client()
        if not client: return False
        sheet = client.open("Survey_greendelivery_nudging").worksheet("B2C_Responses")
        rows = []
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in answers:
            row = [
                ts, str(st.session_state.session_id), str(item['group']),
                str(demographics.get('Gender', '')), str(demographics.get('Age', '')),
                str(demographics.get('Occupation', '')), str(demographics.get('Education', '')),
                str(demographics.get('Household_Size', '')), str(demographics.get('Income', '')),
                str(demographics.get('Urbanization', '')), str(demographics.get('Car_Owner', '')),
                str(demographics.get('Dist_Locker', '')), str(demographics.get('Dist_Pickup', '')),
                str(demographics.get('Online_Freq', '')), str(demographics.get('mode_locker', '')),
                str(demographics.get('mode_shop', '')), str(demographics.get('Categories', '')),
                int(item['scenario_id']), str(item['choice']), str(item['choice_price']), str(item['choice_dist'])
            ]
            rows.append(row)
        sheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        return False

def save_b2b_to_google_sheets(b2b_data):
    try:
        client = get_gspread_client()
        if not client: return False
        sheet = client.open("Survey_greendelivery_nudging").worksheet("B2B_Responses")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Flatten lists into comma-separated strings for Google Sheets
        flat_data = [ts, str(st.session_state.session_id)]
        for key, val in b2b_data.items():
            if isinstance(val, list):
                flat_data.append(", ".join(val))
            else:
                flat_data.append(str(val))
                
        sheet.append_row(flat_data)
        return True
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        return False

# ============================================
# 4. SESSION STATE INIT
# ============================================
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(random.randint(100000, 999999))

# APP STAGES: "intro" -> "routing" -> "b2b_survey" ELLER "b2c_survey"
if 'stage' not in st.session_state:
    st.session_state.stage = "intro"

if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
    st.session_state.answers = []
    
    query_params = st.query_params
    if "group" in query_params:
        st.session_state.group = query_params["group"]
    else:
        st.session_state.group = random.choice(["control", "label", "co2"])

# ============================================
# 5. NAVIGATION HELPER FUNCTIONS
# ============================================
def set_stage(stage_name):
    st.session_state.stage = stage_name

def get_nudge_text(mode, group):
    if group == "control": return ""
    if group == "label":
        if mode in ["Parcel Locker", "Express Locker", "Store Collect"]: return "🌿 Eco Choice"
        return ""
    if group == "co2":
        if mode == "Express Home": return "🔴 850g CO2e"
        if mode == "Standard Home": return "🟠 300g CO2e"
        if mode in ["Parcel Locker", "Express Locker", "Store Collect"]: return "🟢 50g CO2e"
    return ""


# ============================================
# 6. APP RENDER LOGIC
# ============================================

# --------------------------------------------
# STAGE 1: INTRODUKTION
# --------------------------------------------
if st.session_state.stage == "intro":
    st.title("Välkommen till vår undersökning!")
    st.markdown("""
    Enkäten är en del av forskningsprojektet SPARA, som studerar hur leveranser av material kan göras mer flexibla och resurseffektiva i sista delen av distributionskedjan. Den genomförs av Linköpings universitet i samarbete med KTH.

    **Enkäten består av två delar:**
    * Först får du svara på några frågor om dig eller ditt företag och hur ni vanligtvis köper och tar emot material.
    * Sen får du ta ställning till ett antal köpscenarier, där du väljer mellan olika leveransalternativ i ett digitalt gränssnitt liknande sådant som man beställer i som e-handelskonsument. 

    Hela enkäten tar cirka 10 minuter att genomföra. Dina svar är anonyma och kommer att användas i forskningssyfte. Resultaten redovisas enbart sammanställt, så att inga enskilda svar kan kopplas till dig eller ditt företag.

    Har du frågor är du välkommen att kontakta [namn, e-postadress].
    """)
    st.button("Starta undersökningen", on_click=set_stage, args=("routing",), type="primary")

# --------------------------------------------
# STAGE 2: VÄGVAL (B2B ELLER B2C)
# --------------------------------------------
elif st.session_state.stage == "routing":
    st.title("Vem representerar du?")
    st.markdown("För att vi ska kunna ställa rätt frågor behöver vi veta i vilken roll du besvarar denna enkät.")
    
    user_type = st.radio(
        "Jag svarar på denna enkät som:",
        ["Representant för ett företag (B2B)", "Privatkonsument (B2C)"]
    )
    
    if st.button("Gå vidare", type="primary"):
        if "företag" in user_type:
            set_stage("b2b_survey")
        else:
            set_stage("b2c_survey")
        st.rerun()

# --------------------------------------------
# STAGE 3A: B2B UNDERSÖKNING
# --------------------------------------------
# --------------------------------------------
# STAGE 3A: B2B UNDERSÖKNING
# --------------------------------------------
elif st.session_state.stage == "b2b_survey":
    st.title("Del 1: Bakgrund och Köpbeteende (B2B)")
    st.markdown("Vänligen besvara frågorna nedan. Alla frågor är obligatoriska.")
    
    with st.form("b2b_form"):
        # Vanliga valfrågor (Selectbox) med tomma startvärden
        q1 = st.selectbox(
            "1. Vilken typ av verksamhet representerar du i den här enkäten?", 
            ["Huvudentreprenör", "Underentreprenör", "Installatör", "Fastighetsägare/förvaltare", "Återförsäljare/grossist", "Annat"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        q2 = st.selectbox(
            "2. Hur många anställda har ert företag totalt?", 
            ["1 (endast jag)", "2–9", "10–49", "50–249", "250 eller fler"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        q3 = st.selectbox(
            "3. Vilken är din huvudsakliga yrkesroll?", 
            ["Inköpare/inköpsansvarig", "Projektledare", "Hantverkare/montör/installatör", "Arbetsledare/platschef", "VD/ägare", "Lagerchef/lageransvarig", "Annat"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        q4 = st.selectbox(
            "4. Hur många års erfarenhet har du av branschen?", 
            ["0–2 år", "3–5 år", "6–10 år", "11–20 år", "Mer än 20 år"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        
        st.markdown("---")
        # Skalfrågor omgjorda till klickbara Radio-knappar (horisontella)
        st.write("**5. Hur ofta använder du följande sätt att lägga en beställning?**")
        scale_options = ["Aldrig", "Sällan", "Ibland", "Ofta", "Alltid"]
        
        q5_webb = st.radio("5a. Webbutik/app", options=scale_options, index=None, horizontal=True)
        q5_epost = st.radio("5b. E-post", options=scale_options, index=None, horizontal=True)
        q5_tel = st.radio("5c. Telefon", options=scale_options, index=None, horizontal=True)
        q5_butik = st.radio("5d. I butik", options=scale_options, index=None, horizontal=True)
        
        st.markdown("---")
        q6 = st.selectbox(
            "6. Hur långt i förväg vet du vanligtvis om ett kommande materialbehov, innan en beställning behöver läggas?", 
            ["Samma dag", "1–2 dagar i förväg", "3–7 dagar i förväg", "Mer än en vecka i förväg", "Varierar mycket från fall till fall"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        q7 = st.selectbox(
            "7. Hur ofta lägger ni vanligtvis en beställning hos er huvudsakliga leverantör?", 
            ["Flera gånger per dag", "Dagligen", "Några gånger per vecka", "Veckovis", "Månadsvis", "Mer sällan"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        q8 = st.multiselect(
            "8. Vilken typ av gods köper ni oftast? (Flera val möjliga)", 
            ["Litet paket (får plats i brevlåda)", "Kan bäras för hand (större än brevlåda)", "Kräver kärra eller truck", "Pall", "Kräver kran eller specialtransport", "Varierar mycket"],
            placeholder="Välj alternativ i listan nedan..."
        )

        st.markdown("---")
        st.write("**9. Med vilken frekvens används följande leveranssätt för era leveranser?**")
        q9_butik = st.radio("9a. Upphämtning i butik", options=scale_options, index=None, horizontal=True)
        q9_direkt = st.radio("9b. Direktleverans till arbetsplatsen (utan box)", options=scale_options, index=None, horizontal=True)
        q9_box_arb = st.radio("9c. Låsbar leveransbox/container på arbetsplatsen", options=scale_options, index=None, horizontal=True)
        q9_box_annat = st.radio("9d. Låsbar leveransbox på annat ställe än arbetsplatsen", options=scale_options, index=None, horizontal=True)
        
        st.markdown("---")
        q10 = st.multiselect(
            "10. Vad skulle få dig att överväga en annan leveransplats än den du normalt använder? Välj dina topp 3 anledningar.", 
            ["Lägre pris", "Snabbare leverans", "Mer exakt leveranstid/tidsfönster", "Mindre miljöpåverkan", "Närmare din arbetsplats", "Minskad tid för mottagning"], 
            max_selections=3, placeholder="Välj upp till 3 alternativ i listan nedan..."
        )
        
        q11 = st.selectbox(
            "11. Är ni bundna av ramavtal eller upphandling som styr vilka leverantörer ni får handla från?", 
            ["Ja, helt styrt", "Ja, delvis styrt", "Nej, vi väljer fritt", "Vet ej"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )
        q12 = st.multiselect(
            "12. Vilka kriterier var avgörande när ni valde er nuvarande leverantör? Markera de tre viktigaste.", 
            ["Pris", "Leveranstider", "Tidigare samarbete", "Referensprojekt", "Kompetens i allmänhet", "Kompetens för det specifika projektet", "Miljöaspekter", "Leverantören finns redan i vårt system/vår organisation"], 
            max_selections=3, placeholder="Välj upp till 3 alternativ i listan nedan..."
        )
        q13 = st.selectbox(
            "13. Vem betalar transporten i de flesta av era projekt/uppdrag?", 
            ["Vi betalar transporten separat", "Transporten ingår i produktpriset", "Beställaren av projektet står för transporten", "Vet ej"],
            index=None, placeholder="Välj ett alternativ i listan nedan..."
        )

        # Skicka in-knapp
        b2b_submit = st.form_submit_button("Skicka in svar", type="primary")
        
        if b2b_submit:
            # Lista på alla svar för validering
            all_answers = [
                q1, q2, q3, q4, 
                q5_webb, q5_epost, q5_tel, q5_butik, 
                q6, q7, q8, 
                q9_butik, q9_direkt, q9_box_arb, q9_box_annat, 
                q10, q11, q12, q13
            ]
            
            # Kontrollera om något värde är None (för radio/selectbox) eller [] (för multiselect)
            if any(a is None or (isinstance(a, list) and len(a) == 0) for a in all_answers):
                st.error("⚠️ Vänligen besvara alla frågor (1-13) innan du skickar in.")
            else:
                # Spara datan och mappa tillbaka till de gamla A,B,C,D-rubrikerna för din Excel-fil
                b2b_data = {
                    "A1": q1, "A2": q2, "A3": q3, "A4": q4,
                    "B1_Webb": q5_webb, "B1_Epost": q5_epost, "B1_Tel": q5_tel, "B1_Butik": q5_butik,
                    "B2": q6, "B3": q7, "B4": q8,
                    "C1_Butik": q9_butik, "C1_Direkt": q9_direkt, "C1_BoxArb": q9_box_arb, "C1_BoxAnnat": q9_box_annat,
                    "C2_Faktorer": q10,
                    "D1": q11, "D2": q12, "D3": q13
                }
                
                success = save_b2b_to_google_sheets(b2b_data)
                if success:
                    st.success("Tack! Dina svar är inskickade.")
                    st.balloons()
                    # Eventuell kod här för att skicka dem vidare till B2B-scenarierna
                    # Valfritt: Led användaren vidare till B2C check-out simuleringen om de ska göra del 2 också:
                    # set_stage("b2c_survey")
                    # st.rerun()

# --------------------------------------------
# STAGE 3B: B2C CHECK-OUT SCENARIER
# --------------------------------------------
elif st.session_state.stage == "b2c_survey":
    
    if st.session_state.current_q < len(scenarios):
        q_data = scenarios[st.session_state.current_q]
        st.progress((st.session_state.current_q) / len(scenarios))
        st.write(f"Scenario {st.session_state.current_q + 1} av {len(scenarios)}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            if os.path.exists("headset.png"):
                st.image("headset.png", use_column_width=True)
            else:
                st.image("https://via.placeholder.com/300x350.png?text=RM+Hoodie", use_column_width=True)
                
            st.markdown(f"""
                <h3>RM Headset</h3>
                <p>Brand: X | Batterytime: X</p>
                <div class="price-tag">499 SEK</div>
                <div class="total-row">Subtotal: 499 SEK</div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.subheader("Select Delivery Method")
            options = [
                {"name": "Standard Home", "time": "2-4 days", "dist": "Doorstep", "price": q_data['h_s']},
                {"name": "Express Home", "time": "Next Day", "dist": "Doorstep", "price": q_data['h_e']},
                {"name": "Parcel Locker", "time": "2-4 days", "dist": q_data['l_d'], "price": q_data['l_s']},
                {"name": "Express Locker", "time": "Next Day", "dist": q_data['l_d'], "price": q_data['l_e']},
                {"name": "Store Collect", "time": "2-4 days", "dist": q_data['s_d'], "price": q_data['s_p']},
            ]
            
            radio_labels = []
            opt_lookup = {}
            for opt in options:
                nudge = get_nudge_text(opt['name'], st.session_state.group)
                price_str = "FREE" if opt['price'] == 0 else f"{opt['price']} SEK"
                label = f"**{opt['name']}** |  {opt['time']}  |  {opt['dist']}  |  **{price_str}**"
                if nudge: label += f"  \n_{nudge}_"
                radio_labels.append(label)
                opt_lookup[label] = opt

            choice = st.radio("Options:", radio_labels, key=f"q_{st.session_state.current_q}")
            st.markdown("---")
            
            nav_col1, nav_col2 = st.columns(2)
            with nav_col1:
                if st.session_state.current_q > 0:
                    if st.button("⬅️ Go Back", use_container_width=True):
                        st.session_state.current_q -= 1
                        if len(st.session_state.answers) > 0:
                            st.session_state.answers.pop()
                        st.rerun()
            with nav_col2:
                if st.button("Confirm Selection ➡️", type="primary", use_container_width=True):
                    selected = opt_lookup[choice]
                    st.session_state.answers.append({
                        "scenario_id": q_data['id'],
                        "group": st.session_state.group,
                        "choice": selected['name'],
                        "choice_price": selected['price'],
                        "choice_dist": selected['dist']
                    })
                    st.session_state.current_q += 1
                    st.rerun()

    else:
        # B2C DEMOGRAFISKT FORMULÄR
        st.subheader("Almost done! Please answer a few questions about yourself.")
        if st.button("⬅️ Go Back to Last Scenario"):
            st.session_state.current_q -= 1
            if len(st.session_state.answers) > 0: st.session_state.answers.pop()
            st.rerun()
            
        with st.form("demographics_form"):
            d_gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Prefer not to say"])
            d_age = st.selectbox("Age Group", ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
            d_educ = st.selectbox("Education Level", ["High School", "University (Bachelor)", "University (Master/PhD)", "Other"])
            d_occup = st.selectbox("Occupation", ["Student", "Employed", "Self-employed", "Unemployed", "Retired"])
            d_income = st.selectbox("Monthly Income (after Tax)", ["< 20k SEK", "20k-35k SEK", "35k-50k SEK", "> 50k SEK", "Prefer not to say"])
            d_urban = st.selectbox("Living Area", ["Urban (Center)", "Suburban", "Rural"])
            d_hh_size = st.number_input("Household Size", 1, 10, 1)
            d_car = st.radio("Do you have access to a car?", ["Yes", "No"])
            
            st.markdown("---")
            d_freq = st.selectbox("How often do you shop online?", ["Daily", "Weekly", "Monthly", "Rarely"])
            d_cat = st.multiselect("What do you usually buy online?", ["Clothing", "Electronics", "Beauty/Pharmacy", "Groceries", "Home Goods"])
            d_dist_l = st.selectbox("Distance to nearest Parcel Locker from home", ["< 500m", "500m - 1km", "1-3 km", "> 3km"])
            d_dist_s = st.selectbox("Distance to nearest Shop Center", ["<1km", "1-3km", "3-6km", ">6km"])
            
            d_freq_tolocker = st.selectbox("How do you usually travel to pick up parcels (Locker)?", ["Walk", "Bike", "Car", "Public Transport", "N/A"])
            d_freq_toshop = st.selectbox("How do you usually travel to pick up parcels (Store)?", ["Walk", "Bike", "Car", "Public Transport", "N/A"])

            submitted = st.form_submit_button("Submit Survey")
            
            if submitted:
                demographics = {
                    "Gender": d_gender, "Age": d_age, "Education": d_educ, 
                    "Occupation": d_occup, "Income": d_income, "Urbanization": d_urban,
                    "Household_Size": d_hh_size, "Car_Owner": d_car,
                    "Online_Freq": d_freq, "Categories": ", ".join(d_cat),
                    "Dist_Locker": d_dist_l, "Dist_Pickup": d_dist_s,
                    "mode_locker": d_freq_tolocker, "mode_shop": d_freq_toshop
                }
                
                success = save_b2c_to_google_sheets(st.session_state.answers, demographics)
                if success:
                    st.success("Data saved successfully! Thank you for participating.")
                    st.balloons()
