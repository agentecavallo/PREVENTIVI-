import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import tempfile
import base64
from fpdf import FPDF

st.set_page_config(page_title="Generatore Preventivi", layout="wide")

# --- INIZIALIZZAZIONE DELLA MEMORIA (CARRELLO) ---
if 'carrello' not in st.session_state:
    st.session_state['carrello'] = []

# 1. Controllo esistenza file Excel
file_path = 'Listino_agente.xlsx'

if not os.path.exists(file_path):
    st.error(f"⚠️ Il file '{file_path}' non esiste nella cartella!")
    st.stop()

# 2. Caricamento dati
try:
    df = pd.read_excel(file_path)
    df.columns = [str(c).strip().upper() for c in df.columns]
except Exception as e:
    st.error(f"❌ Errore nel leggere l'Excel: {e}")
    st.stop()

st.title("📄 Realizzatore di Offerte")

# --- NUOVO CAMPO: NOME CLIENTE ---
st.sidebar.header("Dati Documento")
nome_cliente = st.sidebar.text_input("Nome del Cliente:", placeholder="Inserisci nome azienda o persona")

# 3. Interfaccia di ricerca
st.sidebar.divider()
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
            
            st.write("**Applica Sconti (%)**")
            col_sconto1, col_sconto2, col_sconto3 = st.columns(3)
            sc1 = col_sconto1.number_input("Sconto 1 (%)", min_value=0.0, max_value=100.0, step=1.0, value=40.0)
            sc2 = col_sconto2.number_input("Sconto 2 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            sc3 = col_sconto3.number_input("Sconto 3 (%)", min_value=0.0, max_value=100.0, step=1.0, value=0.0)
            
            prezzo_netto = prezzo_listino * (1 - sc1/100) * (1 - sc2/100) * (1 - sc3/100)
            st.markdown(f"### Prezzo Netto: {prezzo_netto:.2f} €")
            
            st.divider()
            
            if st.button("🔄 Azzera Quantità"):
                for taglia in range(35, 51):
                    st.session_state[f"qta_{taglia}"] = 0
            
            st.write("**Sviluppo Taglie (Inserisci le quantità):**")
            taglie_disponibili = list(range(35, 51))
            
            cols_taglie = st.columns(4)
            quantita_taglie = {}
            
            for i, taglia in enumerate(taglie_disponibili):
                col_idx = i % 4
                with cols_taglie[col_idx]:
                    if f"qta_{taglia}" not in st.session_state:
                        st.session_state[f"qta_{taglia}"] = 0
                    quantita_taglie[taglia] = st.number_input(
                        f"Tg {taglia}", min_value=0, step=1, key=f"qta_{taglia}"
                    )
            
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
                            "Totale Riga": prezzo_netto * qta,
                            "Immagine": str(d['IMMAGINE']).strip()
                        }
                        st.session_state['carrello'].append(articolo_da_aggiungere)
                        aggiunti += 1
                
                if aggiunti > 0:
                    st.success(f"✅ Aggiunto {d['ARTICOLO']} al preventivo!")
                else:
                    st.warning("⚠️ Inserisci almeno una quantità!")
                
        with c2:
            st.subheader("Foto")
            url = str(d['IMMAGINE']).strip()
            if url.startswith('http'):
                try:
                    h = {'User-Agent': 'Mozilla/5.0'}
                    r = requests.get(url, headers=h, timeout=5)
                    st.image(BytesIO(r.content), use_container_width=True)
                except:
                    st.write("Immagine non caricabile.")
    else:
        st.warning("Nessun articolo trovato.")

# =========================================================
# --- SEZIONE CARRELLO E GENERAZIONE PDF ---
# =========================================================

if len(st.session_state['carrello']) > 0:
    st.divider()
    st.header("🛒 Riepilogo Preventivo")
    
    df_carrello = pd.DataFrame(st.session_state['carrello'])
    st.dataframe(df_carrello.drop(columns=["Immagine"]), use_container_width=True)
    
    totale_finale = df_carrello["Totale Riga"].sum()
    st.markdown(f"## Totale Finale: {totale_finale:.2f} €")
    
    c_btn1, c_btn2 = st.columns(2)
    
    with c_btn1:
        if st.button("🗑️ Svuota Tutto"):
            st.session_state['carrello'] = []
            st.rerun()
            
    with c_btn2:
        if st.button("📄 Genera e Apri PDF"):
            raggruppamento = {}
            for riga in st.session_state['carrello']:
                art = riga["Articolo"]
                if art not in raggruppamento:
                    raggruppamento[art] = {
                        "Taglie": [], "Totale_Modello": 0,
                        "Immagine": riga.get("Immagine", ""),
                        "Prezzo_Netto": riga["Netto U."]
                    }
                raggruppamento[art]["Taglie"].append(f"Tg {riga['Taglia']}: {riga['Quantità']}pz")
                raggruppamento[art]["Totale_Modello"] += riga["Totale Riga"]

            class PDF(FPDF):
                def header(self):
                    # Logo a sinistra
                    for nome_f in ["logo.png", "logo.jpg", "logo.jpeg"]:
                        if os.path.exists(nome_f):
                            self.image(nome_f, 10, 8, 33)
                            break
                    
                    # Nome cliente in alto a destra
                    self.set_font("helvetica", "B", 12)
                    self.set_xy(110, 15)
                    testo_cliente = f"Spett.le {nome_cliente}" if nome_cliente else "Spett.le Cliente"
                    self.cell(90, 10, testo_cliente, align="R", ln=True)
                    self.ln(20)

            pdf = PDF()
            pdf.add_page()
            
            for art, dati in raggruppamento.items():
                y_start = pdf.get_y()
                prezzo_pulito = str(dati['Prezzo_Netto']).replace('€', 'Euro')
                
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(130, 8, f"Modello: {art} - Prezzo: {prezzo_pulito}", ln=True)
                
                pdf.set_font("helvetica", "", 10)
                taglie_str = " | ".join(dati["Taglie"])
                pdf.multi_cell(130, 6, f"Sviluppo Taglie:\n{taglie_str}")
                
                pdf.set_font("helvetica", "B", 11)
                pdf.cell(130, 8, f"Totale modello: {dati['Totale_Modello']:.2f} Euro", ln=True)
                
                if dati["Immagine"].startswith("http"):
                    try:
                        r = requests.get(dati["Immagine"], headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
                        if r.status_code == 200:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                                tmp.write(r.content)
                                tmp_path = tmp.name
                            pdf.image(tmp_path, x=145, y=y_start, w=40)
                            os.remove(tmp_path)
                    except: pass
                
                if pdf.get_y() < y_start + 45: pdf.set_y(y_start + 45)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
            
            pdf.ln(10)
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"TOTALE GENERALE: {totale_finale:.2f} Euro", align="R", ln=True)

            pdf_bytes = bytes(pdf.output())
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            st.download_button(label="⬇️ Scarica PDF", data=pdf_bytes, file_name=f"Preventivo_{nome_cliente}.pdf", mime="application/pdf")
