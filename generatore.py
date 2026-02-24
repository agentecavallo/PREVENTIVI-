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

# --- NUOVO: MEMORIA PER L'ESPOSITORE SELEZIONATO ---
# Questo serve a ricordare quale bottone hai cliccato nella sidebar
if 'espositore_selezionato' not in st.session_state:
    st.session_state['espositore_selezionato'] = None

# --- CARICAMENTO DATI ---
@st.cache_data
def carica_dati(path, tipo="base"):
    if not os.path.exists(path):
        return None
    try:
        data = pd.read_excel(path)
        if tipo == "atg":
            data = data.iloc[:, :5]
            data.columns = ['ARTICOLO', 'RIVESTIMENTO', 'QTA_BOX', 'RANGE_TAGLIE', 'LISTINO']
            data['IMMAGINE'] = ""
        else:
            data.columns = [str(c).strip().upper() for c in data.columns]
        return data
    except:
        return None

df_base = carica_dati('Listino_agente.xlsx', "base")
df_atg = carica_dati('Listino_ATG.xlsx', "atg")

# =========================================================
# --- SIDEBAR: DATI CLIENTE, SCONTI, NOTE E ESPOSITORI ---
# =========================================================
st.sidebar.header("📋 Dati Documento")
nome_cliente = st.sidebar.text_input("Nome del Cliente:", placeholder="Spett.le...")

st.sidebar.divider()

# Sconti Base
st.sidebar.header("💰 Sconto Base")
col_sc1, col_sc2, col_sc3 = st.sidebar.columns(3)
sc1 = col_sc1.number_input("Sc. 1 %", 0.0, 100.0, 40.0, key="sc_base1")
sc2 = col_sc2.number_input("Sc. 2 %", 0.0, 100.0, 10.0, key="sc_base2")
sc3 = col_sc3.number_input("Sc. 3 %", 0.0, 100.0, 0.0, key="sc_base3")

st.sidebar.divider()

# Sconti ATG
st.sidebar.header("🧤 Sconto ATG")
col_atg1, col_atg2, col_atg3 = st.sidebar.columns(3)
sc_atg1 = col_atg1.number_input("Sc. ATG 1 %", 0.0, 100.0, 40.0, key="sc_atg1")
sc_atg2 = col_atg2.number_input("Sc. ATG 2 %", 0.0, 100.0, 10.0, key="sc_atg2")
sc_atg3 = col_atg3.number_input("Sc. ATG 3 %", 0.0, 100.0, 0.0, key="sc_atg3")

st.sidebar.divider()

# --- NUOVA SEZIONE SIDEBAR: PULSANTI ESPOSITORI ---
st.sidebar.header("🎁 Espositori Omagio")
st.sidebar.write("Clicca per selezionare l'espositore da includere nel PDF:")

# Creiamo due righe con due colonne ciascuna per i 4 pulsanti
col_esp1, col_esp2 = st.sidebar.columns(2)
col_esp3, col_esp4 = st.sidebar.columns(2)

# Funzione di aiuto per gestire il click (imposta la memoria e mostra una notifica)
def seleziona_espositore(nome_file_img):
    st.session_state['espositore_selezionato'] = nome_file_img
    # Mostra un piccolo messaggio pop-up di conferma
    st.toast(f"Selezionato: {nome_file_img.replace('.jpg','')}", icon="✅")

with col_esp1:
    # Il testo del bottone è solo testo, come richiesto
    if st.button("ATG Banco", use_container_width=True):
        seleziona_espositore("ATG banco.jpg")
with col_esp2:
    if st.button("ATG Terra", use_container_width=True):
        seleziona_espositore("ATG terra.jpg")
with col_esp3:
    if st.button("Base Banco", use_container_width=True):
        seleziona_espositore("Base banco.jpg")
with col_esp4:
    if st.button("Base Terra", use_container_width=True):
        seleziona_espositore("BASE terra.jpg")

# Mostra cosa è stato selezionato e dai la possibilità di rimuoverlo
if st.session_state['espositore_selezionato']:
    st.sidebar.success(f"✅ Incluso nel PDF: **{st.session_state['espositore_selezionato'].replace('.jpg','')}**")
    if st.sidebar.button("❌ Rimuovi Espositore"):
        st.session_state['espositore_selezionato'] = None
        st.rerun()

st.sidebar.divider()

note_preventivo = st.sidebar.text_area("📝 Note Aggiuntive (verranno inserite a fine PDF):", height=200, placeholder="Scrivi qui le tue note...")

