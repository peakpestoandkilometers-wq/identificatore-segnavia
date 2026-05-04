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

st.set_page_config(page_title="Riconoscimento Segnavia CAI", layout="centered")

st.title("📸 Identificatore Segnavia CAI e OSM")
st.write("Scatta o carica l'immagine del segnavia: l'AI lo convertirà nel formato OSMC per interrogarlo su OSM.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

def cerca_su_osm_osmc(simbolo_osmc):
    """Interroga il database OSM per trovare l'itinerario tramite il tag osmc:symbol."""
    # Cerchiamo in modo flessibile utilizzando il parametro regex (~)
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    relation["osmc:symbol"~"{simbolo_osmc}", i]["route"="hiking"];
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=6)
        data = response.json()
        
        if 'elements' in data and len(data['elements']) > 0:
            rel = data['elements'][0]
            return {
                "nome": rel.get('tags', {}).get('name', 'Sentiero senza nome'),
                "id": rel['id'],
                "simbolo_trovato": rel.get('tags', {}).get('osmc:symbol', 'N/D')
            }
    except:
        pass
    return None

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza e confronta con OSM"):
        with st.spinner("Analisi in corso..."):
            try:
                # 1. Chiediamo a Gemini di estrarre il simbolo e convertirlo nel formato (es. circle, bar, red)
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                response = model.generate_content([
                    """
                    Sei un assistente esperto di cartografia CAI e OpenStreetMap.
                    Osserva il segnavia nell'immagine e, basandoti sulla sintassi di osmc:symbol (es. "circle", "bar", "diamond"), 
                    individua forma e colore per formare una stringa da cercare (es. "red_circle", "red_bar", "white_circle").
                    Rispondi solo con la parola chiave esatta della forma, es: "circle" o "bar".
                    """,
                    image_file
                ])
                
                simbolo_letto = response.text.strip()
                st.info(f"Simbolo standardizzato dall'AI: **{simbolo_letto}**")
                
                st.write("Interrogazione del catasto escursionistico OSM...")
                risultato = cerca_su_osm_osmc(simbolo_letto)
                
                if risultato:
                    st.success(f"✅ Trovato su OSM: **{risultato['nome']}**")
                    st.write(f"**Codice OSMC:** {risultato['simbolo_trovato']}")
                    st.write(f"👉 [Apri su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?id={risultato['id']})")
                else:
                    st.warning("Nessuna corrispondenza trovata su OpenStreetMap per questo simbolo.")
                    st.write("Il sentiero potrebbe non avere ancora la codifica OSMC associata nel database.")
                    
            except Exception as e:
                st.error(f"Errore durante l'analisi: {e}")
