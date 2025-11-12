# python
import pandas as pd
from sklearn.model_selection import train_test_split
import sys
import numpy as np

MASTER_FILE = "../data/master_dataset_pulito.csv"
BENCHMARK_FILE = "../data/benchmark.xlsx"
RANDOM_STATE = 42

TEST_RATIO = 0.15
VAL_RATIO = 0.15
TRAIN_RATIO = 1.0 - TEST_RATIO - VAL_RATIO

try:
    df_master = pd.read_csv(MASTER_FILE)
except FileNotFoundError:
    print(f"ERROR: File {MASTER_FILE} not found.")
    sys.exit(1)

try:
    df_benchmark = pd.read_excel(BENCHMARK_FILE)
except FileNotFoundError:
    print(f"ERROR: File {BENCHMARK_FILE} not found.")
    sys.exit(1)
except ImportError:
    print("ERROR: To read .xlsx files the 'openpyxl' library is required.")
    print("Run: pip install openpyxl")
    sys.exit(1)

if 'abstract' not in df_benchmark.columns:
    print(f"ERROR: The column 'abstract' was not found in {BENCHMARK_FILE}.")
    sys.exit(1)

benchmark_texts = set(df_benchmark['abstract'].dropna())

is_benchmark_row = (df_master['label'] == 1) & (df_master['text'].isin(benchmark_texts))

df_forced_test = df_master[is_benchmark_row].copy()
df_splittable = df_master[~is_benchmark_row].copy()

if len(df_forced_test) == 0:
    print("WARNING: No relevant (label 1) benchmark documents were found in the master dataset.")
elif len(df_forced_test) > len(benchmark_texts):
    print("WARNING: Duplicates found in the master dataset that match the benchmark.")



total_docs = len(df_master)
target_val_size = int(total_docs * VAL_RATIO)
target_test_size = int(total_docs * TEST_RATIO)

num_val_needed = target_val_size
num_test_needed = max(0, target_test_size - len(df_forced_test))

num_train_needed = len(df_splittable) - num_val_needed - num_test_needed

if num_train_needed <= 0:
    print(f"ERROR: Insufficient data. With {len(df_splittable)} splittable documents it is not possible to create a train set")
    print(f"after allocating {num_val_needed} for validation and {num_test_needed} for test.")
    sys.exit(1)

val_test_pool_size = num_val_needed + num_test_needed

if len(df_splittable) == 0:
    val_test_ratio = 0
else:
    val_test_ratio = val_test_pool_size / len(df_splittable)

if val_test_ratio >= 1.0:
    df_train = pd.DataFrame(columns=df_master.columns)
    df_val_test_pool = df_splittable
else:
    df_train, df_val_test_pool = train_test_split(
        df_splittable,
        test_size=val_test_ratio,
        random_state=RANDOM_STATE,
        stratify=df_splittable['label']
    )

if (num_val_needed + num_test_needed) > 0 and len(df_val_test_pool) > 0:
    test_needed_ratio = num_test_needed / (num_val_needed + num_test_needed)

    if test_needed_ratio == 0:
        df_val = df_val_test_pool
        df_test_needed = pd.DataFrame(columns=df_master.columns)
    elif test_needed_ratio == 1:
        df_val = pd.DataFrame(columns=df_master.columns)
        df_test_needed = df_val_test_pool
    elif len(df_val_test_pool) < 2 or len(np.unique(df_val_test_pool['label'])) < 2:
        df_val, df_test_needed = train_test_split(
            df_val_test_pool,
            test_size=test_needed_ratio,
            random_state=RANDOM_STATE
        )
    else:
        df_val, df_test_needed = train_test_split(
            df_val_test_pool,
            test_size=test_needed_ratio,
            random_state=RANDOM_STATE,
            stratify=df_val_test_pool['label']
        )
else:
    df_val = pd.DataFrame(columns=df_master.columns)
    df_test_needed = pd.DataFrame(columns=df_master.columns)

df_test_final = pd.concat([df_forced_test, df_test_needed], ignore_index=True)
df_train_final = df_train
df_val_final = df_val

df_train_final.to_csv("train_set.csv", index=False)
df_val_final.to_csv("validation_set.csv", index=False)
df_test_final.to_csv("test_set.csv", index=False)



train_texts = set(df_train_final['text'])
val_texts = set(df_val_final['text'])

benchmark_violations = 0
for text in benchmark_texts:
    if text in train_texts or text in val_texts:
        benchmark_violations += 1

if benchmark_violations == 0:
    print("\nSAFETY CHECK: OK!")
    print("No benchmark document is present in `train_set.csv` or `validation_set.csv`.")
else:
    print("\nSAFETY CHECK: FAILED!")
    print(f"Found {benchmark_violations} benchmark violations in train/validation.")