# =========================================================
# --- PAGINA PRINCIPALE: RICERCA E INSERIMENTO ---
# =========================================================
st.title("📄 OFFERTE & ORDINI")

catalogo = st.radio("📂 Scegli in quale Listino cercare:", ["Listino Base", "Listino ATG"], horizontal=True)

if catalogo == "Listino Base":
    df_corrente = df_base
    sconto_applicato = (sc1, sc2, sc3)
else:
    df_corrente = df_atg
    sconto_applicato = (sc_atg1, sc_atg2, sc_atg3)

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
                
                if catalogo == "Listino ATG":
                    st.caption(f"**Rivestimento:** {d.get('RIVESTIMENTO', '-')} | **Q.tà Box:** {d.get('QTA_BOX', '-')} | **Range Taglie:** {d.get('RANGE_TAGLIE', '-')}")
                
                prezzo_listino = float(d['LISTINO'])
                s1, s2, s3 = sconto_applicato
                prezzo_netto = prezzo_listino * (1 - s1/100) * (1 - s2/100) * (1 - s3/100)
                st.markdown(f"### Prezzo Netto: :green[{prezzo_netto:.2f} €]")
                
                st.divider()
                
                modalita = st.radio(
                    "Scegli la modalità di inserimento:", 
                    ["Specifica Taglie", "Solo Modello/Vetrina (Senza taglie)"], 
                    horizontal=True,
                    key="mod_inserimento"
                )
                
                st.write("")
                
                if modalita == "Specifica Taglie":
                    st.write("**Quantità per Taglia:**")
                    
                    if catalogo == "Listino Base":
                        taglie_disponibili = list(range(35, 51))
                    else:
                        taglie_disponibili = [6, 7, 8, 9, 10, 11, 12] 
                    
                    if st.button("🔄 Azzera Campi"):
                        for t in taglie_disponibili:
                            st.session_state[f"qta_{t}_{catalogo}"] = 0
                        st.rerun()

                    quantita_taglie = {}
                    
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
                url = str(d.get('IMMAGINE', '')).strip()
                if url.startswith('http'):
                    try:
                        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                        st.image(BytesIO(r.content), caption=d['ARTICOLO'], use_container_width=True)
                    except: 
                        st.write("Immagine non disponibile")
                elif catalogo == "Listino ATG":
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
                            self.image(f, 10, 8, 60)
                            break
                    self.set_font("helvetica", "B", 15)
                    self.set_xy(100, 15)
                    
                    # Nome Cliente a capo
                    self.cell(100, 8, "Spett.le", align="R", ln=1)
                    self.set_x(100) 
                    testo_nome = nome_cliente if nome_cliente else "Cliente"
                    self.cell(100, 8, testo_nome, align="R", ln=1)
                    
                    self.ln(20) 

            pdf = PDF()
            pdf.add_page()
            
            # --- CICLO PRODOTTI ---
            for art, dati in raggruppo.items():
                y_inizio = pdf.get_y()
                if y_inizio > 230:
                    pdf.add_page()
                    y_inizio = pdf.get_y()

                # 1. STAMPA TESTI PRODOTTO
                pdf.set_xy(10, y_inizio)
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(135, 7, f"Modello: {art}", ln=1)
                
                pdf.set_font("helvetica", "", 10)
                pdf.cell(135, 6, f"Prezzo Netto: {dati['Netto'].replace('€', 'Euro')}", ln=1)
                
                if dati["T"]:
                    pdf.set_font("helvetica", "I", 9)
                    pdf.multi_cell(135, 5, " | ".join(dati["T"]))
                else:
                    pdf.set_font("helvetica", "I", 9)
                    pdf.cell(135, 5, "Proposta Modello (Nessuna quantità specificata)", ln=1)
                
                pdf.ln(2) 
                
                if dati['Tot'] > 0:
                    pdf.set_x(10) 
                    pdf.set_font("helvetica", "B", 10)
                    pdf.cell(135, 6, f"Subtotale: {dati['Tot']:.2f} Euro", ln=1)
                
                y_fine_testo = pdf.get_y()

                # 2. GESTIONE IMMAGINE PRODOTTO
                foto_inserita = False
                y_fine_immagine = y_inizio + 10 
                
                if dati["Img"].startswith("http"):
                    try:
                        res = requests.get(dati["Img"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                        if res.status_code == 200:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                                tmp.write(res.content)
                                pdf.image(tmp.name, x=155, y=y_inizio, w=35)
                            os.remove(tmp.name)
                            foto_inserita = True
                            y_fine_immagine = y_inizio + 35 
                    except: 
                        pass
                
                if not foto_inserita:
                    pdf.set_xy(155, y_inizio + 10)
                    pdf.set_font("helvetica", "I", 9)
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(35, 10, "Foto non disponibile", align="C")
                    pdf.set_text_color(0, 0, 0)
                    y_fine_immagine = y_inizio + 20
                
                # 3. LINEA DI SEPARAZIONE
                y_fine_blocco = max(y_fine_testo, y_fine_immagine)
                pdf.set_y(y_fine_blocco + 5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

            # --- TOTALE GENERALE ---
            pdf.ln(5)
            if totale_generale > 0:
                pdf.set_font("helvetica", "B", 14)
                pdf.cell(0, 10, f"TOTALE GENERALE: {totale_generale:.2f} Euro", align="R")
                pdf.ln(15)

            # =========================================================
            # --- NUOVA SEZIONE: INSERIMENTO ESPOSITORE NEL PDF ---
            # =========================================================
            # Recuperiamo dalla memoria quale espositore è stato scelto
            espositore_img_file = st.session_state.get('espositore_selezionato')

            # Se un espositore è stato scelto (non è None)
            if espositore_img_file:
                # Controlliamo se c'è abbastanza spazio nella pagina, altrimenti ne aggiungiamo una
                if pdf.get_y() > 180: 
                    pdf.add_page()
                
                pdf.ln(10) # Un po' di spazio prima dell'espositore
                current_y_esp = pdf.get_y() # Salviamo la posizione verticale attuale

                # 1. Inseriamo l'immagine a sinistra (x=10)
                # Controlliamo se il file esiste davvero per evitare errori
                if os.path.exists(espositore_img_file):
                    # Inserisce l'immagine con larghezza 50mm
                    pdf.image(espositore_img_file, x=10, y=current_y_esp, w=50)
                else:
                    # Se manca il file, scriviamo un avviso nel PDF
                    pdf.set_xy(10, current_y_esp)
                    pdf.set_font("helvetica", "I", 10)
                    pdf.set_text_color(200,0,0)
                    pdf.cell(50, 10, f"File '{espositore_img_file}' non trovato.", ln=1)
                    pdf.set_text_color(0,0,0)

                # 2. Inseriamo il testo a destra dell'immagine (x=65)
                pdf.set_xy(65, current_y_esp + 15) # Posizioniamo il testo un po' più in basso rispetto all'inizio dell'immagine
                pdf.set_font("helvetica", "B", 16)
                # Usiamo un colore verde scuro per evidenziare che è gratuito
                pdf.set_text_color(0, 100, 0) 
                pdf.multi_cell(0, 8, "Espositore in OMAGGIO\ncon questo ordine!")
                pdf.set_text_color(0, 0, 0) # Reimpostiamo il colore nero

                # Spostiamo il cursore sotto l'immagine dell'espositore per le note successive
                # (Immagine alta circa 50mm + 10mm di margine)
                pdf.set_y(current_y_esp + 60) 
            # =========================================================

            # --- NOTE ---
            if note_preventivo.strip():
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 8, "Note:")
                pdf.ln(8)
                pdf.set_font("helvetica", "", 10)
                testo_note = note_preventivo.replace('€', 'Euro')
                pdf.multi_cell(0, 6, testo_note)
                pdf.ln(10)
            
            # --- FIRMA ---
            pdf.ln(10)
            pdf.set_font("helvetica", "I", 11)
            pdf.cell(0, 6, "Michele Cavallo", align="R", ln=1)
            pdf.cell(0, 6, "Area Manager", align="R", ln=1)
            pdf.cell(0, 6, "Base Protection srl", align="R", ln=1)
            pdf.cell(0, 6, "tel. 389.0199088", align="R", ln=1)

            pdf_out = pdf.output()
            
            if isinstance(pdf_out, str):
                pdf_bytes = pdf_out.encode('latin-1')
            elif isinstance(pdf_out, bytearray):
                pdf_bytes = bytes(pdf_out)
            else:
                pdf_bytes = bytes(pdf_out)

            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            st.divider()
            st.info("💡 Se non visualizzi l'anteprima qui sotto, clicca sul tasto 'Scarica PDF'.")
            
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            st.download_button(
                label="⬇️ Scarica PDF",
                data=pdf_bytes,
                file_name="Preventivo_Aggiornato.pdf",
                mime="application/pdf",
                use_container_width=True
            )
