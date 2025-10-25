import pandas as pd
from datasets import Dataset, DatasetDict
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
import numpy as np
import torch

# Controlla se è disponibile una GPU (MOLTO raccomandato)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Utilizzo del dispositivo: {device}")

# --- 1. CARICARE I SET DI DATI ---
try:
    train_df = pd.read_csv("train_set.csv")
    val_df = pd.read_csv("validation_set.csv")
    test_df = pd.read_csv("test_set.csv")
except FileNotFoundError:
    print("ERRORE: File di set non trovati.")
    print("Esegui prima 'split_data.py'.")
    exit()

# Converti i DataFrame di Pandas in 'Dataset' di Hugging Face
ds = DatasetDict({
    'train': Dataset.from_pandas(train_df),
    'validation': Dataset.from_pandas(val_df),
    'test': Dataset.from_pandas(test_df)
})

print(f"Dataset caricati:\n{ds}")

# --- 2. CARICARE TOKENIZER E MODELLO ---
MODEL_NAME = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract"

# Carica il Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Carica il Modello
# num_labels=2 (classe 0 e classe 1)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
model.to(device)  # Sposta il modello sulla GPU se disponibile


# --- 3. TOKENIZZARE I DATI ---
def tokenize_function(examples):
    # 'truncation=True' taglia i testi più lunghi di 512 token
    # 'padding="max_length"' aggiunge token finti fino a 512
    return tokenizer(examples['text'], padding="max_length", truncation=True, max_length=512)


# Applica la tokenizzazione a tutti i set in parallelo
tokenized_datasets = ds.map(tokenize_function, batched=True)

# Rimuovi la colonna 'text' (non più necessaria) e formatta per il training
tokenized_datasets = tokenized_datasets.remove_columns(["text"])
tokenized_datasets.set_format("torch")

print(f"\nDati tokenizzati. Esempio (train):\n{tokenized_datasets['train'][0]}")


# --- 4. DEFINIRE LE METRICHE DI VALUTAZIONE ---
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)

    acc = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='binary')
    precision = precision_score(labels, predictions, average='binary')
    recall = recall_score(labels, predictions, average='binary')

    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }


# --- 5. DEFINIRE GLI ARGOMENTI DI TRAINING ---
training_args = TrainingArguments(
    output_dir="./polyphenol_classifier",  # Cartella dove salvare il modello
    evaluation_strategy="epoch",  # Valuta alla fine di ogni epoca
    save_strategy="epoch",  # Salva il modello alla fine di ogni epoca
    num_train_epochs=3,  # 3 epoche sono un buon punto di partenza
    per_device_train_batch_size=8,  # Riduci se la tua GPU ha poca VRAM (es. a 4)
    per_device_eval_batch_size=8,
    learning_rate=2e-5,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    logging_steps=10,
    load_best_model_at_end=True,  # Carica il modello migliore alla fine
    metric_for_best_model="f1",  # Scegli il modello migliore in base all'F1-score
    report_to="none"  # Disabilita il logging online (wandb)
)

# --- 6. CREARE IL TRAINER ---
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    compute_metrics=compute_metrics,
    tokenizer=tokenizer,
)

# --- 7. AVVIARE IL TRAINING (FINE-TUNING) ---
print("\n--- INIZIO FINE-TUNING MODELLO ---")
trainer.train()
print("--- FINE-TUNING COMPLETATO ---")

# --- 8. VALUTAZIONE FINALE SUL TEST SET ---
print("\n--- VALUTAZIONE SUL TEST SET (DATI MAI VISTI) ---")
test_results = trainer.evaluate(eval_dataset=tokenized_datasets["test"])

print(f"Accuracy sul Test Set: {test_results['eval_accuracy']:.4f}")
print(f"F1-score sul Test Set: {test_results['eval_f1']:.4f}")
print(f"Precision sul Test Set: {test_results['eval_precision']:.4f}")
print(f"Recall sul Test Set: {test_results['eval_recall']:.4f}")

# Salva i risultati finali su un file
with open("test_results.txt", "w") as f:
    f.write(str(test_results))

# Salva il modello finale
trainer.save_model("./polyphenol_classifier_final")
print("Modello finale salvato in './polyphenol_classifier_final'")