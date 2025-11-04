import pandas as pd
from scholarly import scholarly
import time

input_file = "../data/abstracts.csv"
output_file = "../data/abstracts.csv"

df = pd.read_csv(input_file)

if "abstract" not in df.columns:
    df["abstract"] = ""

def get_abstract(title):
    try:
        q = scholarly.search_pubs(title)
        r = next(q)
        return r["bib"].get("abstract", None)
    except:
        return None

for i, row in df.iterrows():
    title = row["title"]

    if pd.notna(row["abstract"]) and row["abstract"].strip() != "":
        continue

    print(f"Searching: {title}")

    abs_text = get_abstract(title)

    if abs_text:
        df.at[i, "abstract"] = abs_text
        print(" -> found")
    else:
        df.at[i, "abstract"] = ""
        print(" -> not found")

    time.sleep(5)  # avoid rate-limiting

df.to_csv(output_file, index=False)
print("Done:", output_file)

