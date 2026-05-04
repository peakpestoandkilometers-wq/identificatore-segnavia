import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Configura l'API di Gemini (la chiave è salvata nei segreti di Streamlit)
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Identificatore Segnavia", layout="centered")
st.title("📸 Riconoscimento Segnavia CAI")
st.write("Carica una foto del segnavia per identificarne il significato.")

# Widget per caricare l'immagine
uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Identifica Segnavia"):
        with st.spinner("Analisi in corso..."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Invio dell'immagine al modello
            response = model.generate_content([
                "Identifica questo segnavia di sentiero montano. Fornisci il nome, il significato e il grado di confidenza.",
                image
            ])
            
            st.success("Analisi completata!")
            st.write(response.text)
