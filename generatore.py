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

# 1. Caricamento dati
file_path = 'Listino_agente.xlsx'

@st.cache_data
def carica_dati(path):
    if not os.path.exists(path):
        return None
    try:
        data = pd.read_excel(path)
        data.columns = [str(c).strip().upper() for c in data.columns]
        return data
    except:
        return None

df = carica_dati(file_path)

if df is None:
    st.error(f"⚠️ Errore: Il file '{file_path}' non è stato trovato o è illeggibile.")
    st.stop()

# =========================================================
# --- SIDEBAR: DATI CLIENTE E SCONTI ---
# =========================================================
st.sidebar.header("📋 Dati Documento")
nome_cliente = st.sidebar.text_input("Nome del Cliente:", placeholder="Spett.le...")

st.sidebar.divider()

st.sidebar.header("💰 Impostazioni Sconto")
col_sc1, col_sc2, col_sc3 = st.sidebar.columns(3)
sc1 = col_sc1.number_input("Sc. 1 %", 0.0, 100.0, 40.0)
sc2 = col_sc2.number_input("Sc. 2 %", 0.0, 100.0, 0.0)
sc3 = col_sc3.number_input("Sc. 3 %", 0.0, 100.0, 0.0)

# =========================================================
# --- PAGINA PRINCIPALE: RICERCA E INSERIMENTO ---
# =========================================================
st.title("📄 Realizzatore di Offerte Professionali")

st.header("🔍 Ricerca Articolo")
ricerca = st.text_input("Inserisci nome modello:", placeholder="Digita qui il modello...").upper()

if ricerca:
    risultato = df[df['ARTICOLO'].astype(str).str.upper().str.contains(ricerca, na=False)]
    
    if not risultato.empty:
        scelta = st.selectbox("Seleziona l'articolo:", risultato['ARTICOLO'].unique())
        d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
        
        st.divider()
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader(f"Modello: {d['ARTICOLO']}")
            prezzo_listino = float(d['LISTINO'])
            
            prezzo_netto = prezzo_listino * (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100)
            st.markdown(f"### Prezzo Netto: :green[{prezzo_netto:.2f} €]")
            
            st.divider()
            
            # --- MODALITÀ DI INSERIMENTO ---
            modalita = st.radio(
                "Scegli la modalità di inserimento:", 
                ["Specifica Taglie", "Solo Modello/Vetrina (Senza taglie)"], 
                horizontal=True
            )
            
            st.write("") # Spazio vuoto
            
            if modalita == "Specifica Taglie":
                st.write("**Quantità per Taglia:**")
                
                if st.button("🔄 Azzera Campi"):
                    for t in range(35, 51):
                        st.session_state[f"qta_{t}"] = 0
                    st.rerun()

                taglie = list(range(35, 51))
                quantita_taglie = {}
                
                cols1 = st.columns(8)
                for i in range(8):
                    t = taglie[i]
                    with cols1[i]:
                        key = f"qta_{t}"
                        if key not in st.session_state: st.session_state[key] = 0
                        quantita_taglie[t] = st.number_input(str(t), min_value=0, step=1, key=key)
                
                cols2 = st.columns(8)
                for i in range(8, 16):
                    t = taglie[i]
                    with cols2[i-8]:
                        key = f"qta_{t}"
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
                                "Immagine": str(d['IMMAGINE']).strip()
                            })
                            aggiunti += 1
                    if aggiunti > 0: 
                        st.success("Aggiunto con successo!")
                        st.rerun()
                    else: 
                        st.warning("Inserisci almeno una quantità!")
            
            else:
                # MODALITÀ VETRINA (SENZA TAGLIE)
                st.info("💡 In questa modalità puoi inserire l'articolo senza specificare le taglie. Se lasci '0', l'articolo apparirà nel PDF solo con il prezzo unitario come vetrina.")
                qta_generica = st.number_input("Quantità generica totale:", min_value=0, step=1, value=0)
                
                if st.button("🛒 Aggiungi Modello", use_container_width=True, type="primary"):
                    st.session_state['carrello'].append({
                        "Articolo": d['ARTICOLO'], 
                        "Taglia": "-", # Trattino per indicare l'assenza di taglia
                        "Quantità": qta_generica,
                        "Netto U.": f"{prezzo_netto:.2f} €", 
                        "Totale Riga": prezzo_netto * qta_generica,
                        "Immagine": str(d['IMMAGINE']).strip()
                    })
                    st.success("Modello aggiunto al preventivo!")
                    st.rerun()
                
        with c2:
            url = str(d['IMMAGINE']).strip()
            if url.startswith('http'):
                try:
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                    st.image(BytesIO(r.content), caption=d['ARTICOLO'], use_container_width=True)
                except: 
                    st.write("Immagine non disponibile")

