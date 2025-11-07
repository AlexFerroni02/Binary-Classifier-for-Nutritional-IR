# python
import pandas as pd
from pathlib import Path

def main():
    path = Path(__file__).resolve().parents[1] / "data" / "non_relevant_publications.xlsx"
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        print(f"ERRORE: file `{path}` non trovato.")
        return

    # trova la colonna Abstract (case-insensitive)
    col = next((c for c in df.columns if c.lower() == "abstract"), None)
    if col is None:
        print("ERRORE: colonna `Abstract` non trovata. Colonne presenti:")
        print(", ".join(df.columns))
        return

    texts = df[col].fillna("").astype(str)
    is_empty = texts.str.strip() == ""
    n_empty = int(is_empty.sum())
    total = len(df)
    pct = (n_empty / total * 100) if total else 0.0

    print(f"Totale righe: {total}")
    print(f"Abstract vuoti: {n_empty} ({pct:.2f}%)")
    if n_empty:
        print("Esempi di indici con abstract vuoto:", list(df.index[is_empty][:10]))

if __name__ == "__main__":
    main()
