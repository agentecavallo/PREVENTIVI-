import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os

# Configurazione della pagina
st.set_page_config(page_title="Generatore Preventivi", layout="wide")
st.title("📄 Realizzatore di Offerte")

# Nome del tuo file Excel (assicurati che si chiami esattamente così a sinistra)
file_path = 'Listino_agente.xlsx'

# Controlliamo se il file esiste
if not os.path.exists(file_path):
    st.error(f"❌ File '{file_path}' non trovato nella colonna a sinistra!")
    st.info("Trascina il file Excel dentro GitHub Codespaces per continuare.")
else:
    # Carichiamo i dati
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip() # Puliamo i nomi delle colonne

    # Barra di ricerca nella colonna laterale
    st.sidebar.header("Filtri")
    ricerca = st.sidebar.text_input("Cerca ARTICOLO (es. nome o codice):").upper()

    if ricerca:
        # Cerchiamo l'articolo nel foglio Excel
        risultato = df[df['ARTICOLO'].astype(str).str.contains(ricerca, na=False)]
        
        if not risultato.empty:
            # Se ci sono più risultati, facciamo scegliere quello esatto
            scelta = st.selectbox("Seleziona l'articolo esatto:", risultato['ARTICOLO'])
            d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
            
            st.divider()
            
            # Creiamo due colonne per la visualizzazione
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📋 Dettagli Prodotto")
                st.write(f"**Modello:** {d['ARTICOLO']}")
                st.write(f"**Range Taglie:** {d['RANGE TAGLIE']}")
                st.markdown(f"### Prezzo: {d['LISTINO']} €")
                
                # Spazio per eventuali note o tasti futuri
                st.info("Puoi usare lo screenshot di questa pagina per inviare l'offerta rapida.")

            with col2:
                st.subheader("📸 Immagine")
                url_img = str(d['IMMAGINE']).strip()
                
                if url_img.lower().startswith('http'):
                    try:
                        # Simuliamo un browser per scaricare l'immagine (evita blocchi)
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        res = requests.get(url_img, headers=headers, timeout=10)
                        if res.status_code == 200:
                            st.image(BytesIO(res.content), caption=d['ARTICOLO'], use_container_width=True)
                        else:
                            st.warning("⚠️ Il sito non permette la visualizzazione automatica.")
                            st.write(f"[Clicca qui per vedere la foto]({url_img})")
                    except Exception as e:
                        st.error("Errore nel caricamento dell'immagine.")
                        st.write(f"🔗 [Link Diretto Foto]({url_img})")
                else:
                    st.warning("Nessun link immagine trovato per questo articolo.")
        else:
            st.warning("Nessun articolo trovato con questo nome.")
    else:
        st.info("👈 Digita il nome di un articolo nella barra a sinistra per iniziare.")
