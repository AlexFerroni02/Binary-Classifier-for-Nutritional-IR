# python
import requests
import pandas as pd
import random
import time
import xml.etree.ElementTree as ET
from pathlib import Path

esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

N_RELEVANT = 1308

params = {
    "db": "pubmed",
    "term": "(all[tiab]) NOT (polyphenol[title/abstract] OR polyphenols[title/abstract])",
    "retmode": "json",
    "retmax": 5000
}

resp = requests.get(esearch_url, params=params)
resp.raise_for_status()
esearch_data = resp.json()

pmid_list = esearch_data.get("esearchresult", {}).get("idlist", [])
print(f"Found {len(pmid_list)} candidate non-relevant PMIDs.")

if len(pmid_list) < N_RELEVANT:
    raise ValueError("Not enough non-relevant PMIDs retrieved to reach target of 1308 abstracts.")

# shuffle and iterate until we collect N_RELEVANT with non-empty abstract
random.shuffle(pmid_list)
results = []
processed = 0
kept = 0

for pmid in pmid_list:
    if kept >= N_RELEVANT:
        break

    efetch_params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
        "rettype": "abstract"
    }

    try:
        fetch_resp = requests.get(efetch_url, params=efetch_params, timeout=20)
        fetch_resp.raise_for_status()
    except Exception as e:
        print(f"Warning: failed to fetch PMID {pmid}: {e}")
        time.sleep(0.4)
        continue

    try:
        root = ET.fromstring(fetch_resp.text)
    except ET.ParseError:
        print(f"Warning: failed to parse XML for PMID {pmid}")
        time.sleep(0.4)
        continue

    article = root.find(".//PubmedArticle")
    if article is None:
        processed += 1
        time.sleep(0.4)
        continue

    title_el = article.find(".//ArticleTitle")
    title = title_el.text.strip() if (title_el is not None and title_el.text) else ""

    abstract_elems = article.findall(".//AbstractText")
    if abstract_elems:
        abstract_parts = [a.text.strip() for a in abstract_elems if a.text and a.text.strip()]
        abstract = " ".join(abstract_parts).strip()
    else:
        abstract = ""

    processed += 1
    if abstract:
        results.append({"Title": title, "PMID": pmid, "Abstract": abstract})
        kept += 1
        # stampa ogni volta che viene trovato un abstract valido
        t_snip = title.replace("\n", " ").strip()[:120]
        a_snip = abstract.replace("\n", " ").strip()[:120]
        print(f"Found {kept}/{N_RELEVANT} — PMID {pmid} — Title: {t_snip} — Abstract snippet: {a_snip}")

    if processed % 50 == 0 or kept % 100 == 0:
        print(f"Processed {processed} PMIDs, kept {kept} with non-empty abstract.")

    time.sleep(0.34)

print(f"Finished fetching: processed {processed} PMIDs, kept {kept} abstracts.")

if kept < N_RELEVANT:
    raise RuntimeError(f"Could not collect {N_RELEVANT} non-empty abstracts (collected {kept}). Try increasing retmax or running again.")

df_nr = pd.DataFrame(results[:N_RELEVANT])
out_nr_path = DATA_DIR / "non_relevant_publications.xlsx"
df_nr.to_excel(out_nr_path, index=False)
print(f"Saved {len(df_nr)} non-relevant publications with abstracts to `{out_nr_path}`.")

# --- Combine with existing publications, keeping only rows with non-empty abstracts ---
def find_abstract_col(df):
    for c in df.columns:
        if c.lower() == "abstract":
            return c
    return None

pubs_path = DATA_DIR / "publications_with_all_abstracts.xlsx"
if pubs_path.exists():
    df1 = pd.read_excel(pubs_path)
    col1 = find_abstract_col(df1)
    if col1 is None:
        print(f"Warning: `Abstract` column not found in `{pubs_path}`. The file will be ignored in the merge.")
        df1 = pd.DataFrame(columns=["Abstract"])
    else:
        df1 = df1.rename(columns={col1: "Abstract"})
else:
    print(f"Warning: `{pubs_path}` not found. Combining only fetched non-relevants.")
    df1 = pd.DataFrame(columns=["Abstract"])

# ensure our fetched file has consistent column name
col_nr = find_abstract_col(df_nr)
if col_nr and col_nr != "Abstract":
    df_nr = df_nr.rename(columns={col_nr: "Abstract"})

df1["Abstract"] = df1.get("Abstract", "").fillna("").astype(str)
df_nr["Abstract"] = df_nr.get("Abstract", "").fillna("").astype(str)

df1 = df1[df1["Abstract"].str.strip() != ""].copy()
df_nr = df_nr[df_nr["Abstract"].str.strip() != ""].copy()

combined_df = pd.concat([df1, df_nr], ignore_index=True)
combined_df = combined_df.reset_index(drop=True)

out_all_path = DATA_DIR / "all_publications.xlsx"
combined_df.to_excel(out_all_path, index=False)
print(f"Saved combined publications with abstracts to `{out_all_path}`. Total rows: {len(combined_df)}.")
