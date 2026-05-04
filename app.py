import streamlit as st
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Scanner Segnavia", layout="centered")

st.title("📸 Scanner Segnavia CAI")
st.write("Inquadra il segnavia o carica una foto per identificarlo all'istante.")

# Archivio locale dei sentieri
data = {
    "Codice_Identificativo": ["501", "12A", "AV", "T"],
    "Nome_Sentiero": ["Alta Via delle Grazie", "Sentiero dei Re Magi", "Alta Via dei Monti Liguri", "Tappa Tematica"],
    "Difficoltà": ["E", "EE", "EEA", "E"],
    "Regione": ["Lombardia", "Liguria", "Liguria", "Toscana"],
    "Significato": [
        "Sentiero escursionistico standard", 
        "Variante secondaria del percorso", 
        "Percorso di crinale di lunga percorrenza", 
        "Tracciato tematico locale"
    ]
}
df = pd.DataFrame(data)

# Widget fotocamera/caricamento (attiva la fotocamera su smartphone)
uploaded_file = st.file_uploader("Scatta una foto o carica l'immagine...", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Segnavia scansionato", use_column_width=True)
    
    # Campo di testo per digitare il codice (permette di correggere l'analisi al volo)
    codice_letto = st.text_input("Inserisci il codice letto o stimato (es. 501, 12A, AV):")
    
    if st.button("Avvia Scansione"):
        if not codice_letto:
            st.warning("Inserisci il codice del sentiero per verificare l'archivio.")
        else:
            # Cerca il codice nel database
            risultato = df[df["Codice_Identificativo"].str.lower() == codice_letto.lower()]
            
            if not risultato.empty:
                riga = risultato.iloc[0]
                st.success(f"✅ **Trovato nel database:** {riga['Nome_Sentiero']}")
                st.write(f"**Significato:** {riga['Significato']}")
                st.write(f"**Difficoltà:** {riga['Difficoltà']}")
                st.write(f"**Regione:** {riga['Regione']}")
            else:
                st.warning("Nessuna corrispondenza esatta trovata. Il codice potrebbe essere un segnale locale non ancora digitalizzato.")
