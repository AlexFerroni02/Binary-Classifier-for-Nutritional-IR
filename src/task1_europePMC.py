import pandas as pd
import requests
import time
import csv
import os

INPUT_FILE = "../data/abstracts_filled.csv"
OUTPUT_FILE = "../data/abstracts_filled.csv"
SLEEP = 0.4

def safe_read(path):
    try:
        return pd.read_csv(path, sep=",", quotechar='"', escapechar="\\", engine="python")
    except:
        return pd.read_csv(path, on_bad_lines="skip")

df = safe_read(INPUT_FILE)

required = ["indice","title","abstract"]
for c in required:
    if c not in df.columns:
        raise ValueError(f"Column missing: {c}")

# resume
start = 0
if os.path.exists(OUTPUT_FILE):
    prev = safe_read(OUTPUT_FILE)
    if len(prev)==len(df):
        df = prev
        start = df["abstract"].notna().sum()
        print(f"Resuming at row {start}")

def crossref_doi(title):
    url = "https://api.crossref.org/works"
    p = {"query.title": title, "rows": 1}
    try:
        r = requests.get(url, params=p, timeout=10)
        items = r.json()["message"]["items"]
        if not items: return None
        return items[0].get("DOI")
    except:
        return None

def semantic_abstract(doi):
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract"
        r = requests.get(url, timeout=10)
        return r.json().get("abstract")
    except:
        return None

def openalex_abstract(doi):
    try:
        url = f"https://api.openalex.org/works/doi:{doi}"
        r = requests.get(url, timeout=10)
        return r.json().get("abstract")
    except:
        return None

def europepmc_title(title):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {"query": f'"{title}"', "format":"json", "pageSize":1}
    try:
        r = requests.get(url, params=params, timeout=10)
        res = r.json().get("resultList",{}).get("result",[])
        if not res: return None
        return res[0].get("abstractText")
    except:
        return None

for i in range(start, len(df)):
    title = str(df.at[i,"title"])
    if pd.notna(df.at[i,"abstract"]) and df.at[i,"abstract"].strip():
        continue

    print(f"\n{df.at[i,'indice']} — {title}")

    # 1) DOI via CrossRef
    doi = crossref_doi(title)
    print("DOI:", doi)

    abstract = None
    if doi:
        abstract = semantic_abstract(doi) or openalex_abstract(doi)

    # fallback: EuropePMC
    if not abstract:
        abstract = europepmc_title(title)

    if abstract:
        print(" Abstract found")
        df.at[i,"abstract"] = abstract
    else:
        print("No abstract found")

    df.to_csv(OUTPUT_FILE, index=False, quoting=csv.QUOTE_ALL, escapechar="\\")
    time.sleep(SLEEP)
