import pandas as pd

file_name = 'listino_agente.xlsx'

try:
    # Carichiamo l'Excel
    df = pd.read_excel(file_name)
    
    # Selezioniamo solo le colonne che ci servono davvero
    # Questo evita confusione con la colonna A
    colonne_utili = ['ARTICOLO', 'RANGE TAGLIE', 'LISTINO', 'IMMAGINE']
    df_pulito = df[colonne_utili]

    print("--- Ricerca Prodotto per Preventivo ---")
    ricerca = input("Inserisci il nome dell'ARTICOLO: ").strip().upper()

    # Cerchiamo l'articolo (anche parziale)
    risultato = df_pulito[df_pulito['ARTICOLO'].astype(str).str.contains(ricerca, na=False)]

    if not risultato.empty:
        # Se ci sono più risultati, prendiamo il primo per semplicità
        articolo_scelto = risultato.iloc[0]
        
        print("\n✅ Articolo Selezionato:")
        print(f"Modello:      {articolo_scelto['ARTICOLO']}")
        print(f"Taglie:       {articolo_scelto['RANGE TAGLIE']}")
        print(f"Prezzo:       {articolo_scelto['LISTINO']}€")
        print(f"Rif. Immagine: {articolo_scelto['IMMAGINE']}")
        
        # Salviamo queste info per il prossimo passo
        preventivo_corrente = articolo_scelto.to_dict()
    else:
        print("❌ Nessun articolo trovato.")

except Exception as e:
    print(f"Errore durante la lettura: {e}")
