import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- CONFIGURATION SÉCURISÉE ---
st.set_page_config(page_title="Hôpital Jamot - Expert Vision", layout="wide")

# COLLE TA CLÉ ICI
API_KEY = "TA_CLE_API_A_COLLER_ICI" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

if 'historique' not in st.session_state:
    st.session_state['historique'] = []

# --- INTERFACE ---
with st.sidebar:
    st.header("👤 Identification Patient")
    nom = st.text_input("Nom ou Code", "Anonyme")
    age = st.number_input("Âge", 0, 110, 35)
    sexe = st.selectbox("Sexe", ["M", "F"])
    st.divider()
    current_id = f"JAM-{len(st.session_state['historique']) + 1:03d}"
    st.markdown(f"ID Examen : **{current_id}**")

st.title("🛡️ Diagnostic Thoracique Assisté par API")

up = st.file_uploader("📂 Charger la radiographie", type=['jpg', 'jpeg', 'png'])

if up:
    img = Image.open(up)
    col_img, col_diag = st.columns([1, 1])
    
    with col_img:
        st.image(img, caption="Cliché original", use_container_width=True)

    with col_diag:
        with st.spinner("Analyse experte en cours..."):
            # PROMPT ULTRA-STRICT POUR L'IA
            prompt = f"""
            Analyse cette radiographie thoracique (Patient: {nom}, ID: {current_id}) avec une précision de radiologue :
            
            1. AUDIT QUALITÉ : 
               - Symétrie : Les clavicules sont-elles à égale distance des épineuses ?
               - Inspiration : Est-ce que 6 arcs costaux antérieurs sont visibles au-dessus du diaphragme ?
               - Champ : Les apex et les cul-de-sacs sont-ils inclus ?
            
            2. DIAGNOSTIC :
               - Verdict : [NORMAL] ou [PATHOLOGIQUE].
               - Localisation : Décris précisément la zone suspecte si nécessaire.
            
            Réponds sous forme de liste à puces très claire.
            """
            
            # Appel à l'API de vision
            response = model.generate_content([prompt, img])
            
            st.subheader("📋 Rapport d'Audit")
            st.write(response.text)
            
            # Logique de sauvegarde rapide
            verdict_ia = "Pathologique" if "PATHOLOGIQUE" in response.text.upper() else "Normal"
            
        if st.button("💾 Enregistrer dans le registre"):
            st.session_state['historique'].insert(0, {
                "ID": current_id, "Patient": nom, "Age": age,
                "Verdict": verdict_ia, "Heure": datetime.now().strftime("%H:%M")
            })
            st.rerun()

# --- REGISTRE DE RECHERCHE ---
if st.session_state['historique']:
    st.divider()
    st.subheader("📂 Registre des examens - Hôpital Jamot")
    df = pd.DataFrame(st.session_state['historique'])
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Exporter pour le Master (CSV)", df.to_csv(index=False), "data_recherche_jamot.csv")
