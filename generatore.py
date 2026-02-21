import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os

st.set_page_config(page_title="Generatore Preventivi", layout="wide")
st.title("📄 Realizzatore di Offerte")

file_path = 'Listino_agente.xlsx'

if not os.path.exists(file_path):
    st.error(f"File {file_path} non trovato!")
else:
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()

    ricerca = st.sidebar.text_input("Cerca ARTICOLO:").upper()

    if ricerca:
        risultato = df[df['ARTICOLO'].astype(str).str.contains(ricerca, na=False)]
        
        if not resultado.empty:
            scelta = st.selectbox("Seleziona l'articolo:", risultato['ARTICOLO'])
            d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
            
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Dettagli")
                st.write(f"**Modello:** {d['ARTICOLO']}")
                st.write(f"**Taglie:** {d['RANGE TAGLIE']}")
                st.write(f"**Prezzo:** {d['LISTINO']} €")
            
            with col2:
                st.subheader("Immagine")
                url_img = str(d['IMMAGINE']).strip()
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res = requests.get(url_img, headers=headers, timeout=10)
                    if res.status_code == 200:
                        st.image(BytesIO(res.content), use_container_width=True)
                    else:
                        st.write(f"🔗 [Vedi Foto nel Browser]({url_img})")
                except:
                    st.write(f"🔗 [Link Immagine]({url_img})")
