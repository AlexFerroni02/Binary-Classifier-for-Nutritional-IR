import pandas as pd
import numpy as np

# --- 1. GESTIONE DOCUMENTI RILEVANTI (CLASSE 1) ---

try:
    # Carica i tuoi documenti RILEVANTI originali (file CSV)
    df_relevant_all = pd.read_csv("../data/abstracts.csv")
    print(f"Caricati {len(df_relevant_all)} documenti RILEVANTI (prima del filtro).")
except FileNotFoundError:
    print("ERRORE: File '../data/abstract.csv' non trovato.")
    exit()

# Pulisci gli abstract (sostituisci 'None'/'NaN' con stringhe vuote)
df_relevant_all['abstract'] = df_relevant_all['abstract'].fillna('')

# --- FILTRO CHIAVE ---
# Tieni solo le righe dove l'abstract NON è una stringa vuota
df_relevant = df_relevant_all[df_relevant_all['abstract'].str.strip() != ''].copy()
N_DATASET_SIZE = len(df_relevant) # Questa sarà la nostra dimensione target

print(f"Documenti RILEVANTI tenuti (con Abstract): {N_DATASET_SIZE}")

# --- 2. GESTIONE DOCUMENTI NON RILEVANTI (CLASSE 0) ---

try:
    # Carica TUTTI i documenti NON rilevanti (file Excel)
    df_non_relevant_all = pd.read_excel("../data/publications_with_all_abstracts.xlsx")
    print(f"Caricati {len(df_non_relevant_all)} documenti NON RILEVANTI (prima del campionamento).")
except FileNotFoundError:
    print("ERRORE: File '../data/publications_with_all_abstracts.xlsx' non trovato.")
    exit()

# --- CAMPIONAMENTO CHIAVE ---
# Estrai a caso un numero N_DATASET_SIZE di campioni per bilanciare
df_non_relevant = df_non_relevant_all.sample(
    n=N_DATASET_SIZE,
    random_state=42 # random_state è importante per la riproducibilità
).copy()

print(f"Documenti NON RILEVANTI campionati: {len(df_non_relevant)}")

# --- 3. ETICHETTATURA E COMBINAZIONE ---

df_relevant['label'] = 1
df_non_relevant['label'] = 0

# Combina Titolo e Abstract
df_relevant['text'] = df_relevant['title'].fillna('') + " " + df_relevant['abstract'].fillna('')
df_non_relevant['text'] = df_non_relevant['title'].fillna('') + " " + df_non_relevant['abstract'].fillna('')

# Seleziona solo le colonne che ci servono
df_relevant_final = df_relevant[['text', 'label']]
df_non_relevant_final = df_non_relevant[['text', 'label']]

# Unisci i due DataFrame (ora sono bilanciati)
df_master = pd.concat([df_relevant_final, df_non_relevant_final], ignore_index=True)

# Mescola il dataset
df_master = df_master.sample(frac=1, random_state=42).reset_index(drop=True)

# --- 4. SALVATAGGIO ---
# Salva il file master nella stessa cartella 'data'
df_master.to_csv("../data/master_dataset_pulito.csv", index=False)

print(f"\nDataset 'master_dataset_pulito.csv' creato con successo.")
print(f"Totale documenti: {len(df_master)}")
print(f"Distribuzione classi (ora bilanciata):\n{df_master['label'].value_counts()}")