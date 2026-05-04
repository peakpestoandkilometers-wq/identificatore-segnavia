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

st.title("📸 Identificatore Segnavia e OSM")
st.write("Inserisci la tua posizione e carica l'immagine del segnavia per cercarlo su OpenStreetMap.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])
posizione_utente = st.text_input("In che regione/zona ti trovi? (es. 'Liguria', 'Val Seriana')")

def cerca_su_osm_localizzato(simbolo_letto, localita):
    """Interroga il database OSM limitando la ricerca all'area definita dall'utente."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query che interroga gli elementi escursionistici
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
                osmc_symbol = tags.get('osmc:symbol', '').lower()
                name = tags.get('name', '').lower()
                
                # Confronta il simbolo letto e la località
                if simbolo_letto.lower() in osmc_symbol or name:
                    return {
                        "nome": tags.get('name', 'Sentiero senza nome'),
                        "id": element['id'],
                        "simbolo": tags.get('osmc:symbol', 'N/D')
                    }
    except:
        pass
    return None

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza e confronta"):
        if not posizione_utente:
            st.warning("Inserisci la tua posizione per procedere con l'analisi mirata.")
        else:
            with st.spinner("Analisi in corso..."):
                try:
                    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                    response = model.generate_content([
                        f"""
                        Sei un esperto di escursionismo CAI.
                        Osserva il segnavia nell'immagine e indica la forma e il colore (es. circle, red_bar).
                        Restituisci solo la parola chiave del simbolo, es: "circle" o "bar".
                        """,
                        image_file
                    ])
                    
                    simbolo_letto = response.text.strip()
                    st.info(f"Simbolo identificato dall'AI: **{simbolo_letto}**")
                    
                    st.write(f"Ricerca nel catasto per l'area: **{posizione_utente}**...")
                    risultato = cerca_su_osm_localizzato(simbolo_letto, posizione_utente)
                    
                    if risultato:
                        st.success(f"✅ Trovato su OSM: **{risultato['nome']}**")
                        st.write(f"**Codice OSMC:** {risultato['simbolo']}")
                        st.write(f"👉 [Apri su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?id={risultato['id']})")
                    else:
                        st.warning("Nessuna corrispondenza esatta trovata negli itinerari archiviati.")
                        
                except Exception as e:
                    st.error(f"Errore durante l'esecuzione: {e}")
