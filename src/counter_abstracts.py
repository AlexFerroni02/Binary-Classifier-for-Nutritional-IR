import pandas as pd

df = pd.read_csv(
    "../data/abstracts_filled.csv",
    quoting=1,             
    escapechar="\\",        
    on_bad_lines="skip",    # prevent crash if one row is malformed
    engine="python"         
)


count_non_empty = df['abstract'].notna() & (df['abstract'].str.strip() != "")
count_non_empty = count_non_empty.sum()

print(f"Numero di righe con abstract: {count_non_empty}")

