import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# Configurazione API Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Identificatore Segnavia", layout="centered")

st.title("📸 Riconoscimento Segnavia CAI")
st.write("Carica una foto del segnavia e indica la tua posizione per un'analisi mirata.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

# Inseriamo un campo di testo per far inserire all'utente la posizione/regione
posizione_utente = st.text_input("In quale zona o regione ti trovi? (es. 'Dolomiti, Veneto' o 'Appennino Tosco-Emiliano')", "")

if uploaded_file is not None:
    image_file = Image.open(uploaded_file)
    st.image(image_file, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Analizza Segnavia"):
        if not posizione_utente:
            st.warning("Per favore, inserisci la tua posizione per restringere il campo.")
        else:
            with st.spinner("Analisi del segnavia in corso..."):
                try:
                    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                    
                    # Prompt arricchito con la posizione
                    prompt = f"""
                    Sei un assistente esperto di escursionismo e cartografia CAI.
                    Analizza l'immagine e la posizione indicata dall'utente: {posizione_utente}.
                    
                    Rispondi seguendo questo schema chiaro e discorsivo:
                    
                    - 🎯 Tipologia segnavia:
                    - ℹ️ Significato locale (riferito a {posizione_utente}):
                    - 🔢 Codice sentiero stimato:
                    - 🛡️ Consigli di sicurezza per questa zona:
                    """
                    
                    response = model.generate_content([
                        prompt,
                        image_file
                    ])
                    
                    st.success("Analisi completata!")
                    st.write(response.text)
                    
                except Exception as e:
                    st.error(f"Si è verificato un errore: {e}")
