import requests
import pandas as pd
import time

# File di input
df = pd.read_csv("../data/abstracts.csv")

# Filtriamo i titoli con abstract mancante
missing_df = df[df['abstract'].isna() | (df['abstract'].str.strip() == "")]
print(f"Totale articoli senza abstract: {len(missing_df)}")


semantic_scholar_url = "https://api.semanticscholar.org/graph/v1/paper/search"

for idx, row in missing_df.iterrows():
    title = row['title']
    print(f"\n🔎 Searching Semantic Scholar: {title}")

    abstract_text = None
    try:
        s_params = {"query": title, "limit": 1, "fields": "title,abstract"}
        s_resp = requests.get(semantic_scholar_url, params=s_params, timeout=15)
        s_data = s_resp.json()
        papers = s_data.get("data", [])
        if papers:
            paper = papers[0]
            abstract_text = paper.get("abstract")
    except Exception as e:
        print("Errore Semantic Scholar:", e)

    # Aggiorniamo la cella
    if abstract_text:
        df.at[idx, "abstract"] = abstract_text

    time.sleep(0.5)  # evita overload API

# Salva un nuovo file Excel con tutti gli abstract
df.to_csv("../data/abstracts.csv", index=False)
