import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import tempfile
import base64
from fpdf import FPDF

# Configurazione pagina
st.set_page_config(page_title="Generatore Preventivi", layout="wide", page_icon="📄")

# --- INIZIALIZZAZIONE DELLA MEMORIA ---
if 'carrello' not in st.session_state:
    st.session_state['carrello'] = []

# 1. Caricamento dati
file_path = 'Listino_agente.xlsx'
if not os.path.exists(file_path):
    st.error(f"⚠️ Il file '{file_path}' non esiste nella cartella principale!")
    st.stop()

@st.cache_data
def carica_dati(path):
    try:
        data = pd.read_excel(path)
        data.columns = [str(c).strip().upper() for c in data.columns]
        return data
    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file Excel: {e}")
        return None

df = carica_dati(file_path)
if df is None:
    st.stop()

st.title("📄 Realizzatore di Offerte Professionali")

# --- SIDEBAR: DATI CLIENTE E RICERCA ---
st.sidebar.header("📋 Dati Documento")
nome_cliente = st.sidebar.text_input("Nome del Cliente:", placeholder="Spett.le ditta...")

st.sidebar.divider()
st.sidebar.header("🔍 Ricerca Prodotto")
ricerca = st.sidebar.text_input("Cerca ARTICOLO (es. modello):").upper()

if ricerca:
    risultato = df[df['ARTICOLO'].astype(str).str.upper().str.contains(ricerca, na=False)]
    
    if not risultato.empty:
        scelta = st.selectbox("Seleziona l'articolo esatto:", risultato['ARTICOLO'].unique())
        d = risultato[risultato['ARTICOLO'] == scelta].iloc[0]
        
        st.divider()
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader(f"Modello: {d['ARTICOLO']}")
            prezzo_listino = float(d['LISTINO'])
            
            # --- SEZIONE SCONTI ---
            st.write("**Configurazione Sconti**")
            col_sc1, col_sc2, col_sc3 = st.columns(3)
            sc1 = col_sc1.number_input("Sconto 1 %", 0.0, 100.0, 40.0)
            sc2 = col_sc2.number_input("Sconto 2 %", 0.0, 100.0, 0.0)
            sc3 = col_sc3.number_input("Sconto 3 %", 0.0, 100.0, 0.0)
            
            prezzo_netto = prezzo_listino * (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100)
            st.markdown(f"### Prezzo Netto: :green[{prezzo_netto:.2f} €]")
            
            st.divider()
            
            # --- INSERIMENTO QUANTITÀ ---
            st.write("**Inserisci Quantità per Taglia:**")
            
            # Pulsante reset rapido
            if st.button("🔄 Azzera Campi"):
                for t in range(35, 51):
                    st.session_state[f"qta_{t}"] = 0
                st.rerun()

            taglie = list(range(35, 51))
            quantita_taglie = {}
            
            # Griglia 1 (35-42)
            cols1 = st.columns(8)
            for i in range(8):
                t = taglie[i]
                with cols1[i]:
                    key = f"qta_{t}"
                    if key not in st.session_state: st.session_state[key] = 0
                    quantita_taglie[t] = st.number_input(str(t), min_value=0, step=1, key=key)
            
            # Griglia 2 (43-50)
            cols2 = st.columns(8)
            for i in range(8, 16):
                t = taglie[i]
                with cols2[i-8]:
                    key = f"qta_{t}"
                    if key not in st.session_state: st.session_state[key] = 0
                    quantita_taglie[t] = st.number_input(str(t), min_value=0, step=1, key=key)

            st.write("")
            if st.button("🛒 Aggiungi al Preventivo", use_container_width=True, type="primary"):
                prodotti_aggiunti = []
                for t, q in quantita_taglie.items():
                    if q > 0:
                        prodotti_aggiunti.append({
                            "Articolo": d['ARTICOLO'], 
                            "Taglia": t, 
                            "Quantità": q,
                            "Netto U.": f"{prezzo_netto:.2f} €", 
                            "Totale Riga": prezzo_netto * q,
                            "Immagine": str(d['IMMAGINE']).strip(),
                            "Netto_Val": prezzo_netto
                        })
                
                if prodotti_aggiunti:
                    st.session_state['carrello'].extend(prodotti_aggiunti)
                    st.success(f"✅ Aggiunto {d['ARTICOLO']} al carrello!")
                else:
                    st.warning("⚠️ Inserisci almeno una quantità prima di aggiungere!")
                
        with c2:
            st.write("**Anteprima Prodotto**")
            url = str(d['IMMAGINE']).strip()
            if url.startswith('http'):
                try:
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                    st.image(BytesIO(r.content), use_container_width=True)
                except:
                    st.info("Immagine non disponibile nel catalogo online")

