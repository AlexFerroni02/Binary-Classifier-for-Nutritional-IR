import pandas as pd
import requests
import time
import re
from difflib import get_close_matches
 

file_path = "publications.xlsx"
df = pd.read_excel(file_path)

titles = df['title'].tolist()

# URLs for search and fetch
esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

results = []
pmid_vector = []

for title in titles:
    # We remove the symbols so as to be more elastic
    clean_title = re.sub(r'[^\w\s]', '', title)
    
    # ESearch
    esearch_params = {
        "db": "pubmed",
        "term": f"{clean_title}[Title/Abstract]",  # search in title OR abstract to be more flexible
        "retmode": "json"
    }
    esearch_response = requests.get(esearch_url, params=esearch_params)
    esearch_data = esearch_response.json()
    
    pmid_list = esearch_data.get("esearchresult", {}).get("idlist", [])
    
    if not pmid_list:
        print(f"No PMID found for: {title}")
        results.append({"Title": title, "PMID": None, "Abstract": None})
        pmid_vector.append(0)
        continue
    
    # Get titles of the first 5 articles to check them
    pmid = pmid_list[0]
    efetch_params = {
        "db": "pubmed",
        "id": ",".join(pmid_list[:5]),  
        "retmode": "xml"
    }
    efetch_response = requests.get(efetch_url, params=efetch_params)
    xml_text = efetch_response.text
    
    # Extract titles with parsing
    article_titles = re.findall(r'<ArticleTitle>(.*?)</ArticleTitle>', xml_text)
    
    # Find closest match
    best_match = get_close_matches(clean_title, article_titles, n=1)
    if best_match:
        # Extract PMID of best match
        idx = article_titles.index(best_match[0])
        pmid = pmid_list[idx]
    else:
        best_match = [title]
    
    # EFetch
    efetch_params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "text",
        "rettype": "abstract"
    }
    efetch_response = requests.get(efetch_url, params=efetch_params)
    abstract_text = efetch_response.text.strip()
    
    results.append({"Title": title, "PMID": pmid, "Abstract": abstract_text})
    pmid_vector.append(pmid)

    print(f"PMID {pmid} for: {title}")
    
    # The database doesnt like more than 3 requests/s
    time.sleep(0.4)

# Output
output_df = pd.DataFrame(results)
output_df.to_excel("publications_with_abstracts.xlsx", index=False)
print("Done, file saved as 'publications_with_abstracts.xlsx'.")
