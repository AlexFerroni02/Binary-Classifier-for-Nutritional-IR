"""
import requests
import xml.etree.ElementTree as ET
import re
import time

def esearch(term):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": term, "retmode": "xml"}
    response = requests.get(url, params=params)
    return response.text

def try_queries(title, author=None, year=None, journal=None, page=None):
    # 1. Ricerca esatta col title
    queries = [f'"{title}"[Title]']



    # 4. Title + author + year (se disponibili)
    if author and year:
        queries.append(f'"{title}"[Title] OR ({author}[Author] AND {year}[Date - Publication])')



    # 5. Search generica
    queries.append(title)

    # Prova tutte le query
    for q in queries:
        xml_res = esearch(q)
        root = ET.fromstring(xml_res)
        ids = root.findall(".//Id")
        if ids:
            return ids[0].text  # Restituisce il primo PMID trovato

    return None

def fetch_abstract(pmid):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    response = requests.get(url, params=params)
    root = ET.fromstring(response.text)
    abstract_elems = root.findall(".//AbstractText")
    return "\n".join([a.text or "" for a in abstract_elems]) if abstract_elems else None

# Esempio di utilizzo per una singola riga
title = "Uptake and metabolism of epicatechin and its access to the brain after oral ingestion"
author = "Abd El Mohsen M.M., Kuhnle G., Rechner A.R., Schroeter H., Rose S., Jenner P., Rice-Evans C.A."
year = "2002"
journal = "Free Radic Biol Med"
page = "1693-702"
pmid = try_queries(title, author, year)
if pmid:
    print("PMID trovato:", pmid)
    abs_text = fetch_abstract(pmid)
    print("-- ABSTRACT --\n", abs_text)
else:
    print("Articolo non trovato su PubMed")

# Consigli:
# - Inserisci uno sleep time tra le richieste (0.34s minimo) per evitare limiti API
# - Adatta "author" e "year" solo se i dati sono disponibili dalle colonne dell'Excel
"""
from scholarly import scholarly
import json

def ricerca_articolo(titolo_completo, autori, anno):
    # Estrai il cognome del primo autore
    primo_autore = autori.split(',')[0].split('.')[0].strip()

    # Parole chiave dal titolo per migliorare la precisione
    parole_chiave = ["resveratrol", "Aragon", "wine"]

    print(f"Ricerca in corso per autore '{primo_autore}', anno {anno}...")

    # Costruisci query con autore e anno
    query = f"author:{primo_autore} year:{anno} {' '.join(parole_chiave)}"
    search_query = scholarly.search_pubs(query)

    try:
        # Ottieni il primo risultato
        risultato = next(search_query)

        # Ottieni il titolo trovato
        titolo_trovato = risultato['bib'].get('title', '')

        print("\nTITOLO CERCATO:")
        print(titolo_completo)
        print("\nTITOLO TROVATO:")
        print(titolo_trovato)

        # Verifica automatica se i titoli corrispondono
        titolo_cercato_norm = titolo_completo.lower().strip()
        titolo_trovato_norm = titolo_trovato.lower().strip()

        if titolo_cercato_norm == titolo_trovato_norm:
            print("\n✓ Titolo corrisponde perfettamente!")
            titoli_corrispondono = True
        elif titolo_cercato_norm in titolo_trovato_norm or titolo_trovato_norm in titolo_cercato_norm:
            print("\n? Titolo parzialmente corrispondente")
            titoli_corrispondono = True
        else:
            print("\n✗ Titolo non corrispondente")
            titoli_corrispondono = False

        # Procedi solo se i titoli corrispondono
        if titoli_corrispondono:
            # Stampa informazioni principali
            print("\nINFORMAZIONI TROVATE:")
            print(f"Titolo: {titolo_trovato}")
            print(f"Autori: {risultato['bib'].get('author', 'N/D')}")
            print(f"Anno: {risultato['bib'].get('pub_year', 'N/D')}")
            print(f"Venue: {risultato['bib'].get('venue', 'N/D')}")

            # Controlla e visualizza l'abstract
            abstract = risultato['bib'].get('abstract')
            if abstract:
                print("\nABSTRACT:")
                print(abstract)
            else:
                print("\nNessun abstract disponibile.")

            return risultato
        else:
            print("Ricerca terminata: i titoli non corrispondono.")
            return None

    except StopIteration:
        print("Nessun risultato trovato con i criteri specificati.")
        return None
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")
        return None

# Parametri di ricerca
titolo = "Preliminary study of resveratrol content in Aragon red and rose wines"
autori = "Abril M., Negueruela A.I., Perez C., Juan T., Estopanan G."
anno = "2005"

# Esegui la ricerca
ricerca_articolo(titolo, autori, anno)

