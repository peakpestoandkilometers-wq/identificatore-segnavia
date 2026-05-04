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

# Carica il database da file
@st.cache_data
def carica_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'sentieri.geojson')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Il file non è stato trovato in: {json_path}. Assicurati di averlo caricato.")
        return None

dati_sentieri = carica_database()

def normalizza_stringa(testo):
    """Converte le descrizioni in linguaggio naturale nel formato logico OSMC."""
    testo = str(testo).lower().strip()
    
    # Mappatura delle variabili più frequenti nei sentieri
    sostituzioni = {
        "cerchio": "round",
        "cerchio bianco": "white_round",
        "rombo": "diamond",
        "quadrato": "square",
        "croce": "cross",
        "triangolo": "triangle",
        "barra": "bar",
        "linea": "bar",
        "bianco e rosso": "red:white:red",
        "a rossa": "a",
        "rossa": "red",
        "bianco": "white"
    }
    
    for chiave, valore in sostituzioni.items():
        if chiave in testo:
            testo = testo.replace(chiave, valore)
            
    return testo

def cerca_su_json_locale(simbolo_letto, localita, dati_json):
    """Cerca la corrispondenza del segnavia analizzando tutte le features del file."""
    if not dati_json or 'features' not in dati_json:
        return None

    simbolo_normalizzato = normalizza_stringa(simbolo_letto)

    for feature in dati_json['features']:
        properties = feature.get('properties', {})
        
        # Estrae tutte le variabili di interesse
        osmc_symbol = str(properties.get('osmc:symbol', '')).lower()
        nome = str(properties.get('name', '')).lower()
        ref = str(properties.get('ref', '')).lower()
        simbolo_it = str(properties.get('symbol:it', '')).lower()
        
        # Controlla se una delle variabili corrisponde all'input
        if (simbolo_normalizzato in osmc_symbol or 
            simbolo_normalizzato in nome or 
            simbolo_normalizzato in ref or
            simbolo_normalizzato in simbolo_it):
            
            return {
                "nome": properties.get('name', 'Sentiero senza nome'),
                "ref": properties.get('ref', 'N/D'),
                "simbolo": properties.get('osmc:symbol', 'N/D'),
                "simbolo_it": properties.get('symbol:it', 'N/D')
            }
            
    return None

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    simbolo_manuale = st.text_input("Se hai raggiunto il limite dell'AI, inserisci il segnavia manualmente (es. red:white:red o 'a rossa su cerchio bianco'):")
    
    if st.button("Analizza e confronta") or simbolo_manuale:
        simbolo_letto = simbolo_manuale
        
        if not simbolo_manuale:
            with st.spinner("Analisi in corso..."):
                try:
                    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                    response = model.generate_content([
                        "Osserva l'immagine del segnavia e restituisci la descrizione sintetica del simbolo (es. A rossa, cerchio bianco, rombo rosso).",
                        image_file
                    ])
                    simbolo_letto = response.text.strip()
                except:
                    st.error("Errore con l'AI, inserisci il dato manualmente.")
                    
        if simbolo_letto:
            st.info(f"Simbolo identificato (Originale): **{simbolo_letto}**")
            risultato = cerca_su_json_locale(simbolo_letto, posizione_utente, dati_sentieri)
            
            if risultato:
                st.success(f"✅ Trovato sul database locale: **{risultato['nome']}**")
                st.write(f"**Codice OSMC:** {risultato['simbolo']}")
                st.write(f"**Codice Sentiero:** {risultato['ref']}")
                st.write(f"**Descrizione in IT:** {risultato['simbolo_it']}")
            else:
                st.warning("Nessuna corrispondenza trovata con questo segnavia nel file GeoJSON.")
