import streamlit as st
import os
import json

st.set_page_config(page_title="Scanner Segnavia", layout="centered")
st.title("📸 Scanner Segnavia - Modalità Semplificata")
st.write("Carica l'immagine o inserisci il segnavia per trovare il sentiero associato.")

uploaded_file = st.file_uploader("Carica immagine", type=["jpg", "png", "jpeg"])

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

testo_manuale = st.text_input("Inserisci il codice del segnavia (es. red:white:red o 'a rossa'):")

if st.button("Cerca nel database") or testo_manuale:
    if dati_sentieri is None:
        st.error("File sentieri.geojson non trovato nel repository.")
    else:
        chiave_ricerca = (testo_manuale).lower().strip()
        trovati = []
        
        for feature in dati_sentieri['features']:
            properties = feature.get('properties', {})
            osmc_symbol = str(properties.get('osmc:symbol', '')).lower()
            nome = str(properties.get('name', '')).lower()
            simbolo_it = str(properties.get('symbol:it', '')).lower()
            ref = str(properties.get('ref', '')).lower()
            
            if (chiave_ricerca in osmc_symbol or 
                chiave_ricerca in nome or 
                chiave_ricerca in simbolo_it or 
                chiave_ricerca in ref):
                trovati.append(properties)
                
        if trovati:
            st.success(f"Trovati {len(trovati)} sentieri compatibili:")
            for t in trovati[:3]:
                st.write(f"**Nome:** {t.get('name')}")
                st.write(f"**Codice:** {t.get('ref')}")
                st.write(f"**OSMC:** {t.get('osmc:symbol')}")
                st.write("---")
        else:
            st.warning("Nessun sentiero trovato con i parametri inseriti.")
