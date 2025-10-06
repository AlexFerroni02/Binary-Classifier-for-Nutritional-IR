import pandas as pd

# Leggi il CSV
df = pd.read_csv("../data/abstracts.csv")

# Conta le righe in cui la colonna 'Abstract' non è vuota o NaN
count_non_empty = df['abstract'].notna() & (df['abstract'].str.strip() != "")
count_non_empty = count_non_empty.sum()

print(f"Numero di righe con abstract dopo scholarly prima di semantic scholar: {count_non_empty}")


# Leggi l'Excel
df = pd.read_excel("../data/publications_with_all_abstracts.xlsx")

# Conta le righe in cui la colonna 'Abstract' non è vuota o NaN
count_non_empty = df['abstract'].notna() & (df['abstract'].str.strip() != "")
count_non_empty = count_non_empty.sum()

print(f"Numero di righe con abstract dopo entrambi: {count_non_empty}")