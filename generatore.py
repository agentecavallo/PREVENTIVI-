import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os

st.set_page_config(page_title="Generatore Preventivi", layout="wide")

# --- INIZIALIZZAZIONE DELLA MEMORIA (CARRELLO) ---
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
    risultato = df[df['ARTICOLO'].astype(str).str.upper().str.contains(ricerca, na=False)]
    
    if not risultato.empty:
        scelta = st.selectbox("Seleziona l'articolo trovato:", risultato['ARTICOLO'].unique())
        d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
        
        st.divider()
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Dettagli Prodotto")
            st.write(f"**Modello:** {d['ARTICOLO']}")
            
            prezzo_listino = float(d['LISTINO'])
            st.markdown(f"#### Prezzo di Listino: {prezzo_listino:.2f} €")
            
            # --- GESTIONE SCONTI ---
            st.write("**Applica Sconti (%)**")
            col_sconto1, col_sconto2, col_sconto3 = st.columns(3)
            # Sconto 1 ha value=40.0 come default
            sc1 = col_sconto1.number_input("Sconto 1 (%)", min_value=0.0, max_value=100.0, step=1.0, value=40.0)
            sc2 = col_sconto2.number_input("Sconto 2 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            sc3 = col_sconto3.number_input("Sconto 3 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            
            prezzo_netto = prezzo_listino * (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100)
            st.markdown(f"### Prezzo Netto: {prezzo_netto:.2f} €")
            
            st.divider()
            
            # --- NUOVO: PULSANTE PER AZZERARE LE QUANTITÀ ---
            if st.button("🔄 Azzera Quantità"):
                # Se cliccato, forziamo tutte le taglie a 0 nella memoria dell'app
                for taglia in range(35, 51):
                    st.session_state[f"qta_{taglia}"] = 0
            
            # --- GRIGLIA SVILUPPO TAGLIE ---
            st.write("**Sviluppo Taglie (Inserisci le quantità):**")
            taglie_disponibili = list(range(35, 51))
            
            cols_taglie = st.columns(4)
            quantita_taglie = {}
            
            for i, taglia in enumerate(taglie_disponibili):
                col_idx = i % 4
                with cols_taglie[col_idx]:
                    # Se la taglia non è ancora nella memoria, la inizializziamo a 0
                    if f"qta_{taglia}" not in st.session_state:
                        st.session_state[f"qta_{taglia}"] = 0
                        
                    # La casella prende il valore dalla memoria dell'app tramite la 'key'
                    quantita_taglie[taglia] = st.number_input(
                        f"Tg {taglia}", 
                        min_value=0, 
                        step=1, 
                        key=f"qta_{taglia}"
                    )
            
            st.write("")
            
            # --- PULSANTE AGGIUNGI ---
            if st.button("🛒 Aggiungi al Preventivo"):
                aggiunti = 0
                for taglia, qta in quantita_taglie.items():
                    if qta > 0:
                        articolo_da_aggiungere = {
                            "Articolo": d['ARTICOLO'],
                            "Taglia": taglia,
                            "Quantità": qta,
                            "Listino U.": f"{prezzo_listino:.2f} €",
                            "Sconti Applicati": f"{sc1}% + {sc2}% + {sc3}%",
                            "Netto U.": f"{prezzo_netto:.2f} €",
                            "Totale Riga": prezzo_netto * qta
                        }
                        st.session_state['carrello'].append(articolo_da_aggiungere)
                        aggiunti += 1
                
                if aggiunti > 0:
                    st.success(f"✅ Aggiunte correttamente {aggiunti} righe di {d['ARTICOLO']} al preventivo!")
                else:
                    st.warning("⚠️ Non hai inserito nessuna quantità! Metti un numero maggiore di zero in almeno una taglia.")
                
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

if len(st.session_state['carrello']) > 0:
    st.divider()
    st.header("🛒 Riepilogo Preventivo")
    
    df_carrello = pd.DataFrame(st.session_state['carrello'])
    st.dataframe(df_carrello, use_container_width=True)
    
    totale_pezzi = df_carrello["Quantità"].sum()
    totale_finale = df_carrello["Totale Riga"].sum()
    
    st.markdown(f"**Totale Pezzi:** {totale_pezzi}")
    st.markdown(f"## Totale Finale: {totale_finale:.2f} €")
    
    if st.button("🗑️ Svuota Preventivo"):
        st.session_state['carrello'] = []
        st.rerun()
