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
                    
                    # Estraiamo il valore e puliamolo con estrema cura
                    url_raw = d['IMMAGINE']
                    
                    # Trasformiamolo in stringa e togliamo spazi o caratteri invisibili
                    url_pulito = str(url_raw).strip()
                    
                    # Debug: facciamo apparire il link per sicurezza (puoi cliccarlo per test)
                    st.write(f"[Clicca qui per verificare il link]({url_pulito})")

                    if url_pulito.lower().startswith('http'):
                        try:
                            # Proviamo a caricare l'immagine
                            st.image(url_pulito, use_container_width=True)
                        except Exception as e:
                            st.error("Errore tecnico nel caricamento dell'immagine.")
                            st.info("Nota: Alcuni siti bloccano l'accesso diretto alle immagini da altre app.")
                    else:
                        st.warning("⚠️ Il link non sembra iniziare con http o https")
                        st.write(f"Contenuto rilevato: {url_pulito}")
                    else:
                        st.warning("Il contenuto non sembra un link valido.")
                        st.write(f"Testo nella cella: {url_immagine}") 
                    
            else:
                st.warning("Nessun articolo trovato.")
        else:
            st.info("👈 Usa la barra a sinistra per cercare un articolo nel listino.")

    except Exception as e:
        st.error(f"Errore durante l'apertura dell'Excel: {e}")
