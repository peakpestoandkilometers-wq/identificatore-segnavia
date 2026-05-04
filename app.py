import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import os

# Configurazione delle API di Google
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Riconoscimento Segnavia", layout="centered")

st.title("📸 Identificatore Segnavia CAI e OSM")
st.write("Carica l'immagine del segnavia. L'AI lo identificherà e cercherà il percorso su OpenStreetMap.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

def cerca_su_osm_simbolo(descrizione_simbolo):
    """Interroga il database di OpenStreetMap cercando i sentieri in base al simbolo."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query che cerca i sentieri in base ai tag del simbolo (es. triangolo, rosso)
    overpass_query = f"""
    [out:json];
    relation["osmc:symbol"~"{descrizione_simbolo}", i]["route"="hiking"];
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=5)
        data = response.json()
        if 'elements' in data and len(data['elements']) > 0:
            rel = data['elements'][0]
            return {
                "nome": rel.get('tags', {}).get('name', 'Sentiero senza nome'),
                "id": rel['id']
            }
    except:
        pass
    return None

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza con OSM"):
        with st.spinner("Analisi in corso..."):
            try:
                # 1. Gemini identifica la forma del segnale
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                response = model.generate_content([
                    """
                    Sei un assistente esperto di escursionismo CAI. 
                    Guarda il segnavia nell'immagine e descrivine il simbolo principale e il colore (es. "red:white:triangle" o "doppia barra rossa").
                    Rispondi solo con la descrizione del simbolo. Non aggiungere altro testo.
                    """,
                    image_file
                ])
                
                simbolo_letto = response.text.strip()
                st.info(f"Simbolo identificato dall'AI: **{simbolo_letto}**")
                
                # 2. Interroghiamo OpenStreetMap
                st.write("Ricerca nel database di OpenStreetMap...")
                risultato_osm = cerca_su_osm_simbolo(simbolo_letto)
                
                if risultato_osm:
                    st.success(f"✅ Trovato su OSM: **{risultato_osm['nome']}**")
                    st.write(f"👉 [Apri su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?id={risultato_osm['id']})")
                else:
                    st.warning("Nessuna corrispondenza trovata su OpenStreetMap per questo specifico simbolo.")
                    
            except Exception as e:
                st.error(f"Errore durante l'analisi: {e}")
