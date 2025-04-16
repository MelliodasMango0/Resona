import os
import random
from itertools import combinations

# === PARAMETERS ===
MUSIC_DIR = "music/"  # Base directory with genre subfolders
OUTPUT_FILE = "dataset.txt"

# === COLLECT SONGS AND GENRES ===
print("Collecting songs and genres...")
song_to_genre = {}
for genre in os.listdir(MUSIC_DIR):
    genre_path = os.path.join(MUSIC_DIR, genre)
    if os.path.isdir(genre_path):
        for song in os.listdir(genre_path):
            if song.endswith(".mp3") or song.endswith('.wav'):
                full_path = os.path.join(genre_path, song)
                song_to_genre[song] = genre

songs = list(song_to_genre.keys())
print(f"Found {len(songs)} unique songs.")

# === GENERATE ALL UNIQUE UNORDERED PAIRS ===
print("Generating all unique song pairs...")
all_pairs = list(combinations(songs, 2))  # Each pair: (song1, song2)

# === LABEL PAIRS ===
positive_pairs = []
negative_pairs = []

for s1, s2 in all_pairs:
    genre1 = song_to_genre[s1]
    genre2 = song_to_genre[s2]
    label = 1 if genre1 == genre2 else 0
    formatted_pair = f'"{s1}", "{s2}", {label}'

    if label == 1:
        positive_pairs.append(formatted_pair)
    else:
        negative_pairs.append(formatted_pair)

# === BALANCE THE DATASET ===
num_pairs = min(len(positive_pairs), len(negative_pairs))
print(f"Balancing dataset to {num_pairs} positive and {num_pairs} negative pairs.")

selected_positive = random.sample(positive_pairs, num_pairs)
selected_negative = random.sample(negative_pairs, num_pairs)

final_dataset = selected_positive + selected_negative
random.shuffle(final_dataset)

# === WRITE TO FILE ===
print(f"Saving {len(final_dataset)} total pairs to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(final_dataset))

print("✅ Dataset generation complete.")

