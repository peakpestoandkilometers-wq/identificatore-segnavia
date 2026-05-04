import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# Configura l'API di Gemini usando i Secrets di Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    # Fallback per il test in locale
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Identificatore Segnavia", layout="centered")

# Intestazione della pagina
st.title("📸 Riconoscimento Segnavia CAI")
st.write("Carica una foto del segnavia per identificarne il significato e la classificazione escursionistica.")

# Widget per caricare l'immagine
uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Mostra l'immagine caricata
    image = Image.open(uploaded_file)
    st.image(image, caption="Segnavia caricato", use_column_width=True)
    
    # Pulsante di analisi
    if st.button("Identifica Segnavia"):
        with st.spinner("Analisi del segnavia in corso..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Invio dell'immagine con il prompt strutturato
                response = model.generate_content([
                    """
                    Sei un assistente esperto di escursionismo e cartografia. Analizza l'immagine del segnavia e rispondi seguendo questo schema:
                    - 🎯 Tipologia:
                    - ℹ️ Significato CAI:
                    - 🔢 Codice sentiero:
                    - 🛡️ Consiglio di sicurezza:
                    - ⚖️ Confidenza AI:
                    """,
                    image
                ])
                
                st.success("Analisi completata!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Si è verificato un errore durante l'analisi: {e}")
