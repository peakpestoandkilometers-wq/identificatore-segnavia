import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import os

# Configurazione API Google
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Riconoscimento Segnavia CAI", layout="centered")

st.title("📸 Identificatore Segnavia e OSM")
st.write("L'AI analizza il simbolo e interroga il catasto escursionistico di OpenStreetMap.")

uploaded_file = st.file_uploader("Carica l'immagine del segnavia...", type=["jpg", "png", "jpeg"])

def cerca_su_osm(simbolo_letto):
    """Interroga il database OSM per trovare l'itinerario corrispondente."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query che cerca tutte le relazioni escursionistiche e controlla il simbolo
    overpass_query = f"""
    [out:json];
    relation["route"="hiking"];
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=6)
        data = response.json()
        
        if 'elements' in data:
            for element in data['elements']:
                tags = element.get('tags', {})
                osmc_symbol = tags.get('osmc:symbol', '')
                
                # Controllo di corrispondenza tra quanto letto dall'AI e i dati OSM
                if simbolo_letto.lower() in osmc_symbol.lower() or osmc_symbol.lower() in simbolo_letto.lower():
                    return {
                        "nome": tags.get('name', 'Sentiero senza nome'),
                        "id": element['id']
                    }
    except:
        pass
    return None

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza e confronta con OSM"):
        with st.spinner("Analisi e interrogazione in corso..."):
            try:
                # 1. Chiediamo a Gemini di descrivere il simbolo in formato standard (es. circle, red_bar, ecc.)
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                response = model.generate_content([
                    """
                    Sei un esperto di cartografia CAI. 
                    Guarda l'immagine e individua il simbolo del sentiero.
                    Restituisci solo il nome o la descrizione del simbolo (es. "circle", "triangle", "bar").
                    """,
                    image_file
                ])
                
                simbolo_letto = response.text.strip()
                st.info(f"Simbolo identificato dall'AI: **{simbolo_letto}**")
                
                # 2. Interrogazione del database
                st.write("Confronto con gli itinerari escursionistici di OpenStreetMap...")
                risultato = cerca_su_osm(simbolo_letto)
                
                if risultato:
                    st.success(f"✅ Trovato su OSM: **{risultato['nome']}**")
                    st.write(f"👉 [Visualizza su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?id={risultato['id']})")
                else:
                    st.warning("Nessuna corrispondenza esatta trovata negli itinerari archiviati.")
                    st.write("Il simbolo potrebbe non essere ancora stato digitalizzato su OpenStreetMap con la codifica esatta.")
                    
            except Exception as e:
                st.error(f"Errore durante l'esecuzione: {e}")
