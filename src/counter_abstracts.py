import pandas as pd

df = pd.read_csv(
    "../data/abstracts.csv",
    quoting=1,             
    escapechar="\\",        
    on_bad_lines="skip",    # prevent crash if one row is malformed
    engine="python"         
)

df1 = pd.read_csv(
    "../data/abstracts_filled.csv",
    quoting=1,             
    escapechar="\\",        
    on_bad_lines="skip",    # prevent crash if one row is malformed
    engine="python"         
)


count_non_empty = df['abstract'].notna() & (df['abstract'].str.strip() != "")
count_non_empty = count_non_empty.sum()

count_non_empty1 = df1['abstract'].notna() & (df1['abstract'].str.strip() != "")
count_non_empty1 = count_non_empty1.sum()
1
print(f"Numero di righe con abstract: {count_non_empty}")
print(f"Numero di righe con abstract: {count_non_empty1}")

