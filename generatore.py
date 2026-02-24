import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import tempfile
import base64
from fpdf import FPDF

# Configurazione della pagina
st.set_page_config(page_title="Generatore Preventivi", layout="wide", page_icon="📄")

# --- INIZIALIZZAZIONE DELLA MEMORIA ---
if 'carrello' not in st.session_state:
    st.session_state['carrello'] = []

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_dati(path, tipo="base"):
    if not os.path.exists(path):
        return None
    try:
        data = pd.read_excel(path)
        if tipo == "atg":
            # Mappiamo le prime 5 colonne come richiesto: A: articolo, B: rivestimento, C: q.tà box, D: range taglie, E: listino
            data = data.iloc[:, :5]
            data.columns = ['ARTICOLO', 'RIVESTIMENTO', 'QTA_BOX', 'RANGE_TAGLIE', 'LISTINO']
            # Aggiungiamo una colonna IMMAGINE vuota per non far "rompere" il codice del PDF
            data['IMMAGINE'] = ""
        else:
            data.columns = [str(c).strip().upper() for c in data.columns]
        return data
    except:
        return None

# Cerchiamo comunque il file nominato Listino_agente.xlsx per comodità tua, ma lo trattiamo come "base"
df_base = carica_dati('Listino_agente.xlsx', "base")
df_atg = carica_dati('Listino_ATG.xlsx', "atg")

# =========================================================
# --- SIDEBAR: DATI CLIENTE, SCONTI E NOTE ---
# =========================================================
st.sidebar.header("📋 Dati Documento")
nome_cliente = st.sidebar.text_input("Nome del Cliente:", placeholder="Spett.le...")

st.sidebar.divider()

# Sconti Base
st.sidebar.header("💰 Sconto Base")
col_sc1, col_sc2, col_sc3 = st.sidebar.columns(3)
sc1 = col_sc1.number_input("Sc. 1 %", 0.0, 100.0, 40.0, key="sc_base1")
sc2 = col_sc2.number_input("Sc. 2 %", 0.0, 100.0, 10.0, key="sc_base2") # Impostato a 10 di default
sc3 = col_sc3.number_input("Sc. 3 %", 0.0, 100.0, 0.0, key="sc_base3")

st.sidebar.divider()

# Sconti ATG
st.sidebar.header("🧤 Sconto ATG")
col_atg1, col_atg2, col_atg3 = st.sidebar.columns(3)
sc_atg1 = col_atg1.number_input("Sc. ATG 1 %", 0.0, 100.0, 40.0, key="sc_atg1")
sc_atg2 = col_atg2.number_input("Sc. ATG 2 %", 0.0, 100.0, 10.0, key="sc_atg2") # Impostato a 10 di default
sc_atg3 = col_atg3.number_input("Sc. ATG 3 %", 0.0, 100.0, 0.0, key="sc_atg3")

st.sidebar.divider()

# Il grande campo note spostato sotto gli sconti
note_preventivo = st.sidebar.text_area("📝 Note Aggiuntive (verranno inserite a fine PDF):", height=400, placeholder="Scrivi qui le tue note (es. tempi di consegna, validità offerta, ecc.)...")


# =========================================================
# --- PAGINA PRINCIPALE: RICERCA E INSERIMENTO ---
# =========================================================
st.title("📄 Realizzatore di Offerte Professionali")

# SELEZIONE CATALOGO
catalogo = st.radio("📂 Scegli in quale Listino cercare:", ["Listino Base", "Listino ATG"], horizontal=True)

# Imposta il dataframe e gli sconti in base alla scelta
if catalogo == "Listino Base":
    df_corrente = df_base
    sconto_applicato = (sc1, sc2, sc3)
else:
    df_corrente = df_atg
    sconto_applicato = (sc_atg1, sc_atg2, sc_atg3)

# Verifica che il file esista prima di procedere
if df_corrente is None:
    st.warning(f"⚠️ Il file Excel per il '{catalogo}' non è stato trovato nella cartella. Assicurati che i nomi dei file siano 'Listino_agente.xlsx' e 'Listino_ATG.xlsx'.")