# =========================================================
# --- RIEPILOGO E PDF ---
# =========================================================
if st.session_state['carrello']:
    st.divider()
    st.header("🛒 Riepilogo")
    df_c = pd.DataFrame(st.session_state['carrello'])
    
    # Mostriamo la tabella a video in modo pulito (se taglia è -, la formattiamo)
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
                
                # Gestiamo come scrivere le quantità in base alla modalità
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
                            self.image(f, 10, 8, 30)
                            break
                    self.set_font("helvetica", "B", 11)
                    self.set_xy(100, 15)
                    testo = f"Spett.le {nome_cliente}" if nome_cliente else "Spett.le Cliente"
                    self.cell(100, 10, testo, align="R")
                    self.ln(20)

            pdf = PDF()
            pdf.add_page()
            
            for art, dati in raggruppo.items():
                y_inizio = pdf.get_y()
                if y_inizio > 230:
                    pdf.add_page()
                    y_inizio = pdf.get_y()

                # Immagine a destra
                if dati["Img"].startswith("http"):
                    try:
                        res = requests.get(dati["Img"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(res.content)
                            pdf.image(tmp.name, x=155, y=y_inizio, w=35)
                        os.remove(tmp.name)
                    except: pass

                # Testo a sinistra
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(135, 7, f"Modello: {art}")
                pdf.ln(7)
                pdf.set_font("helvetica", "", 10)
                pdf.cell(135, 6, f"Prezzo Netto: {dati['Netto'].replace('€', 'Euro')}")
                pdf.ln(6)
                
                # Stampo le quantità/taglie solo se ce ne sono
                if dati["T"]:
                    pdf.set_font("helvetica", "I", 9)
                    pdf.multi_cell(135, 5, " | ".join(dati["T"]))
                else:
                    pdf.set_font("helvetica", "I", 9)
                    pdf.cell(135, 5, "Proposta Modello (Nessuna quantità specificata)")
                    pdf.ln(5)
                
                # Stampo il Subtotale solo se c'è un valore
                if dati['Tot'] > 0:
                    pdf.set_font("helvetica", "B", 10)
                    pdf.cell(135, 7, f"Subtotale: {dati['Tot']:.2f} Euro")
                    pdf.ln(7)
                else:
                    pdf.ln(7) # Lascia un po' di spazio se non c'è il subtotale
                
                # Calcolo posizione per evitare sovrapposizioni
                y_fine = max(pdf.get_y(), y_inizio + 40)
                pdf.set_y(y_fine + 2)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

            pdf.ln(5)
            
            # Mostro il totale generale solo se è maggiore di zero
            if totale_generale > 0:
                pdf.set_font("helvetica", "B", 14)
                pdf.cell(0, 10, f"TOTALE GENERALE: {totale_generale:.2f} Euro", align="R")
            
            # ==========================================
            # FIX DEFINITIVO PER FPDF E STREAMLIT
            # ==========================================
            pdf_out = pdf.output()
            
            if isinstance(pdf_out, str):
                pdf_bytes = pdf_out.encode('latin-1')
            elif isinstance(pdf_out, bytearray):
                pdf_bytes = bytes(pdf_out)
            else:
                pdf_bytes = bytes(pdf_out)

            # Anteprima in Base64
            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            st.divider()
            st.info("💡 Se non visualizzi l'anteprima qui sotto, clicca sul tasto 'Scarica PDF'.")
            
            pdf_display = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # Pulsante Download
            st.download_button(
                label="⬇️ Scarica PDF",
                data=pdf_bytes,
                file_name="Preventivo_Vetrina.pdf",
                mime="application/pdf",
                use_container_width=True
            )
