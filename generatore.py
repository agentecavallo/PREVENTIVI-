import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os

st.set_page_config(page_title="Generatore Preventivi", layout="wide")

# --- INIZIALIZZAZIONE DELLA MEMORIA (CARRELLO) ---
# Se il carrello non esiste ancora nella "memoria" dell'app, lo creiamo vuoto
if 'carrello' not in st.session_state:
    st.session_state['carrello'] = []

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

# 3. Verifica colonne presenti
colonne_necessarie = ['ARTICOLO', 'LISTINO', 'IMMAGINE']
colonne_presenti = df.columns.tolist()

missing = [c for c in colonne_necessarie if c not in colonne_presenti]
if missing:
    st.warning(f"Attenzione! Nel tuo Excel mancano queste colonne: {missing}")
    st.write("Le colonne che ho trovato nel tuo file sono:", colonne_presenti)
    st.stop()

# 4. Interfaccia di ricerca
ricerca = st.sidebar.text_input("Cerca ARTICOLO:").upper()

if ricerca:
    # Filtro: cerchiamo in ARTICOLO
    risultato = df[df['ARTICOLO'].astype(str).str.upper().str.contains(ricerca, na=False)]
    
    # QUI HO CORRETTO L'ERRORE "resultado"
    if not risultato.empty:
        scelta = st.selectbox("Seleziona l'articolo trovato:", risultato['ARTICOLO'].unique())
        d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
        
        st.divider()
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Dettagli Prodotto")
            st.write(f"**Modello:** {d['ARTICOLO']}")
            
            # Assicuriamoci che il listino sia un numero
            prezzo_listino = float(d['LISTINO'])
            st.markdown(f"#### Prezzo di Listino: {prezzo_listino:.2f} €")
            
            # --- NUOVO: SELEZIONE TAGLIA ---
            # Crea un menu a tendina con i numeri da 35 a 50
            taglie_disponibili = list(range(35, 51))
            taglia_scelta = st.selectbox("Seleziona la Taglia:", taglie_disponibili)
            
            # --- NUOVO: GESTIONE SCONTI (Fino a 3) ---
            st.write("**Applica Sconti (%)**")
            col_sconto1, col_sconto2, col_sconto3 = st.columns(3)
            # Caselle numeriche per gli sconti. Di base partono da 0.0
            sc1 = col_sconto1.number_input("Sconto 1 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            sc2 = col_sconto2.number_input("Sconto 2 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            sc3 = col_sconto3.number_input("Sconto 3 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            
            # Calcolo del prezzo netto (Sconto a cascata)
            prezzo_netto = prezzo_listino * (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100)
            
            st.markdown(f"### Prezzo Netto: {prezzo_netto:.2f} €")
            
            # Quantità
            quantita = st.number_input("Quantità", min_value=1, step=1, value=1)
            
            # --- NUOVO: PULSANTE AGGIUNGI AL CARRELLO ---
            if st.button("🛒 Aggiungi al Preventivo"):
                # Creiamo una "riga" con i dati che ci interessano
                articolo_da_aggiungere = {
                    "Articolo": d['ARTICOLO'],
                    "Taglia": taglia_scelta,
                    "Quantità": quantita,
                    "Listino U.": f"{prezzo_listino:.2f} €",
                    "Sconti Applicati": f"{sc1}% + {sc2}% + {sc3}%",
                    "Netto U.": f"{prezzo_netto:.2f} €",
                    "Totale Riga": prezzo_netto * quantita # Lo teniamo come numero per sommarlo dopo
                }
                # Lo salviamo nella memoria dell'app
                st.session_state['carrello'].append(articolo_da_aggiungere)
                st.success(f"Aggiunto: {d['ARTICOLO']} (Tg {taglia_scelta}) al preventivo!")
                
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
    st.info("Inserisci il nome di un articolo a sinistra per iniziare.")


# =========================================================
# --- SEZIONE CARRELLO / PREVENTIVO (VISIBILE IN FONDO) ---
# =========================================================

# Se c'è almeno un elemento nel carrello, mostriamo questa sezione
if len(st.session_state['carrello']) > 0:
    st.divider()
    st.header("🛒 Riepilogo Preventivo")
    
    # Trasformiamo la lista in una tabella per farla vedere bene
    df_carrello = pd.DataFrame(st.session_state['carrello'])
    
    # Mostriamo la tabella a schermo
    st.dataframe(df_carrello, use_container_width=True)
    
    # Calcoliamo il totale finale sommando tutte le righe
    totale_finale = df_carrello["Totale Riga"].sum()
    st.markdown(f"## Totale Finale Preventivo: {totale_finale:.2f} €")
    
    # Tasto per cancellare tutto e ricominciare
    if st.button("🗑️ Svuota Preventivo"):
        st.session_state['carrello'] = []
        st.rerun() # Ricarica l'app per azzerare lo schermo
