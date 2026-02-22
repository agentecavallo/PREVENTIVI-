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

# 1. Controllo esistenza file
file_path = 'Listino_agente.xlsx'

if not os.path.exists(file_path):
    st.error(f"⚠️ Il file '{file_path}' non esiste nella cartella di sinistra!")
    st.stop()

# 2. Caricamento dati
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
            
            st.write("")
            
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
                            "Immagine": str(d['IMMAGINE']).strip() # Salviamo anche l'immagine per il PDF
                        }
                        st.session_state['carrello'].append(articolo_da_aggiungere)
                        aggiunti += 1
                
                if aggiunti > 0:
                    st.success(f"✅ Aggiunte correttamente {aggiunti} righe di {d['ARTICOLO']} al preventivo!")
                else:
                    st.warning("⚠️ Non hai inserito nessuna quantità!")
                
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
else:
    st.info("Inserisci il nome di un articolo a sinistra per iniziare.")


# =========================================================
# --- SEZIONE CARRELLO E GENERAZIONE PDF ---
# =========================================================

if len(st.session_state['carrello']) > 0:
    st.divider()
    st.header("🛒 Riepilogo Preventivo")
    
    df_carrello = pd.DataFrame(st.session_state['carrello'])
    
    # Mostriamo a schermo una tabella semplificata (senza l'URL dell'immagine)
    st.dataframe(df_carrello.drop(columns=["Immagine"]), use_container_width=True)
    
    totale_pezzi = df_carrello["Quantità"].sum()
    totale_finale = df_carrello["Totale Riga"].sum()
    
    st.markdown(f"**Totale Pezzi:** {totale_pezzi}")
    st.markdown(f"## Totale Finale: {totale_finale:.2f} €")
    
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    
    with c_btn1:
        if st.button("🗑️ Svuota Preventivo"):
            st.session_state['carrello'] = []
            st.rerun()
            
    with c_btn2:
        if st.button("📄 Genera e Apri PDF"):
            # Raggruppiamo il carrello per Articolo per fare una riga per modello
            raggruppamento = {}
            for riga in st.session_state['carrello']:
                art = riga["Articolo"]
                if art not in raggruppamento:
                    raggruppamento[art] = {
                        "Taglie": [],
                        "Totale_Modello": 0,
                        "Immagine": riga.get("Immagine", "")
                    }
                raggruppamento[art]["Taglie"].append(f"Tg {riga['Taglia']}: {riga['Quantità']}pz")
                raggruppamento[art]["Totale_Modello"] += riga["Totale Riga"]

            # --- CREAZIONE DEL PDF ---
            class PDF(FPDF):
                def header(self):
                    self.set_font("helvetica", "B", 16)
                    self.cell(0, 10, "Preventivo Ordine", align="C", new_x="LMARGIN", new_y="NEXT")
                    self.ln(5)

            pdf = PDF()
            pdf.add_page()
            
            for art, dati in raggruppamento.items():
                y_start = pdf.get_y() # Salviamo la posizione verticale per affiancare l'immagine
                
                # Testi
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(130, 8, f"Modello: {art}", new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("helvetica", "", 10)
                taglie_str = " | ".join(dati["Taglie"])
                pdf.multi_cell(130, 6, f"Sviluppo Taglie:\n{taglie_str}")
                
                pdf.set_font("helvetica", "B", 11)
                pdf.cell(130, 8, f"Totale per questo modello: {dati['Totale_Modello']:.2f} Euro", new_x="LMARGIN", new_y="NEXT")
                
                # Gestione Immagine
                if dati["Immagine"].startswith("http"):
                    try:
                        r = requests.get(dati["Immagine"], headers={'User-Agent': 'Mozilla'}, timeout=2)
                        if r.status_code == 200:
                            # Salviamo l'immagine in un file temporaneo invisibile per farla leggere al PDF
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                                tmp.write(r.content)
                                tmp_path = tmp.name
                            # Incolliamo l'immagine sulla destra (x=140)
                            pdf.image(tmp_path, x=140, y=y_start, w=40)
                            os.remove(tmp_path) # Pulizia file temporaneo
                    except:
                        pass # Se l'immagine fallisce, andiamo avanti senza far bloccare l'app
                
                # Spazio sotto ogni riga
                if pdf.get_y() < y_start + 45:
                    pdf.set_y(y_start + 45)
                
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
            
            # Aggiunta del totale finale in fondo al PDF
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"TOTALE FINALE PREVENTIVO: {totale_finale:.2f} Euro", align="R", new_x="LMARGIN", new_y="NEXT")

            # Estraiamo i dati del PDF per mostrarli e scaricarli
            pdf_bytes = bytes(pdf.output())
            
            # --- MOSTRA IL PDF SUBITO A SCHERMO ---
            st.success("✅ PDF Generato con successo!")
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # --- PULSANTE PER IL DOWNLOAD VERO E PROPRIO ---
            st.download_button(
                label="⬇️ Scarica il PDF sul computer",
                data=pdf_bytes,
                file_name="Preventivo.pdf",
                mime="application/pdf"
            )