else:
    st.header("🔍 Ricerca Articolo")
    ricerca = st.text_input("Inserisci nome modello:", placeholder="Digita qui il modello...").upper()

    if ricerca:
        risultato = df_corrente[df_corrente['ARTICOLO'].astype(str).str.upper().str.contains(ricerca, na=False)]
        
        if not risultato.empty:
            scelta = st.selectbox("Seleziona l'articolo:", risultato['ARTICOLO'].unique())
            d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
            
            st.divider()
            c1, c2 = st.columns([2, 1])
            
            with c1:
                st.subheader(f"Modello: {d['ARTICOLO']}")
                
                # Se è ATG, mostra i dati aggiuntivi
                if catalogo == "Listino ATG":
                    st.caption(f"**Rivestimento:** {d.get('RIVESTIMENTO', '-')} | **Q.tà Box:** {d.get('QTA_BOX', '-')} | **Range Taglie:** {d.get('RANGE_TAGLIE', '-')}")
                
                prezzo_listino = float(d['LISTINO'])
                
                # Calcolo Prezzo Netto dinamico
                s1, s2, s3 = sconto_applicato
                prezzo_netto = prezzo_listino * (1 - s1/100) * (1 - s2/100) * (1 - s3/100)
                st.markdown(f"### Prezzo Netto: :green[{prezzo_netto:.2f} €]")
                
                st.divider()
                
                # --- MODALITÀ DI INSERIMENTO ---
                modalita = st.radio(
                    "Scegli la modalità di inserimento:", 
                    ["Specifica Taglie", "Solo Modello/Vetrina (Senza taglie)"], 
                    horizontal=True,
                    key="mod_inserimento"
                )
                
                st.write("")
                
                if modalita == "Specifica Taglie":
                    st.write("**Quantità per Taglia:**")
                    
                    # Definiamo le taglie in base al catalogo
                    if catalogo == "Listino Base":
                        taglie_disponibili = list(range(35, 51))
                    else:
                        taglie_disponibili = [6, 7, 8, 9, 10, 11, 12] # Taglie standard guanti ATG
                    
                    if st.button("🔄 Azzera Campi"):
                        for t in taglie_disponibili:
                            st.session_state[f"qta_{t}_{catalogo}"] = 0
                        st.rerun()

                    quantita_taglie = {}
                    
                    # Generatore di griglia flessibile (max 8 per riga)
                    for i in range(0, len(taglie_disponibili), 8):
                        chunk = taglie_disponibili[i:i+8]
                        cols = st.columns(8)
                        for j, t in enumerate(chunk):
                            with cols[j]:
                                key = f"qta_{t}_{catalogo}"
                                if key not in st.session_state: st.session_state[key] = 0
                                quantita_taglie[t] = st.number_input(str(t), min_value=0, step=1, key=key)

                    st.write("")
                    if st.button("🛒 Aggiungi al Preventivo", use_container_width=True, type="primary"):
                        aggiunti = 0
                        for t, q in quantita_taglie.items():
                            if q > 0:
                                st.session_state['carrello'].append({
                                    "Articolo": d['ARTICOLO'], "Taglia": t, "Quantità": q,
                                    "Netto U.": f"{prezzo_netto:.2f} €", "Totale Riga": prezzo_netto * q,
                                    "Immagine": str(d.get('IMMAGINE', '')).strip()
                                })
                                aggiunti += 1
                        if aggiunti > 0: 
                            st.success("Aggiunto con successo!")
                            st.rerun()
                        else: 
                            st.warning("Inserisci almeno una quantità!")
                
                else:
                    st.info("💡 In questa modalità puoi inserire l'articolo senza specificare le taglie.")
                    qta_generica = st.number_input("Quantità generica totale:", min_value=0, step=1, value=0, key="qta_gen")
                    
                    if st.button("🛒 Aggiungi Modello", use_container_width=True, type="primary"):
                        st.session_state['carrello'].append({
                            "Articolo": d['ARTICOLO'], 
                            "Taglia": "-", 
                            "Quantità": qta_generica,
                            "Netto U.": f"{prezzo_netto:.2f} €", 
                            "Totale Riga": prezzo_netto * qta_generica,
                            "Immagine": str(d.get('IMMAGINE', '')).strip()
                        })
                        st.success("Modello aggiunto al preventivo!")
                        st.rerun()
                    
            with c2:
                # Gestione immagine (solo per Base o se è presente per caso in ATG)
                url = str(d.get('IMMAGINE', '')).strip()
                if url.startswith('http'):
                    try:
                        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                        st.image(BytesIO(r.content), caption=d['ARTICOLO'], use_container_width=True)
                    except: 
                        st.write("Immagine non disponibile")
                elif catalogo == "Listino ATG":
                    # Spazio decorativo per ATG se non ci sono immagini
                    st.markdown("### 🧤 **Prodotto ATG**")
                    st.write("*(Nessuna immagine nel listino)*")

# =========================================================
# --- RIEPILOGO E PDF ---
# =========================================================
if st.session_state['carrello']:
    st.divider()
    st.header("🛒 Riepilogo")
    df_c = pd.DataFrame(st.session_state['carrello'])
    
    st.table(df_c[["Articolo", "Taglia", "Quantità", "Netto U.", "Totale Riga"]])
    
    totale_generale = df_c["Totale Riga"].sum()
    st.markdown(f"### Totale Generale: **{totale_generale:.2f} €**")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        if st.button("🗑️ Svuota Tutto", use_container_width=True):
            st.session_state['carrello'] = []
            st.rerun()
            
    with c_p2:
        if st.button("📄 Genera ed Esporta PDF", use_container_width=True, type="primary"):
            raggruppo = {}
            for r in st.session_state['carrello']:
                art = r["Articolo"]
                if art not in raggruppo:
                    raggruppo[art] = {"T": [], "Tot": 0, "Img": r["Immagine"], "Netto": r["Netto U."]}
                
                if r["Quantità"] > 0:
                    if r["Taglia"] == "-":
                        raggruppo[art]["T"].append(f"Q.tà: {r['Quantità']}pz")
                    else:
                        raggruppo[art]["T"].append(f"Tg{r['Taglia']}: {r['Quantità']}pz")
                
                raggruppo[art]["Tot"] += r["Totale Riga"]

            class PDF(FPDF):
                def header(self):
                    for f in ["logo.png", "logo.jpg", "logo.jpeg"]:
                        if os.path.exists(f):
                            # DIMENSIONI RADDOPPIATE: da 30 a 60
                            self.image(f, 10, 8, 60)
                            break
                    self.set_font("helvetica", "B", 11)
                    self.set_xy(100, 15)
                    testo = f"Spett.le {nome_cliente}" if nome_cliente else "Spett.le Cliente"
                    self.cell(100, 10, testo, align="R")
                    # Aumentato lo spazio verticale per compensare il logo più grande
                    self.ln(30)

            pdf = PDF()
            pdf.add_page()
            
            for art, dati in raggruppo.items():
                y_inizio = pdf.get_y()
                if y_inizio > 230:
                    pdf.add_page()
                    y_inizio = pdf.get_y()

                # Immagine a destra (se presente)
                if dati["Img"].startswith("http"):
                    try:
                        res = requests.get(dati["Img"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                        with tempfile.Named
