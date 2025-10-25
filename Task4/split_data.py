import pandas as pd
from sklearn.model_selection import train_test_split

# Carica il dataset master
try:
    df = pd.read_csv("../data/master_dataset_pulito.csv")
except FileNotFoundError:
    print("ERRORE: 'master_dataset.csv' non trovato.")
    print("Esegui prima 'prepare_dataset.py'.")
    exit()

# Definisci le dimensioni
TEST_SIZE = 0.15  # 15% del totale per il test set
VAL_SIZE = 0.15   # 15% del totale per il validation set
# Il restante 70% sarà per il training

# Separa features (X) e label (y)
X = df['text']
y = df['label']

# --- PRIMO SPLIT: Training+Validation vs. Test ---
# Il test set lo mettiamo da parte e non lo tocchiamo più.
X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y,
    test_size=TEST_SIZE,
    random_state=42,
    stratify=y # Fondamentale per bilanciare le classi
)

# --- SECONDO SPLIT: Training vs. Validation ---
# Ora dividiamo il blocco 'train_val'
# Dobbiamo ricalcolare la proporzione per il validation set
# (es. 0.15 / (1.0 - 0.15) = 0.1765 circa)
val_proportion = VAL_SIZE / (1.0 - TEST_SIZE)

X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val,
    test_size=val_proportion,
    random_state=42,
    stratify=y_train_val # Stratifichiamo anche qui
)

# --- SALVATAGGIO DEI SET ---

# Creiamo dei DataFrame e salviamoli
train_df = pd.DataFrame({'text': X_train, 'label': y_train})
val_df = pd.DataFrame({'text': X_val, 'label': y_val})
test_df = pd.DataFrame({'text': X_test, 'label': y_test})

train_df.to_csv("train_set.csv", index=False)
val_df.to_csv("validation_set.csv", index=False)
test_df.to_csv("test_set.csv", index=False)

print("Suddivisione dati completata.")
print(f"Documenti di Training:   {len(train_df)}")
print(f"Documenti di Validation: {len(val_df)}")
print(f"Documenti di Testing:    {len(test_df)}")