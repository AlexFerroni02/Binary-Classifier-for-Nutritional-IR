import pandas as pd
import requests
import time
import csv
import re

INPUT_FILE = "../data/abstracts.csv"
OUTPUT_FILE = "../data/abstracts.csv"
SLEEP = 2

def safe_read(path):
    try:
        return pd.read_csv(path, sep=",", quotechar='"', escapechar="\\", engine="python")
    except:
        return pd.read_csv(path, on_bad_lines="skip")

def sanitize_title(title):
    return re.sub(r"[\n\r\t]+", " ", str(title)).strip()

df = safe_read(INPUT_FILE)
required = ["indice", "title", "abstract"]
for c in required:
    if c not in df.columns:
        raise ValueError(f"Missing column: {c}")

start = 0

def crossref_doi(title):
    url = "https://api.crossref.org/works"
    params = {"query.title": title, "rows": 1}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        if not items:
            return None
        return items[0].get("DOI")
    except Exception as e:
        print("Error CrossRef:", e)
        return None

def europepmc_title(title, doi=None):
    title = sanitize_title(title)
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    
    queries = []
    if doi:
        queries.append(f"DOI:{doi}")
    queries.append(title) 
    
    for q in queries:
        params = {"query": q, "format": "json", "pageSize": 1, "resulttype": "core"}
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            results = data.get("resultList", {}).get("result", [])
            if not results:
                continue
            item = results[0]
            abs_text = item.get("abstractText") or item.get("abstract")
            if abs_text:
                return abs_text
        except Exception as e:
            print(f"EuropePMC errore con query {q}:", e)
    return None

for i in range(start, len(df)):
    title = sanitize_title(df.at[i, "title"])
    
    if pd.notna(df.at[i, "abstract"]) and df.at[i, "abstract"].strip():
        continue

    print(f"\n{df.at[i, 'indice']} — {title}")

    doi = crossref_doi(title)
    if doi:
        print("DOI found:", doi)

    abstract = europepmc_title(title, doi)

    if abstract:
        print("Abstract found!")
        df.at[i, "abstract"] = abstract
    else:
        print("No abstract")

    df.to_csv(OUTPUT_FILE, index=False, quoting=csv.QUOTE_ALL, escapechar="\\")

    time.sleep(SLEEP)

print("\nFile saved in ", OUTPUT_FILE)