# =========================================================
# --- RIEPILOGO E GENERAZIONE PDF ---
# =========================================================
if st.session_state['carrello']:
    st.divider()
    st.header("🛒 Articoli in Preventivo")
    
    df_carrello = pd.DataFrame(st.session_state['carrello'])
    # Mostriamo una tabella pulita
    st.table(df_carrello[["Articolo", "Taglia", "Quantità", "Netto U.", "Totale Riga"]])
    
    totale_generale = df_carrello["Totale Riga"].sum()
    st.subheader(f"Totale Complessivo Documento: {totale_generale:.2f} €")
    
    cp1, cp2 = st.columns(2)
    with cp1:
        if st.button("🗑️ Svuota Carrello", use_container_width=True):
            st.session_state['carrello'] = []
            st.rerun()
            
    with cp2:
        if st.button("📄 Genera ed Esporta PDF", use_container_width=True, type="primary"):
            # Raggruppamento per modello per il PDF
            raggruppo = {}
            for r in st.session_state['carrello']:
                art = r["Articolo"]
                if art not in raggruppo:
                    raggruppo[art] = {"T": [], "Tot": 0, "Img": r["Immagine"], "Netto": r["Netto U."]}
                raggruppo[art]["T"].append(f"Tg.{r['Taglia']} ({r['Quantità']}pz)")
                raggruppo[art]["Tot"] += r["Totale Riga"]

            class PDF(FPDF):
                def header(self):
                    # Logo aziendale
                    for f in ["logo.png", "logo.jpg", "logo.jpeg"]:
                        if os.path.exists(f):
                            self.image(f, 10, 8, 30)
                            break
                    self.set_font("Arial", "B", 12)
                    self.set_xy(110, 15)
                    testo_cli = f"Spett.le {nome_cliente}" if nome_cliente else "Spett.le Cliente"
                    self.cell(90, 10, testo_cli, align="R", ln=True)
                    self.ln(20)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

            pdf = PDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            for art, dati in raggruppo.items():
                y_inizio = pdf.get_y()
                
                # Salto pagina preventivo se siamo a fine foglio
                if y_inizio > 230:
                    pdf.add_page()
                    y_inizio = pdf.get_y()

                # --- DISEGNO IMMAGINE (A DESTRA) ---
                if dati["Img"].startswith("http"):
                    try:
                        res = requests.get(dati["Img"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(res.content)
                            # Immagine alta, allineata all'inizio del blocco testo
                            pdf.image(tmp.name, x=155, y=y_inizio, w=35)
                        os.remove(tmp.name)
                    except:
                        pass

                # --- TESTO DESCRITTIVO (A SINISTRA) ---
                prezzo_str = str(dati['Netto']).replace('€', 'Euro')
                pdf.set_font("Arial", "B", 12)
                pdf.cell(135, 7, f"Modello: {art}", ln=True)
                
                pdf.set_font("Arial", "", 10)
                pdf.cell(135, 6, f"Prezzo Unitario Netto: {prezzo_str}", ln=True)
                
                pdf.set_font("Arial", "I", 9)
                dettaglio_taglie = " / ".join(dati["T"])
                pdf.multi_cell(135, 5, f"Dettaglio taglie: {dettaglio_taglie}")
                
                pdf.set_font("Arial", "B", 10)
                pdf.cell(135, 8, f"Subtotale Articolo: {dati['Tot']:.2f} Euro", ln=True)
                
                # Calcolo spazio per non sovrascrivere
                y_fine_testo = pdf.get_y()
                y_fine_img = y_inizio + 40
                pdf.set_y(max(y_fine_testo, y_fine_img) + 2)
                
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

            # --- TOTALE FINALE ---
            pdf.ln(5)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, f"TOTALE GENERALE PREVENTIVO: {totale_generale:.2f} Euro", align="R", ln=True)
            
            # Generazione output
            pdf_output = pdf.output(dest='S').encode('latin-1')
            b64_pdf = base64.b64encode(pdf_output).decode('utf-8')
            
            # --- SEZIONE ANTEPRIMA ---
            st.divider()
            st.info("💡 **Consiglio:** Se non visualizzi l'anteprima qui sotto, clicca sul tasto 'Scarica PDF' per scaricarlo direttamente.")
            
            pdf_display = f'<embed src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf">'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            st.download_button(
                label="⬇️ Scarica il PDF del Preventivo",
                data=pdf_output,
                file_name="Preventivo_Calzature.pdf",
                mime="application/pdf",
                use_container_width=True
            )
