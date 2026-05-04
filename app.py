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
st.write("L'AI identifica il segnavia e cerca gli itinerari escursionistici su OpenStreetMap.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

def cerca_itinerari_osm(descrizione_simbolo):
    """Interroga il database di OpenStreetMap per tutti gli itinerari escursionistici (route=hiking)."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query che cerca tutti gli itinerari escursionistici nell'area
    overpass_query = f"""
    [out:json];
    relation["route"="hiking"];
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=5)
        data = response.json()
        
        if 'elements' in data and len(data['elements']) > 0:
            # Filtriamo i risultati per trovare quelli che contengono la parola chiave del simbolo
            for rel in data['elements']:
                symbol_tag = rel.get('tags', {}).get('osmc:symbol', '')
                if descrizione_simbolo.lower() in symbol_tag.lower() or 'circle' in symbol_tag.lower():
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
                # 1. Gemini identifica il simbolo e prova a tradurlo in tag
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                response = model.generate_content([
                    """
                    Sei un assistente esperto di escursionismo CAI. 
                    Guarda il segnavia nell'immagine. Identifica il simbolo e indica il colore e la forma (es. cerchio, triangolo).
                    Rispondi solo con la parola chiave inglese o italiana della forma (es. "circle", "triangle").
                    """,
                    image_file
                ])
                
                simbolo_letto = response.text.strip()
                st.info(f"Simbolo standardizzato dall'AI: **{simbolo_letto}**")
                
                # 2. Interroghiamo OpenStreetMap
                st.write("Ricerca nel database degli itinerari escursionistici...")
                risultato_osm = cerca_itinerari_osm(simbolo_letto)
                
                if risultato_osm:
                    st.success(f"✅ Trovato su OSM: **{risultato_osm['nome']}**")
                    st.write(f"👉 [Apri su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?id={risultato_osm['id']})")
                else:
                    st.warning("Nessuna corrispondenza trovata su OpenStreetMap per questo simbolo. Il percorso potrebbe non essere ancora stato tracciato nella mappa OSM.")
                    
            except Exception as e:
                st.error(f"Errore durante l'analisi: {e}")
