import pandas as pd
import requests
import time
import xml.etree.ElementTree as ET
import difflib
import os

def format_first_author(authors):
    if not isinstance(authors, str) or not authors.strip():
        return None
    first_author = authors.split(",")[0].strip()
    first_author_formatted = first_author.replace('.', '').replace('  ', ' ')
    return first_author_formatted

def esearch(term):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": term, "retmode": "xml"}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.text.startswith('<?xml'):
        return response.text
    return None

def fetch_title_from_pmid(pmid):
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    response = requests.get(efetch_url, params=params)
    if response.status_code != 200:
        return None
    try:
        root = ET.fromstring(response.text)
        title = root.findtext(".//ArticleTitle")
        return title
    except ET.ParseError:
        return None

def is_title_similar(original_title, fetched_title, threshold=0.9):
    if not (original_title and fetched_title):
        return False
    ratio = difflib.SequenceMatcher(None, original_title.lower(), fetched_title.lower()).ratio()
    return ratio >= threshold

def try_pubmed_queries(title, authors=None, year=None):
    queries = [f'"{title}"[Title]']
    if authors and year:
        queries.append(f'"{title}"[Title] OR ({authors}[Author] AND {year}[Date - Publication])')
    queries.append(title)

    for q in queries:
        xml_text = esearch(q)
        if xml_text:
            try:
                root = ET.fromstring(xml_text)
                id_nodes = root.findall(".//Id")
                for pmid_node in id_nodes:
                    pmid = pmid_node.text
                    fetched_title = fetch_title_from_pmid(pmid)
                    if is_title_similar(title, fetched_title):
                        return pmid
            except ET.ParseError:
                continue
    return None

def get_abstract_xml(pmid):
    efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }
    response = requests.get(efetch_url, params=params)
    return response.text if response.status_code == 200 and response.text.startswith('<?xml') else None

def extract_abstract_from_xml(xml_text):
    if not xml_text:
        return None
    try:
        root = ET.fromstring(xml_text)
        abstract = root.findtext(".//AbstractText")
        return abstract.strip() if abstract else None
    except ET.ParseError:
        return None

def main():
    input_file = "../data/publications.xlsx"
    output_file = "../data/abstracts.csv"
    df = pd.read_excel(input_file)

    # Carica indici già processati se il file esiste
    processed_indices = set()
    if os.path.exists(output_file):
        try:
            df_existing = pd.read_csv(output_file)
            processed_indices = set(df_existing['indice'])
            print(f"Trovati {len(processed_indices)} articoli già processati.")
        except Exception:
            pass

    results_batch = []
    save_interval = 100

    for idx, row in df.iterrows():
        if idx in processed_indices:
            continue

        title = row.get("title", "").strip()
        authors = format_first_author(row.get("authors", ""))
        year = str(row.get("year_of_publication", "")).strip()

        pmid = try_pubmed_queries(title, authors, year)
        abstract = None
        if pmid:
            abstract_xml = get_abstract_xml(pmid)
            abstract = extract_abstract_from_xml(abstract_xml)

        print(f"Iterazione {idx}")

        results_batch.append({
            "title": title,
            "pmid": pmid if pmid else "NA",
            "abstract": abstract if abstract else "NA",
            "indice": idx
        })
        time.sleep(0.4)

        # Salva ogni 100
        if len(results_batch) >= save_interval:
            print(f"Salvo {len(results_batch)} risultati su CSV...")
            header = not os.path.exists(output_file)
            pd.DataFrame(results_batch).to_csv(output_file, mode='a', header=header, index=False)
            results_batch = []

    # Salva gli ultimi risultati rimasti
    if results_batch:
        print(f"Salvo ultimi {len(results_batch)} risultati su CSV...")
        header = not os.path.exists(output_file)
        pd.DataFrame(results_batch).to_csv(output_file, mode='a', header=header, index=False)

    print("Processo completato.")

if __name__ == "__main__":
    main()

