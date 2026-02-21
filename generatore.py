import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os

st.set_page_config(page_title="Generatore Preventivi", layout="wide")

# 1. Controllo esistenza file
file_path = 'Listino_agente.xlsx'

if not os.path.exists(file_path):
    st.error(f"⚠️ Il file '{file_path}' non esiste nella cartella di sinistra!")
    st.stop()

# 2. Caricamento dati con gestione errori
try:
    df = pd.read_excel(file_path)
    # Puliamo i nomi delle colonne da spazi invisibili
    df.columns = [str(c).strip().upper() for c in df.columns]
except Exception as e:
    st.error(f"❌ Errore nel leggere l'Excel: {e}")
    st.stop()

st.title("📄 Realizzatore di Offerte")

# 3. Verifica colonne presenti (Debug)
colonne_necessarie = ['ARTICOLO', 'LISTINO', 'IMMAGINE']
colonne_presenti = df.columns.tolist()

missing = [c for c in colonne_necessarie if c not in colonne_presenti]
if missing:
    st.warning(f"Attenzione! Nel tuo Excel mancano (o sono scritte male) queste colonne: {missing}")
    st.write("Le colonne che ho trovato nel tuo file sono:", colonne_presenti)
    st.stop()

# 4. Interfaccia di ricerca
ricerca = st.sidebar.text_input("Cerca ARTICOLO:").upper()

if ricerca:
    # Filtro: cerchiamo in ARTICOLO
    risultato = df[df['ARTICOLO'].astype(str).str.upper().str.contains(ricerca, na=False)]
    
    if not resultado.empty if 'resultado' in locals() else not risultato.empty:
        scelta = st.selectbox("Seleziona l'articolo:", risultato['ARTICOLO'].unique())
        d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
        
        st.divider()
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Dettagli Prodotto")
            st.write(f"**Modello:** {d['ARTICOLO']}")
            # Usiamo .get per evitare errori se manca RANGE TAGLIE
            taglie = d.get('RANGE TAGLIE', 'N/D')
            st.write(f"**Taglie:** {taglie}")
            st.markdown(f"## Prezzo: {d['LISTINO']} €")
            
        with c2:
            st.subheader("Foto")
            url = str(d['IMMAGINE']).strip()
            if url.startswith('http'):
                try:
                    h = {'User-Agent': 'Mozilla/5.0'}
                    r = requests.get(url, headers=h, timeout=5)
                    st.image(BytesIO(r.content), use_container_width=True)
                except:
                    st.write(f"🔗 [Link Immagine]({url})")
            else:
                st.info("Nessun link immagine valido.")
    else:
        st.warning("Nessun articolo trovato.")
else:
    st.info("Inserisci il nome di un articolo a sinistra.")
