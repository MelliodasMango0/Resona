import os
import random
import itertools
import csv
from collections import defaultdict

# Set random seed for reproducibility
random.seed(42)

# Define paths
DATASET_DIR = r"C:\Users\Joe\Documents\GitHub\Resona\GTZAN_model\Data\images_original"
TRAIN_CSV = "train_pairs.csv"
VAL_CSV = "val_pairs.csv"

# Number of validation samples per genre
VAL_SAMPLES_PER_GENRE = 10

# Initialize dictionaries to hold training and validation data
train_data = defaultdict(list)
val_data = defaultdict(list)

# Step 1: Split each genre into training and validation sets
for genre in os.listdir(DATASET_DIR):
    genre_path = os.path.join(DATASET_DIR, genre)
    if not os.path.isdir(genre_path):
        continue
    images = [os.path.join(genre_path, img) for img in os.listdir(genre_path) if img.endswith(".png")]
    images.sort()  # Ensure consistent ordering
    val_images = images[:VAL_SAMPLES_PER_GENRE]
    train_images = images[VAL_SAMPLES_PER_GENRE:]
    train_data[genre] = train_images
    val_data[genre] = val_images

# Helper function to generate positive pairs
def generate_positive_pairs(data_dict):
    pairs = []
    for genre, images in data_dict.items():
        # Generate all unique pairs within the genre
        genre_pairs = list(itertools.combinations(images, 2))
        pairs.extend([(img1, img2, 1) for img1, img2 in genre_pairs])
    return pairs

# Helper function to generate negative pairs
def generate_negative_pairs(data_dict, num_pairs):
    pairs = set()
    genres = list(data_dict.keys())
    while len(pairs) < num_pairs:
        genre1, genre2 = random.sample(genres, 2)
        img1 = random.choice(data_dict[genre1])
        img2 = random.choice(data_dict[genre2])
        pair = tuple(sorted([img1, img2]))
        pairs.add(pair)
    return [(img1, img2, 0) for img1, img2 in pairs]

# Step 2: Generate training pairs
train_positive_pairs = generate_positive_pairs(train_data)
train_negative_pairs = generate_negative_pairs(train_data, len(train_positive_pairs))
train_pairs = train_positive_pairs + train_negative_pairs
random.shuffle(train_pairs)

# Step 3: Generate validation pairs
val_positive_pairs = generate_positive_pairs(val_data)
val_negative_pairs = generate_negative_pairs(val_data, len(val_positive_pairs))
val_pairs = val_positive_pairs + val_negative_pairs
random.shuffle(val_pairs)

# Step 4: Save pairs to CSV files
def save_pairs_to_csv(pairs, filename):
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["image1", "image2", "label"])
        for img1, img2, label in pairs:
            writer.writerow([img1, img2, label])

save_pairs_to_csv(train_pairs, TRAIN_CSV)
save_pairs_to_csv(val_pairs, VAL_CSV)

print(f"Training pairs saved to {TRAIN_CSV}")
print(f"Validation pairs saved to {VAL_CSV}")
