import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# --- 1. CONFIGURAZIONE ---

# Specifica il percorso della cartella dove hai salvato il modello finale
MODEL_PATH = "./polyphenol_classifier_final"

# Controlla se è disponibile una GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Utilizzo del dispositivo: {device}")

# --- 2. CARICAMENTO MODELLO E TOKENIZER ---

print("Caricamento del modello e del tokenizer...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    # Sposta il modello sulla GPU (o CPU se non c'è GPU)
    model.to(device)
    model.eval()  # Metti il modello in modalità "valutazione" (disattiva il dropout, ecc.)
    print("Modello caricato con successo.")
except OSError:
    print(f"ERRORE: La cartella del modello '{MODEL_PATH}' non è stata trovata.")
    print("Assicurati di aver eseguito 'train_model.py' e che il percorso sia corretto.")
    exit()


# --- 3. FUNZIONE DI PREDIZIONE ---

def predict_abstract(title, abstract):
    """
    Classifica un abstract combinato con un titolo.
    Restituisce la classe predetta (0 o 1) e il punteggio di confidenza (softmax).
    """
    # Combina titolo e abstract
    text = str(title) + " " + str(abstract)
    if not text.strip():
        print("Input vuoto, impossibile classificare.")
        return None, None

    # Tokenizza il testo
    # return_tensors='pt' -> restituisce PyTorch Tensors
    inputs = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors='pt'
    )

    # Sposta i tensori di input sul dispositivo corretto (GPU/CPU)
    inputs = {key: val.to(device) for key, val in inputs.items()}

    # Esegui la predizione
    # 'with torch.no_grad():' disattiva il calcolo del gradiente (più veloce, meno memoria)
    with torch.no_grad():
        outputs = model(**inputs)

    # Ottieni i "logits" (i punteggi grezzi del modello)
    logits = outputs.logits

    # Applica la funzione Softmax per ottenere le probabilità (da 0 a 1)
    probabilities = torch.softmax(logits, dim=-1).cpu().numpy()[0]

    # Trova la classe con la probabilità più alta (0 o 1)
    predicted_class_id = np.argmax(probabilities)

    # Ottieni il punteggio di confidenza per quella classe
    confidence = probabilities[predicted_class_id]

    return predicted_class_id, confidence


# --- 4. ESEMPIO DI UTILIZZO ---

if __name__ == "__main__":
    # Esempio 1: Testo chiaramente RILEVANTE (dovrebbe dare 1)
    test_title_1 = "The antioxidant activity of flavonoids and polyphenols in grapes"
    test_abstract_1 = "We analyzed the total polyphenol content (TPC) in different grape varieties. Our findings show that red grapes have significantly higher concentrations of resveratrol and other polyphenols, which contribute to strong antioxidant effects."

    pred_1, conf_1 = predict_abstract(test_title_1, test_abstract_1)

    print("\n--- TEST 1 (RILEVANTE) ---")
    print(f"Titolo: {test_title_1}")
    print(f"Predizione: {'Rilevante (1)' if pred_1 == 1 else 'Non Rilevante (0)'}")
    print(f"Confidenza: {conf_1 * 100:.2f}%")

    # Esempio 2: Testo chiaramente NON RILEVANTE (dovrebbe dare 0)
    test_title_2 = "A study on the migration patterns of arctic birds"
    test_abstract_2 = "This paper investigates the effects of climate change on the seasonal migration routes of Sterna paradisaea. We used satellite tracking to monitor 20 birds over a period of 5 years. The dataset shows a significant shift northwards."

    pred_2, conf_2 = predict_abstract(test_title_2, test_abstract_2)

    print("\n--- TEST 2 (NON RILEVANTE) ---")
    print(f"Titolo: {test_title_2}")
    print(f"Predizione: {'Rilevante (1)' if pred_2 == 1 else 'Non Rilevante (0)'}")
    print(f"Confidenza: {conf_2 * 100:.2f}%")

    # Esempio 3: Testo ambiguo (vediamo cosa fa)
    test_title_3 = "Nutritional analysis of common breakfast cereals"
    test_abstract_3 = "We analyzed the fiber, sugar, and vitamin content of 15 popular breakfast cereals. Results indicate high levels of added sugars. Some products contained whole grains, which are a source of natural compounds."

    pred_3, conf_3 = predict_abstract(test_title_3, test_abstract_3)

    print("\n--- TEST 3 (AMBIGUO/CEREALI) ---")
    print(f"Titolo: {test_title_3}")
    print(f"Predizione: {'Rilevante (1)' if pred_3 == 1 else 'Non Rilevante (0)'}")
    print(f"Confidenza: {conf_3 * 100:.2f}%")