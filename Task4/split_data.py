# python
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

try:
    df = pd.read_csv("../data/master_dataset_pulito.csv")
except FileNotFoundError:
    print("ERROR: `../data/master_dataset_pulito.csv` not found.")
    print("Run `prepare_dataset.py` first.")
    sys.exit(1)

TEST_SIZE = 0.15
VAL_SIZE = 0.15

X = df['text']
y = df['label']

X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=42, stratify=y
)

val_proportion = VAL_SIZE / (1.0 - TEST_SIZE)

X_train, X_val, y_train, y_val = train_test_split(
    X_train_val, y_train_val, test_size=val_proportion, random_state=42, stratify=y_train_val
)

train_df = pd.DataFrame({'text': X_train, 'label': y_train})
val_df = pd.DataFrame({'text': X_val, 'label': y_val})
test_df = pd.DataFrame({'text': X_test, 'label': y_test})

train_df.to_csv("train_set.csv", index=False)
val_df.to_csv("validation_set.csv", index=False)
test_df.to_csv("test_set.csv", index=False)

print("Data split completed.")
print(f"Training documents:   {len(train_df)}")
print(f"Validation documents: {len(val_df)}")
print(f"Testing documents:    {len(test_df)}")
