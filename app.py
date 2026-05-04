import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json

st.set_page_config(page_title="Riconoscimento Segnavia", layout="centered")

st.title("📸 Identificatore Segnavia")
st.write("Carica la foto del segnavia e l'AI la confronterà con il catasto sentieri.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

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
    
    # Configura l'API Key
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    
    if st.button("Analizza con l'AI"):
        with st.spinner("Analisi visiva in corso..."):
            try:
                # Modello aggiornato a 1.5 Flash
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                response = model.generate_content([
                    "Osserva l'immagine e restituisci solo la descrizione del simbolo (es. triangolo rosso, cerchio bianco, rombo rosso).",
                    image_file
                ])
                
                simbolo_letto = response.text.strip()
                st.info(f"Simbolo identificato dall'AI: **{simbolo_letto}**")
                
                if dati_sentieri is None:
                    st.warning("Il database (sentieri.geojson) non è stato trovato.")
                else:
                    trovati = []
                    chiave = simbolo_letto.lower()
                    
                    for feature in dati_sentieri.get('features', []):
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
                            st.write(f"**Nome:** {t.get('name')} | **Codice:** {t.get('ref')}")
                            st.write(f"**OSMC:** {t.get('osmc:symbol')}")
                            st.write("---")
                    else:
                        st.warning("Nessun sentiero trovato per questo segnavia nel file.")
                        
            except Exception as e:
                st.error("Hai raggiunto il limite giornaliero dell'API. Inserisci il codice manualmente per proseguire il test:")
                testo_manuale = st.text_input("Inserisci il codice OSMC (es. red:white:red):")
                if st.button("Cerca manualmente"):
                    chiave_man = testo_manuale.lower().strip()
                    trovati_man = [
                        f.get('properties') for f in dati_sentieri.get('features', [])
                        if chiave_man in str(f.get('properties', {}).get('osmc:symbol', '')).lower()
                    ]
                    if trovati_man:
                        st.success("Trovato:")
                        st.write(f"**Nome:** {trovati_man[0].get('name')}")
