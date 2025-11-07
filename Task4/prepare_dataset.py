# python
import pandas as pd
import numpy as np
import sys

# --- 1. GESTIONE DOCUMENTI RILEVANTI (CLASSE 1) ---

try:
    df_relevant_all = pd.read_csv("../data/abstracts_filled.csv")
    print(f"Caricati {len(df_relevant_all)} documenti RILEVANTI (prima del filtro).")
except FileNotFoundError:
    print("ERRORE: File `../data/abstracts_filled.csv` non trovato.")
    sys.exit(1)

# Assicurati che ci siano le colonne attese
for col in ['title', 'abstract']:
    if col not in df_relevant_all.columns:
        print(f"ERRORE: Colonna `{col}` non trovata in `../data/abstracts_filled.csv`.")
        sys.exit(1)

# Pulisci gli abstract/title (sostituisci NaN con stringhe vuote) e strip
df_relevant_all['abstract'] = df_relevant_all['abstract'].fillna('').astype(str)
df_relevant_all['title'] = df_relevant_all['title'].fillna('').astype(str)
df_relevant_all['abstract_stripped'] = df_relevant_all['abstract'].str.strip()
df_relevant_all['title_stripped'] = df_relevant_all['title'].str.strip()

# Tieni solo le righe dove l'abstract NON è vuoto
df_relevant = df_relevant_all[df_relevant_all['abstract_stripped'] != ''].copy()

# Scarta le righe dove title == abstract (dopo strip)
df_relevant = df_relevant[df_relevant['title_stripped'] != df_relevant['abstract_stripped']].copy()

N_DATASET_SIZE = len(df_relevant)
print(f"Documenti RILEVANTI tenuti (con Abstract valido e diverso dal Title): {N_DATASET_SIZE}")

if N_DATASET_SIZE == 0:
    print("ERRORE: Nessun documento rilevante disponibile dopo i filtri.")
    sys.exit(1)

# --- 2. GESTIONE DOCUMENTI NON RILEVANTI (CLASSE 0) ---

try:
    df_non_relevant_all = pd.read_excel("../data/non_relevant_publications.xlsx")
    print(f"Caricati {len(df_non_relevant_all)} documenti NON RILEVANTI (prima del campionamento).")
except FileNotFoundError:
    print("ERRORE: File `../data/non_relevant_publications.xlsx` non trovato.")
    sys.exit(1)

if len(df_non_relevant_all) < N_DATASET_SIZE:
    print("ERRORE: Non ci sono abbastanza documenti NON RILEVANTI per bilanciare il dataset.")
    sys.exit(1)

df_non_relevant = df_non_relevant_all.sample(
    n=N_DATASET_SIZE,
    random_state=42
).copy()

print(f"Documenti NON RILEVANTI campionati: {len(df_non_relevant)}")

# --- 3. ETICHETTATURA E COMBINAZIONE ---

df_relevant['label'] = 1
df_non_relevant['label'] = 0

# Usa solo l'abstract come text (non più title + abstract)
df_relevant['text'] = df_relevant['abstract'].fillna('')
# Per i non rilevanti manteniamo la colonna 'Abstract' usata in precedenza
df_non_relevant['text'] = df_non_relevant['Abstract'].fillna('')

df_relevant_final = df_relevant[['text', 'label']]
df_non_relevant_final = df_non_relevant[['text', 'label']]

df_master = pd.concat([df_relevant_final, df_non_relevant_final], ignore_index=True)
df_master = df_master.sample(frac=1, random_state=42).reset_index(drop=True)

# --- 4. SALVATAGGIO ---
df_master.to_csv("../data/master_dataset_pulito.csv", index=False)

print(f"\nDataset `master_dataset_pulito.csv` creato con successo.")
print(f"Totale documenti: {len(df_master)}")
print(f"Distribuzione classi (ora bilanciata):\n{df_master['label'].value_counts()}")
