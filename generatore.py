import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import tempfile
import base64
from fpdf import FPDF

st.set_page_config(page_title="Generatore Preventivi", layout="wide")

# --- INIZIALIZZAZIONE DELLA MEMORIA ---
if 'carrello' not in st.session_state:
    st.session_state['carrello'] = []

# 1. Caricamento dati
file_path = 'Listino_agente.xlsx'
if not os.path.exists(file_path):
    st.error(f"⚠️ Il file '{file_path}' non esiste!")
    st.stop()

try:
    df = pd.read_excel(file_path)
    df.columns = [str(c).strip().upper() for c in df.columns]
except Exception as e:
    st.error(f"❌ Errore Excel: {e}")
    st.stop()

st.title("📄 Realizzatore di Offerte")

# --- SIDEBAR ---
st.sidebar.header("Dati Documento")
nome_cliente = st.sidebar.text_input("Nome del Cliente:", placeholder="Spett.le...")

st.sidebar.divider()
ricerca = st.sidebar.text_input("Cerca ARTICOLO:").upper()

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
            
            # --- SCONTI ---
            col_sc1, col_sc2, col_sc3 = st.columns(3)
            sc1 = col_sc1.number_input("Sconto 1 %", 0.0, 100.0, 40.0)
            sc2 = col_sc2.number_input("Sconto 2 %", 0.0, 100.0, 0.0)
            sc3 = col_sc3.number_input("Sconto 3 %", 0.0, 100.0, 0.0)
            
            prezzo_netto = prezzo_listino * (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100)
            st.markdown(f"### Prezzo Netto: **{prezzo_netto:.2f} €**")
            
            st.divider()
            
            # --- TASTO AZZERA ---
            if st.button("🔄 Azzera Quantità"):
                for t in range(35, 51):
                    st.session_state[f"qta_{t}"] = 0
            
            st.write("**Inserisci Quantità:**")
            
            taglie = list(range(35, 51))
            quantita_taglie = {}
            
            # Griglia taglie
            cols1 = st.columns(8)
            for i in range(8):
                t = taglie[i]
                with cols1[i]:
                    if f"qta_{t}" not in st.session_state: st.session_state[f"qta_{t}"] = 0
                    quantita_taglie[t] = st.number_input(str(t), min_value=0, step=1, key=f"qta_{t}")
            
            cols2 = st.columns(8)
            for i in range(8, 16):
                t = taglie[i]
                with cols2[i-8]:
                    if f"qta_{t}" not in st.session_state: st.session_state[f"qta_{t}"] = 0
                    quantita_taglie[t] = st.number_input(str(t), min_value=0, step=1, key=f"qta_{t}")

            st.write("")
            if st.button("🛒 Aggiungi al Preventivo", use_container_width=True):
                aggiunti = 0
                for t, q in quantita_taglie.items():
                    if q > 0:
                        st.session_state['carrello'].append({
                            "Articolo": d['ARTICOLO'], "Taglia": t, "Quantità": q,
                            "Netto U.": f"{prezzo_netto:.2f} €", "Totale Riga": prezzo_netto * q,
                            "Immagine": str(d['IMMAGINE']).strip(),
                            "Prezzo_Val": prezzo_netto
                        })
                        aggiunti += 1
                if aggiunti > 0: st.success("Aggiunto!")
                else: st.warning("Inserisci una quantità!")
                
        with c2:
            url = str(d['IMMAGINE']).strip()
            if url.startswith('http'):
                try:
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                    st.image(BytesIO(r.content), caption=d['ARTICOLO'], use_container_width=True)
                except: st.write("Foto non disponibile")

# =========================================================
# --- CARRELLO E PDF ---
# =========================================================
if st.session_state['carrello']:
    st.divider()
    st.header("🛒 Riepilogo Preventivo")
    df_c = pd.DataFrame(st.session_state['carrello'])
    st.dataframe(df_c[["Articolo", "Taglia", "Quantità", "Netto U.", "Totale Riga"]], use_container_width=True)
    
    totale_generale = df_c["Totale Riga"].sum()
    st.markdown(f"### Totale Complessivo: **{totale_generale:.2f} €**")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        if st.button("🗑️ Svuota Tutto"):
            st.session_state['carrello'] = []
            st.rerun()
            
    with c_p2:
        if st.button("📄 Genera PDF", use_container_width=True):
            # Raggruppamento per articolo
            raggruppo = {}
            for r in st.session_state['carrello']:
                art = r["Articolo"]
                if art not in raggruppo:
                    raggruppo[art] = {"T": [], "Tot": 0, "Img": r["Immagine"], "Netto": r["Netto U."]}
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
                    self.cell(100, 10, testo, align="R", ln=True)
                    self.ln(20)

            pdf = PDF()
            pdf.add_page()
            
            for art, dati in raggruppo.items():
                y_inizio = pdf.get_y()
                
                # Controllo fine pagina
                if y_inizio > 230:
                    pdf.add_page()
                    y_inizio = pdf.get_y()

                # --- DISEGNO IMMAGINE (A DESTRA) ---
                if dati["Img"].startswith("http"):
                    try:
                        res = requests.get(dati["Img"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(res.content)
                            # Immagine allineata a y_inizio
                            pdf.image(tmp.name, x=155, y=y_inizio, w=35)
                        os.remove(tmp.name)
                    except:
                        pass

                # --- TESTO (A SINISTRA) ---
                p_p = str(dati['Netto']).replace('€', 'Euro')
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(135, 7, f"Modello: {art}", ln=True)
                pdf.set_font("helvetica", "I", 10)
                pdf.cell(135, 6, f"Prezzo Unitario: {p_p}", ln=True)
                
                pdf.set_font("helvetica", "", 10)
                # multi_cell per gestire liste di taglie lunghe
                pdf.multi_cell(135, 5, " | ".join(dati["T"]))
                
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(135, 7, f"Parziale: {dati['Tot']:.2f} Euro", ln=True)
                
                # Calcolo posizione finale per evitare sovrapposizioni
                y_fine_testo = pdf.get_y()
                y_fine_immagine = y_inizio + 40
                y_punto_di_arresto = max(y_fine_testo, y_fine_immagine)
                
                pdf.set_y(y_punto_di_arresto)
                pdf.ln(2)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

            # --- TOTALE FINALE ---
            pdf.ln(5)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"TOTALE GENERALE: {totale_generale:.2f} Euro", align="R", ln=True)
            
            pdf_out = pdf.output()
            b64 = base64.b64encode(pdf_out).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600"></iframe>', unsafe_allow_html=True)
            st.download_button("⬇️ Scarica PDF", data=bytes(pdf_out), file_name="Preventivo.pdf")
