import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import os

# Configurazione API Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Identificatore Segnavia", layout="centered")

st.title("📸 Riconoscimento Segnavia CAI con OSM")
st.write("Carica una foto del segnavia per identificarlo e verificare il percorso su OpenStreetMap.")

uploaded_file = st.file_uploader("Scegli un'immagine...", type=["jpg", "png", "jpeg"])

def cerca_su_osm(codice_sentiero):
    """Interroga l'API di OpenStreetMap per trovare il sentiero."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query per cercare una relazione con un determinato ref (es. numero del sentiero)
    overpass_query = f"""
    [out:json];
    relation["ref"="{codice_sentiero}"]["route"="hiking"];
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=10)
        data = response.json()
        
        if 'elements' in data and len(data['elements']) > 0:
            rel = data['elements'][0]
            nome = rel.get('tags', {}).get('name', 'Sentiero senza nome')
            osm_id = rel['id']
            return {"nome": nome, "id": osm_id}
    except Exception as e:
        return None
    return None

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Segnavia caricato", use_column_width=True)
    
    if st.button("Identifica con OSM"):
        with st.spinner("Analisi in corso..."):
            try:
                # 1. Identificazione tramite Gemini
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                response = model.generate_content([
                    """
                    Sei un assistente esperto di escursionismo. Identifica il codice numerico del sentiero CAI (es. 501, 12A) dall'immagine.
                    Restituisci solo il numero del codice del sentiero se chiaro. Altrimenti scrivi 'Non trovato'.
                    """,
                    image
                ])
                
                risultato_ai = response.text.strip()
                st.subheader("Esito dell'analisi AI:")
                st.info(f"Codice individuato: {risultato_ai}")
                
                # 2. Controllo e arricchimento con OpenStreetMap
                if risultato_ai != 'Non trovato':
                    st.write("Verifica in corso su OpenStreetMap...")
                    osm_data = cerca_su_osm(risultato_ai)
                    
                    if osm_data:
                        st.success(f"✅ Trovato su OSM: **{osm_data['nome']}**")
                        st.write(f"ID Relazione OSM: {osm_data['id']}")
                        st.write(f"👉 [Visualizza su Waymarked Trails](https://hiking.waymarkedtrails.org/#route?id={osm_data['id']})")
                    else:
                        st.warning("Il sentiero non è presente nel database mondiale di OSM oppure il codice non corrisponde.")
                else:
                    st.warning("Impossibile procedere con la ricerca su OSM senza un codice valido.")
                    
            except Exception as e:
                st.error(f"Errore: {e}")
