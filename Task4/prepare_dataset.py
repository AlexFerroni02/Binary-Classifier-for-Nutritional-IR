python
import pandas as pd
import numpy as np
import sys

try:
    df_relevant_all = pd.read_csv("../data/abstracts_filled.csv")
    print(f"Loaded {len(df_relevant_all)} RELEVANT documents (before filtering).")
except FileNotFoundError:
    print("ERROR: File `../data/abstracts_filled.csv` not found.")
    sys.exit(1)

for col in ['title', 'abstract']:
    if col not in df_relevant_all.columns:
        print(f"ERROR: Column `{col}` not found in `../data/abstracts_filled.csv`.")
        sys.exit(1)

df_relevant_all['abstract'] = df_relevant_all['abstract'].fillna('').astype(str)
df_relevant_all['title'] = df_relevant_all['title'].fillna('').astype(str)
df_relevant_all['abstract_stripped'] = df_relevant_all['abstract'].str.strip()
df_relevant_all['title_stripped'] = df_relevant_all['title'].str.strip()

df_relevant = df_relevant_all[df_relevant_all['abstract_stripped'] != ''].copy()
df_relevant = df_relevant[df_relevant['title_stripped'] != df_relevant['abstract_stripped']].copy()

N_DATASET_SIZE = len(df_relevant)
print(f"Relevant documents kept (with valid abstract and different from title): {N_DATASET_SIZE}")

if N_DATASET_SIZE == 0:
    print("ERROR: No relevant documents available after filters.")
    sys.exit(1)

try:
    df_non_relevant_all = pd.read_excel("../data/non_relevant_publications.xlsx")
    print(f"Loaded {len(df_non_relevant_all)} NON-RELEVANT documents (before sampling).")
except FileNotFoundError:
    print("ERROR: File `../data/non_relevant_publications.xlsx` not found.")
    sys.exit(1)

if len(df_non_relevant_all) < N_DATASET_SIZE:
    print("ERROR: Not enough NON-RELEVANT documents to balance the dataset.")
    sys.exit(1)

df_non_relevant = df_non_relevant_all.sample(
    n=N_DATASET_SIZE,
    random_state=42
).copy()

print(f"NON-RELEVANT documents sampled: {len(df_non_relevant)}")

df_relevant['label'] = 1
df_non_relevant['label'] = 0

df_relevant['text'] = df_relevant['abstract'].fillna('')
df_non_relevant['text'] = df_non_relevant['Abstract'].fillna('')

df_relevant_final = df_relevant[['text', 'label']]
df_non_relevant_final = df_non_relevant[['text', 'label']]

df_master = pd.concat([df_relevant_final, df_non_relevant_final], ignore_index=True)
df_master = df_master.sample(frac=1, random_state=42).reset_index(drop=True)

df_master.to_csv("../data/master_dataset_pulito.csv", index=False)

print(f"\nDataset `../data/master_dataset_pulito.csv` created successfully.")
print(f"Total documents: {len(df_master)}")
print(f"Class distribution (now balanced):\n{df_master['label'].value_counts()}")

