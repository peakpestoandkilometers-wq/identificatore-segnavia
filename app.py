import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json

# Configurazione delle API di Google
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Riconoscimento Segnavia", layout="centered")

st.title("📸 Identificatore Segnavia e OSM")
st.write("Carica l'immagine del segnavia e l'app la confronterà con il database locale dei sentieri.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])
posizione_utente = st.text_input("In che regione/zona ti trovi? (es. 'Liguria')", value="Liguria")

# Funzione per caricare i dati dal file GeoJSON locale
@st.cache_data
def carica_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Nota: il file è sentieri.geojson
    json_path = os.path.join(base_dir, 'sentieri.geojson')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Il file non è stato trovato in: {json_path}. Assicurati di averlo caricato nel repository.")
        return None

# Carica i dati all'avvio
dati_sentieri = carica_database()

def cerca_su_json_locale(simbolo_letto, localita, dati_json):
    """Cerca la corrispondenza del segnavia all'interno del file GeoJSON locale."""
    if not dati_json or 'features' not in dati_json:
        return None

    simbolo_letto = simbolo_letto.lower()
    
    for feature in dati_json['features']:
        properties = feature.get('properties', {})
        osmc_symbol = properties.get('osmc:symbol', '').lower()
        nome = properties.get('name', '').lower()
        
        if simbolo_letto in osmc_symbol or simbolo_letto in nome:
            return {
                "nome": properties.get('name', 'Sentiero senza nome'),
                "ref": properties.get('ref', 'N/D'),
                "simbolo": properties.get('osmc:symbol', 'N/D')
            }
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
                        Osserva il segnavia nell'immagine e indica il simbolo o i colori (es. red:white:red).
                        Restituisci solo la parola chiave del simbolo trovata.
                        """,
                        image_file
                    ])
                    
                    simbolo_letto = response.text.strip()
                    st.info(f"Simbolo identificato dall'AI: **{simbolo_letto}**")
                    
                    st.write(f"Ricerca nel catasto locale per l'area: **{posizione_utente}**...")
                    risultato = cerca_su_json_locale(simbolo_letto, posizione_utente, dati_sentieri)
                    
                    if risultato:
                        st.success(f"✅ Trovato sul database locale: **{risultato['nome']}**")
                        st.write(f"**Codice OSMC (Segnavia):** {risultato['simbolo']}")
                        st.write(f"**Codice Sentiero:** {risultato['ref']}")
                    else:
                        st.warning("Nessuna corrispondenza esatta trovata negli itinerari archiviati nel file GeoJSON.")
                        
                except Exception as e:
                    st.error(f"Errore durante l'esecuzione: {e}")
