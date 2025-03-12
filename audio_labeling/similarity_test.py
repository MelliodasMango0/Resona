import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# === PARAMETERS ===
INPUT_FILE = "song_features.json"  # JSON file with song vectors
OUTPUT_FILE = "training_label_matrix.csv"
SIMILARITY_THRESHOLD = 0.90  # Threshold for considering songs similar

# === LOAD FEATURE VECTORS ===
print("Loading song feature vectors...")

# Load JSON file
with open(INPUT_FILE, "r") as f:
    song_data = json.load(f)

# Extract song names and corresponding feature vectors
song_names = list(song_data.keys())
song_vectors = np.array(list(song_data.values()))  # Shape: (N, D)
num_songs = len(song_names)

# === COMPUTE COSINE SIMILARITY MATRIX ===
print("Computing cosine similarity matrix...")
cosine_sim_matrix = cosine_similarity(song_vectors)  # Shape: (N, N)

# === GENERATE TRAINING LABEL MATRIX ===
print("Generating training label matrix...")
label_matrix = np.zeros((num_songs, num_songs), dtype=int)  # Default: 0 (NS)

# Apply similarity threshold
label_matrix[cosine_sim_matrix >= SIMILARITY_THRESHOLD] = 1  # Mark similar (S)

# Ensure diagonal is 1 (a song is always similar to itself)
np.fill_diagonal(label_matrix, 1)

# Convert to DataFrame for easy viewing
label_matrix_df = pd.DataFrame(label_matrix, index=song_names, columns=song_names)

# === SAVE TO FILE ===
print("Saving label matrix to file...")
label_matrix_df.to_csv(OUTPUT_FILE)

print(f"Training label matrix saved as {OUTPUT_FILE}.")
