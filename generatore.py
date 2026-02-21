import streamlit as st
import pandas as pd

# Configurazione della pagina
st.set_page_config(page_title="Generatore Preventivi", layout="wide")

st.title("uD83DuDCC4 Realizzatore di Offerte")
st.write("Carica il tuo listino e crea un preventivo in un click.")

# 1. Caricamento File
file_path = 'listino_agente.xlsx'

try:
    df = pd.read_excel(file_path)
    # Puliamo i nomi delle colonne
    df.columns = df.columns.str.strip()
    
    # 2. Ricerca Articolo (Interfaccia Grafica)
    st.sidebar.header("Filtri di Ricerca")
    ricerca = st.sidebar.text_input("Cerca l'ARTICOLO:", "").upper()

    if ricerca:
        # Filtriamo i dati
        risultato = df[df['ARTICOLO'].astype(str).str.contains(ricerca, na=False)]
        
        if not resultado.empty:
            st.success(f"Trovati {len(risultato)} articoli")
            
            # Mostriamo la tabella dei risultati (senza colonna A)
            colonne_da_mostrare = ['ARTICOLO', 'RANGE TAGLIE', 'LISTINO', 'IMMAGINE']
            st.dataframe(risultato[colonne_da_mostrare])
            
            # 3. Selezione e Dettaglio
            scelta = st.selectbox("Seleziona l'articolo esatto per il preventivo:", risultato['ARTICOLO'])
            dettaglio = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
            
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Dettagli Offerta")
                st.write(f"**Modello:** {dettaglio['ARTICOLO']}")
                st.write(f"**Taglie:** {dettaglio['RANGE TAGLIE']}")
                st.write(f"**Prezzo di Listino:** {dettaglio['LISTINO']}€")
            
            with col2:
                st.subheader("Immagine")
                # Qui gestiremo la foto appena mi dici cosa c'è nella colonna
                st.info(f"Riferimento: {dettaglio['IMMAGINE']}")
                
        else:
            st.warning("Nessun articolo trovato con questo nome.")
    else:
        st.info("Inserisci il nome di un articolo nella barra a sinistra per iniziare.")

except Exception as e:
    st.error(f"Errore: Assicurati che il file '{file_path}' sia caricato correttamente su GitHub.")
    st.info("Se non l'hai fatto, scrivi 'pip install streamlit pandas openpyxl' nel terminale.")
