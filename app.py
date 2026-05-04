import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import os

# Configurazione API Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Identificatore Segnavia", layout="centered")

st.title("📸 Riconoscimento Segnavia CAI Integrato")
st.write("L'AI analizza l'immagine e interroga il database per verificare la corrispondenza.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

def cerca_su_osm(codice_sentiero):
    """Interroga l'API di OpenStreetMap per trovare il nome del sentiero."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    relation["ref"="{codice_sentiero}"]["route"="hiking"];
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=5)
        data = response.json()
        if 'elements' in data and len(data['elements']) > 0:
            rel = data['elements'][0]
            return rel.get('tags', {}).get('name', 'Nome non disponibile')
    except:
        pass
    return None

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza e Verifica"):
        with st.spinner("Analisi in corso..."):
            try:
                # Interrogazione di Gemini
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                response = model.generate_content([
                    """
                    Sei un assistente esperto di escursionismo. 
                    Analizza l'immagine e individua il codice del sentiero CAI (es. 501, 12A, 1).
                    Rispondi solo con il codice (es. "501"). Se non trovi un codice o non è chiaro, scrivi "Non trovato".
                    """,
                    image
                ])
                
                codice_trovato = response.text.strip()
                st.info(f"Codice identificato da Gemini: **{codice_trovato}**")
                
                if codice_trovato != "Non trovato":
                    st.write("Verifica del sentiero su OpenStreetMap...")
                    nome_osm = cerca_su_osm(codice_trovato)
                    
                    if nome_osm:
                        st.success(f"✅ Trovato su OSM: **{nome_osm}**")
                        st.write(f"👉 [Visualizza su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?ref={codice_trovato})")
                    else:
                        st.warning("Il codice non è presente su OpenStreetMap, ma l'AI ha riconosciuto il segnavia nell'immagine.")
                else:
                    st.warning("Gemini non ha trovato un codice numerico chiaro nell'immagine.")
                    
            except Exception as e:
                st.error(f"Errore: {e}")
