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

st.title("📸 Identificatore Segnavia - Modalità Originale")
st.write("Carica la foto del segnavia e l'AI la confronterà con il catasto sentieri.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

# Funzione per caricare il database
@st.cache_data
def carica_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'sentieri.geojson')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

dati_sentieri = carica_database()

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza immagine"):
        if dati_sentieri is None:
            st.error("Il file sentieri.geojson non è stato trovato nel repository.")
        else:
            with st.spinner("Analisi visiva in corso..."):
                try:
                    # Uso del modello per l'analisi dell'immagine
                    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                    response = model.generate_content([
                        """
                        Sei un esperto escursionista. Osserva il segnavia nell'immagine e 
                        restituisci una descrizione sintetica del simbolo trovato (es. triangolo rosso, 
                        rombo rosso, cerchio bianco, A rossa su cerchio).
                        """,
                        image_file
                    ])
                    
                    simbolo_letto = response.text.strip()
                    st.info(f"Simbolo identificato dall'AI: **{simbolo_letto}**")
                    
                    # Ricerca nel database
                    trovati = []
                    chiave = simbolo_letto.lower()
                    
                    for feature in dati_sentieri['features']:
                        properties = feature.get('properties', {})
                        osmc = str(properties.get('osmc:symbol', '')).lower()
                        nome = str(properties.get('name', '')).lower()
                        simbolo_it = str(properties.get('symbol:it', '')).lower()
                        ref = str(properties.get('ref', '')).lower()
                        
                        if (chiave in osmc or chiave in nome or chiave in simbolo_it or chiave in ref):
                            trovati.append(properties)
                            
                    if trovati:
                        st.success(f"Trovati {len(trovati)} sentieri compatibili:")
                        for t in trovati[:3]:
                            st.write(f"**Nome:** {t.get('name')}")
                            st.write(f"**Codice:** {t.get('ref')}")
                            st.write(f"**Codice OSMC:** {t.get('osmc:symbol')}")
                            st.write("---")
                    else:
                        st.warning("Nessuna corrispondenza trovata con questo segnavia nel file GeoJSON.")
                        
                except Exception as e:
                    st.error("Errore di quota raggiunto (20/20) o richiesta non valida. Riprova con un'altra immagine o usa la stringa manuale sottostante.")
                    
                    # Opzione di fallback per proseguire i test
                    testo_manuale = st.text_input("Inserisci il simbolo manualmente per bypassare l'AI:")
                    if st.button("Cerca manualmente"):
                        chiave_man = testo_manuale.lower().strip()
                        trovati_man = []
                        for f in dati_sentieri['features']:
                            p = f.get('properties', {})
                            if chiave_man in str(p.get('osmc:symbol', '')).lower() or chiave_man in str(p.get('symbol:it', '')).lower():
                                trovati_man.append(p)
                        
                        if trovati_man:
                            st.success(f"Trovati {len(trovati_man)} sentieri:")
                            for t in trovati_man[:3]:
                                st.write(f"**Nome:** {t.get('name')} | **Codice:** {t.get('ref')}")
