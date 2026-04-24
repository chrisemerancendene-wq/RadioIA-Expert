import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="RadioIA Expert - Jamot", layout="wide")

# --- CONFIGURATION DE L'API (VIA SECRETS) ---
# --- CONFIGURATION DE L'API ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    # On force la configuration sur la version stable
    genai.configure(api_key=API_KEY, transport='grpc') 
else:
    st.error("❌ Clé API manquante dans les Secrets.")
    st.stop()

# On utilise le nom complet du modèle pour éviter toute confusion
model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')

# Initialisation du modèle (Syntaxe robuste pour éviter l'erreur 404)
model = genai.GenerativeModel('gemini-1.5-flash')

# Gestion de l'historique pour ton Master
if 'historique' not in st.session_state:
    st.session_state['historique'] = []

# --- INTERFACE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.header("👤 Identification Patient")
    nom = st.text_input("Nom ou Code Patient", "Anonyme")
    age = st.number_input("Âge", 0, 110, 35)
    sexe = st.selectbox("Sexe", ["M", "F"])
    st.divider()
    # ID automatique basé sur le nombre d'examens
    current_id = f"JAM-{len(st.session_state['historique']) + 1:03d}"
    st.markdown(f"ID Examen en cours : **{current_id}**")
    st.info("Ce projet est destiné à l'évaluation de l'IA à l'Hôpital Jamot.")

st.title("🛡️ Diagnostic Thoracique Assisté par IA")
st.caption("Outil de recherche pour le contrôle qualité et le tri automatisé des clichés.")

# --- ZONE DE CHARGEMENT ---
up = st.file_uploader("📂 Charger la radiographie (PNG, JPG, JPEG)", type=['jpg', 'jpeg', 'png'])

if up:
    # Lecture de l'image
    img = Image.open(up)
    col_img, col_diag = st.columns([1, 1])
    
    with col_img:
        st.image(img, caption="Radiographie chargée", use_container_width=True)

    with col_diag:
        st.subheader("📋 Analyse de l'IA")
        
        # Le bouton pour lancer l'analyse
        if st.button("Lancer l'analyse experte"):
            with st.spinner("Analyse en cours via l'API Gemini..."):
                try:
                    # Prompt structuré pour tes critères de recherche
                    prompt = f"""
                    Agis en tant qu'expert radiologue. Analyse cette image (ID: {current_id}) :
                    
                    1. AUDIT DE QUALITÉ :
                       - La symétrie est-elle correcte (clavicules) ?
                       - L'inspiration est-elle suffisante (6 arcs costaux) ?
                       - Le champ pulmonaire est-il complet ?
                    
                    2. INTERPRÉTATION :
                       - Verdict : Réponds uniquement par [NORMAL] ou [PATHOLOGIQUE].
                       - Détails : Si pathologique, décris l'anomalie (opacité, silhouette cardiaque, épanchement).
                    
                    Réponds de manière concise.
                    """
                    
                    # Appel à l'API
                    response = model.generate_content([prompt, img])
                    rapport_texte = response.text
                    
                    st.write(rapport_texte)
                    
                    # Détection du verdict pour le tableau
                    verdict_ia = "Pathologique" if "PATHOLOGIQUE" in rapport_texte.upper() else "Normal"
                    
                    # Stockage temporaire du résultat pour enregistrement
                    st.session_state['last_analysis'] = {
                        "ID": current_id, 
                        "Patient": nom, 
                        "Age": age,
                        "Verdict": verdict_ia,
                        "Rapport": rapport_texte[:100] + "..." # Résumé
                    }
                    
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")

        # Bouton d'enregistrement dans le registre (une fois l'analyse faite)
        if 'last_analysis' in st.session_state:
            if st.button("💾 Enregistrer dans le registre de l'étude"):
                data = st.session_state['last_analysis']
                data["Heure"] = datetime.now().strftime("%H:%M")
                st.session_state['historique'].insert(0, data)
                del st.session_state['last_analysis'] # Nettoyage
                st.success("Données enregistrées !")
                st.rerun()

# --- REGISTRE DES DONNÉES (POUR EXPORT MASTER) ---
if st.session_state['historique']:
    st.divider()
    st.subheader("📂 Registre des examens - Yaoundé (Hôpital Jamot)")
    df = pd.DataFrame(st.session_state['historique'])
    
    # Affichage du tableau
    st.dataframe(df, use_container_width=True)
    
    # Bouton d'exportation
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=csv,
        file_name=f"donnees_recherche_jamot_{datetime.now().strftime('%d_%m_%Y')}.csv",
        mime="text/csv")
