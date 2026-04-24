import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="RadioIA Expert - Jamot", layout="wide")

# --- CONFIGURATION DE L'API (VIA SECRETS) ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
else:
    st.error("❌ La clé API est manquante. Va dans Settings > Secrets sur Streamlit et ajoute : GOOGLE_API_KEY = 'TA_CLE'")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-flash-latest')


if 'historique' not in st.session_state:
    st.session_state['historique'] = []

# --- INTERFACE (SIDEBAR) ---
with st.sidebar:
    st.header("👤 Identification Patient")
    nom = st.text_input("Nom ou Code", "Anonyme")
    age = st.number_input("Âge", 0, 110, 35)
    sexe = st.selectbox("Sexe", ["M", "F"])
    st.divider()
    current_id = f"JAM-{len(st.session_state['historique']) + 1:03d}"
    st.markdown(f"ID Examen : **{current_id}**")

st.title("🛡️ Diagnostic Thoracique Assisté par API Gemini")

# --- ZONE DE CHARGEMENT ---
up = st.file_uploader("📂 Charger la radiographie", type=['jpg', 'jpeg', 'png'])

if up:
    # Affichage de l'image
    img = Image.open(up)
    col_img, col_diag = st.columns([1, 1])
    
    with col_img:
        st.image(img, caption="Cliché importé", use_container_width=True)

    with col_diag:
        with st.spinner("Analyse experte par l'IA en cours..."):
            try:
                # PROMPT SÉMIOLOGIQUE POUR LE MASTER
                prompt = f"""
                Analyse cette radiographie thoracique (Patient: {nom}, ID: {current_id}) avec une précision de radiologue :
                
                1. AUDIT QUALITÉ : 
                   - Symétrie : Les clavicules sont-elles à égale distance des épineuses ?
                   - Inspiration : Est-ce que 6 arcs costaux antérieurs sont visibles ?
                   - Champ : Les apex et les cul-de-sacs sont-ils inclus ?
                
                2. DIAGNOSTIC :
                   - Verdict : [NORMAL] ou [PATHOLOGIQUE].
                   - Description : Si pathologique, localise et décris l'anomalie (opacité, foyer, épanchement, etc.).
                
                Réponds par des points clairs.
                """
                
                # Correction de l'erreur InvalidArgument : on envoie l'image PIL directement
                response = model.generate_content([prompt, img])
                
                st.subheader("📋 Rapport d'Audit API")
                st.write(response.text)
                
                # Détermination du verdict pour le registre
                verdict_ia = "Pathologique" if "PATHOLOGIQUE" in response.text.upper() else "Normal"
                
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
                verdict_ia = "Erreur"

        if st.button("💾 Enregistrer dans le registre"):
            st.session_state['historique'].insert(0, {
                "ID": current_id, 
                "Patient": nom, 
                "Age": age,
                "Verdict": verdict_ia, 
                "Heure": datetime.now().strftime("%H:%M")
            })
            st.rerun()

# --- REGISTRE DE RECHERCHE ---
if st.session_state['historique']:
    st.divider()
    st.subheader("📂 Registre des examens - Hôpital Jamot")
    df = pd.DataFrame(st.session_state['historique'])
    st.dataframe(df, use_container_width=True)
    
    # Correction finale de la parenthèse pour l'export CSV
    st.download_button(
        label="📥 Exporter pour le Master (CSV)",
        data=df.to_csv(index=False),
        file_name=f"recherche_jamot_{datetime.now().strftime('%d_%m')}.csv",
        mime="text/csv")
