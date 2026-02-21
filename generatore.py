import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Generatore Preventivi", layout="wide")

st.title("📄 Realizzatore di Offerte")

# Nome del file AGGIORNATO con la maiuscola
file_path = 'Listino_agente.xlsx'

if not os.path.exists(file_path):
    st.error(f"❌ Non trovo il file: {file_path}")
    st.info(f"File presenti nella cartella: {os.listdir()}")
else:
    try:
        # Carichiamo i dati
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip() # Pulizia nomi colonne
        
        # Barra laterale per la ricerca
        st.sidebar.header("Ricerca Prodotti")
        ricerca = st.sidebar.text_input("Inserisci nome ARTICOLO:").upper()

        if ricerca:
            # Filtriamo (senza considerare la colonna A)
            risultato = df[df['ARTICOLO'].astype(str).str.contains(ricerca, na=False)]
            
            if not risultato.empty:
                # Tabella riassuntiva
                st.write("### Risultati trovati:")
                st.dataframe(risultato[['ARTICOLO', 'RANGE TAGLIE', 'LISTINO', 'IMMAGINE']])
                
                # Selezione singola
                scelta = st.selectbox("Scegli l'articolo esatto per il preventivo:", risultato['ARTICOLO'])
                d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
                
                st.divider()
                
                # Visualizzazione finale
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Scheda: {d['ARTICOLO']}")
                    st.write(f"**Range Taglie:** {d['RANGE TAGLIE']}")
                    st.write(f"**Prezzo Unitario:** {d['LISTINO']} €")
                
                with col2:
                    st.subheader("Immagine Prodotto")
                    
                    # Prendiamo il link dalla colonna IMMAGINE
                    url_immagine = d['IMMAGINE']
                    
                    # Verifichiamo se il link esiste e non è vuoto
                    if pd.notna(url_immagine) and str(url_immagine).startswith('http'):
                        st.image(url_immagine, caption=f"Foto {d['ARTICOLO']}", use_container_width=True)
                    else:
                        st.warning("⚠️ Immagine non disponibile o link non valido")
                        st.write(f"Contenuto cella: {url_immagine}") # Questo ci aiuta a capire cosa c'è scritto 
                    
            else:
                st.warning("Nessun articolo trovato.")
        else:
            st.info("👈 Usa la barra a sinistra per cercare un articolo nel listino.")

    except Exception as e:
        st.error(f"Errore durante l'apertura dell'Excel: {e}")
