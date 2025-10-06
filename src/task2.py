import requests
import pandas as pd
import random
import time
import xml.etree.ElementTree as ET

esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Number of relevant documents: we might need to change this since we cannot fetch all 1308 papers from the original set
N_RELEVANT = 1308 

# Our query searches for the negative set of the original one: since the topic is polyphenols, here we look for any article containing NOT polyphenol(s)
# I couldn't find info regarding whether the pubmed IR system handles stemming of the terms in the queries, so the query includes both the plural and singular
# (either in the title or abstract)
# We're also fetching 5000 papers but will only sample how many we need
params = {
    "db": "pubmed",
    "term": "(all[tiab]) NOT (polyphenol[title/abstract] OR polyphenols[title/abstract])",
    "retmode": "json",
    "retmax": 5000
}
response = requests.get(esearch_url, params=params)
esearch_data = response.json()

pmid_list = esearch_data.get("esearchresult", {}).get("idlist", [])
print(f"Found {len(pmid_list)} candidate non-relevant PMIDs.")

# Now we sample the same number of docs as relevant set
if len(pmid_list) < N_RELEVANT:
    raise ValueError("Not enough non-relevant docs retrieved!") # This is unlikely 
sampled_pmids = random.sample(pmid_list, N_RELEVANT)

# Now we fetch
results = []
i=0
for pmid in sampled_pmids:
    efetch_params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
        "rettype": "abstract"
    }
    fetch_resp = requests.get(efetch_url, params=efetch_params)
    fetch_resp.raise_for_status()
    
    root = ET.fromstring(fetch_resp.text)
    article = root.find(".//PubmedArticle")
    
    if article is not None:
        # Extract Title
        title_el = article.find(".//ArticleTitle")
        title = title_el.text if title_el is not None else None

        # Extract Abstract (concatenate parts if multiple sections)
        abstract_elems = article.findall(".//AbstractText")
        if abstract_elems:  # controlla che esista almeno un abstract
            abstract = " ".join([a.text for a in abstract_elems if a.text])
        else:
            abstract = None  # se non c’è, salviamo None
        
        results.append({
            "Title": title,
            "PMID": pmid,
            "Abstract": abstract
        })

    i = i+1
    print(i,"\n")
    time.sleep(0.4)  # avoid overloading NCBI servers

# We now save the non-relevant articles
df = pd.DataFrame(results)
df.to_excel("non_relevant_publications.xlsx", index=False)

print("done")

df1 = pd.read_excel("publications_with_all_abstracts.xlsx")
df2 = pd.read_excel("non_relevant_publications.xlsx")

combined_df = pd.concat([df1, df2], ignore_index=True)
combined_df.to_excel("all_publications.xlsx", index=False)
