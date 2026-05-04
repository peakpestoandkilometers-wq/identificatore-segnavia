import streamlit as st
from PIL import Image
import numpy as np
import cv2
import os
import json

st.set_page_config(page_title="Scanner Segnavia", layout="centered")
st.title("📸 Scanner Segnavia - Modalità Live")
st.write("Inquadra il segnavia e avvia la scansione per trovare il sentiero.")

uploaded_file = st.file_uploader("Scatta o carica l'immagine del segnavia", type=["jpg", "png", "jpeg"])

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
    image = Image.open(uploaded_file)
    st.image(image, caption="Immagine acquisita", use_column_width=True)
    
    if st.button("Avvia scansione"):
        if dati_sentieri is None:
            st.error("Database non caricato. Controlla il file sentieri.geojson")
        else:
            # Converte l'immagine per l'elaborazione locale
            img_cv = np.array(image)
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
            
            # Analisi del colore dominante (es. rosso e bianco)
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            
            # Maschera per il rosso
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = mask1 + mask2
            
            # Verifica la percentuale di colore rosso per capire se il segnavia è presente
            red_pixels = np.sum(red_mask > 0)
            total_pixels = img_cv.shape[0] * img_cv.shape[1]
            red_percentage = red_pixels / total_pixels
            
            # Simula il riconoscimento visivo
            if red_percentage > 0.05: # Soglia minima di rosso trovata
                st.info("Riconosciuto segnavia con dominanza rossa. Ricerca nel database in corso...")
                trovati = []
                
                for feature in dati_sentieri['features']:
                    properties = feature.get('properties', {})
                    osmc = str(properties.get('osmc:symbol', '')).lower()
                    
                    if "red" in osmc:
                        trovati.append(properties)
                        
                if trovati:
                    st.success(f"Trovato {len(trovati)} sentiero compatibile:")
                    for t in trovati[:3]:
                        st.write(f"**Nome:** {t.get('name')}")
                        st.write(f"**Codice:** {t.get('ref')}")
                        st.write(f"**OSMC:** {t.get('osmc:symbol')}")
                        st.write("---")
                else:
                    st.warning("Nessun sentiero associato al rosso trovato nel database.")
            else:
                st.warning("Impossibile rilevare un segnale escursionistico chiaro nell'immagine.")
