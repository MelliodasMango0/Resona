import random
from sklearn.model_selection import train_test_split

# === PARAMETERS ===
DATASET_FILE = "dataset.txt"
TRAIN_FILE = "train.txt"
TEST_FILE = "test.txt"
TEST_SIZE = 0.3  # 30% test split

# === LOAD DATASET ===
print("Loading dataset...")
with open(DATASET_FILE, "r", encoding="utf-8") as f:
    dataset = [line.strip() for line in f.readlines()]

# === SEPARATE POSITIVE & NEGATIVE PAIRS ===
positive_pairs = [line for line in dataset if line.endswith(", 1")]
negative_pairs = [line for line in dataset if line.endswith(", 0")]

# === ENSURE STRATIFIED SPLIT ===
print("Splitting dataset in a stratified manner...")

# Split positive and negative pairs separately
train_pos, test_pos = train_test_split(positive_pairs, test_size=TEST_SIZE, random_state=42)
train_neg, test_neg = train_test_split(negative_pairs, test_size=TEST_SIZE, random_state=42)

# Combine and shuffle
train_data = train_pos + train_neg
test_data = test_pos + test_neg

random.shuffle(train_data)  # Shuffle to avoid bias
random.shuffle(test_data)

# === SAVE TRAIN & TEST FILES ===
print(f"Saving train set to {TRAIN_FILE} and test set to {TEST_FILE}...")
with open(TRAIN_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(train_data))

with open(TEST_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(test_data))

print(f"Train-Test Split Complete!\nTrain Size: {len(train_data)}, Test Size: {len(test_data)}")
