import pandas as pd
import requests
import time
import csv
import os

INPUT_FILE = "../data/abstracts.csv"
OUTPUT_FILE = "../data/abstracts.csv"
SLEEP = 0.4

# ---------- Helpers ---------- (if problems with csv formatting)
def safe_read(path):
    try:
        return pd.read_csv(path, sep=",", quotechar='"', escapechar="\\", engine="python")
    except Exception:
        return pd.read_csv(path, on_bad_lines="skip")

# ---------- Load / resume ----------
df = safe_read(INPUT_FILE)

required = ["indice", "title", "abstract"]
for c in required:
    if c not in df.columns:
        raise ValueError(f"Column missing: {c}")

start = 0

# ---------- API helpers ----------
def crossref_doi(title):
    """Search DOI by title using CrossRef."""
    url = "https://api.crossref.org/works"
    params = {"query.title": title, "rows": 1}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        if not items:
            return None
        return items[0].get("DOI")
    except Exception:
        return None


def openalex_abstract(doi):
    """Fetch and reconstruct abstract text from OpenAlex."""
    try:
        url = f"https://api.openalex.org/works/doi:{doi}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        # Case 1: Plain abstract (rare)
        if "abstract" in data and data["abstract"]:
            return data["abstract"]

        # Case 2: Tokenized abstract_inverted_index
        inv = data.get("abstract_inverted_index")
        if not inv:
            return None

        # Rebuild text in proper order
        words = sorted(inv.items(), key=lambda kv: kv[1][0])
        return " ".join([w for w, _ in words])

    except Exception:
        return None

# ---------- Main loop ----------
for i in range(start, len(df)):
    title = str(df.at[i, "title"])
    if pd.notna(df.at[i, "abstract"]) and df.at[i, "abstract"].strip():
        continue

    print(f"\n{df.at[i, 'indice']} — {title}")

    # Step 1: Get DOI from CrossRef
    doi = crossref_doi(title)
    print("DOI:", doi)

    abstract = None
    if doi:
        abstract = openalex_abstract(doi)

    # Step 2: Write abstract if found
    if abstract:
        print("Abstract found")
        df.at[i, "abstract"] = abstract
    else:
        print("No abstract found")

    # Save progress incrementally
    df.to_csv(OUTPUT_FILE, index=False, quoting=csv.QUOTE_ALL, escapechar="\\")
    time.sleep(SLEEP)

print("\n Results saved to", OUTPUT_FILE)
