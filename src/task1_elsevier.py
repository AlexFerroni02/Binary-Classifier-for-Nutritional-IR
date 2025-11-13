import pandas as pd
import time
import requests
from difflib import SequenceMatcher
import json
import os

# ---------------- CONFIGURATION ----------------
API_KEY = ""   
INPUT_FILE = "../data/abstracts.csv"
OUTPUT_FILE = "../data/abstracts.csv"


MAX_RETRIES = 3
SLEEP_BETWEEN_CALLS = 1.0
FUZZY_THRESHOLD = 0.93
# ------------------------------------------------

headers = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/json"
}


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def scopus_search(title):
    url = "https://api.elsevier.com/content/search/scopus"
    params = {"query": f'TITLE("{title}")'}

    for _ in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.json()
            time.sleep(2)
        except:
            time.sleep(2)
    return None


def get_doi_from_results(title, results):
    try:
        entries = results.get("search-results", {}).get("entry", [])
        if not entries:
            return None

        # Exact match
        for e in entries:
            if e.get("dc:title", "").strip().lower() == title.lower():
                return e.get("prism:doi")

        # Fuzzy
        best = None
        best_score = 0
        for e in entries:
            t = e.get("dc:title", "").strip()
            score = similar(title, t)
            if score > best_score:
                best_score = score
                best = e

        if best_score >= FUZZY_THRESHOLD:
            return best.get("prism:doi")

    except:
        return None

    return None


def extract_abstract(data):
    paths = [
        ["abstracts-retrieval-response", "coredata", "dc:description"],
        ["full-text-retrieval-response", "coredata", "dc:description"],
        ["abstracts-retrieval-response", "item", "bibrecord", "head", "abstracts", 0, "para"],
    ]

    for path in paths:
        try:
            val = data
            for key in path:
                val = val[key]
            if val:
                text = val if isinstance(val, str) else " ".join(val)
                return text.replace("<p>", "").replace("</p>", "").strip()
        except:
            pass

    return None


def get_abstract_from_doi(doi):
    urls = [
        f"https://api.elsevier.com/content/abstract/doi/{doi}",
        f"https://api.elsevier.com/content/article/doi/{doi}"
    ]

    for url in urls:
        for _ in range(MAX_RETRIES):
            try:
                r = requests.get(url, headers=headers, timeout=15)

                if r.status_code == 200:
                    try:
                        data = r.json()
                    except:
                        return None

                    abs_text = extract_abstract(data)
                    if abs_text:
                        return abs_text

                if r.status_code in [429, 503, 500]:
                    time.sleep(2)

            except:
                time.sleep(2)
    return None

def check_API_key(key):
    if not key:
        key = input("Paste your Scopus API key:\n").strip()
    return key



# ------------- MAIN FLOW ----------------

API_KEY = check_API_key(API_KEY)

df = pd.read_csv(INPUT_FILE)

if not all(c in df.columns for c in ["indice", "title", "abstract"]):
    raise ValueError("CSV must contain: indice, title, abstract")

start_index = 0

print(f"Resuming at row: {start_index}")

fail_list = []

for i in range(start_index, len(df)):
    row = df.iloc[i]
    idx = row["indice"]
    title = str(row["title"]).strip()

    if pd.notna(row["abstract"]) and len(str(row["abstract"]).strip()) > 5:
        continue

    print(f"\nSearching abstract for indice {idx}: {title}")

    results = scopus_search(title)
    if not results:
        print(" Scopus search failed")
        fail_list.append(idx)
        continue

    doi = get_doi_from_results(title, results)
    if not doi:
        print(" DOI not found")
        fail_list.append(idx)
        continue

    print(f" DOI found: {doi}")

    abstract = get_abstract_from_doi(doi)
    if not abstract:
        print(" Abstract fetch failed")
        fail_list.append(idx)
        continue

    print(" Abstract retrieved!")

    df.loc[i, "abstract"] = abstract

    df.to_csv(OUTPUT_FILE, index=False)
    time.sleep(SLEEP_BETWEEN_CALLS)


print("\ndone.")
print(f"Filled file {OUTPUT_FILE}")
