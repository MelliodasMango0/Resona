import os
import random

# === PARAMETERS ===
MUSIC_DIR = "music/"  # Directory where music is stored with subdirectories as genres
OUTPUT_FILE = "dataset.txt"
POSITIVE_PAIRS = 500  # Number of similar pairs (same genre)
NEGATIVE_PAIRS = 500  # Number of dissimilar pairs (different genre)

# === SCAN MUSIC DIRECTORY ===
print("Scanning music directory...")
genre_to_songs = {}  # Dictionary to store songs per genre

# Walk through all subdirectories (genres)
for genre in os.listdir(MUSIC_DIR):
    genre_path = os.path.join(MUSIC_DIR, genre)
    if os.path.isdir(genre_path):  # Ensure it's a folder
        songs = [f for f in os.listdir(genre_path) if f.endswith(".mp3")]
        genre_to_songs[genre] = songs

# === GENERATE POSITIVE PAIRS (Same Genre) ===
print("Generating positive pairs...")
positive_pairs = []
for genre, songs in genre_to_songs.items():
    if len(songs) < 2:
        continue  # Skip genres with fewer than 2 songs

    # Randomly generate positive pairs
    pairs = set()
    while len(pairs) < POSITIVE_PAIRS // len(genre_to_songs):  # Balance across genres
        s1, s2 = random.sample(songs, 2)
        pairs.add((s1, s2))

    # Format and store pairs
    positive_pairs.extend([f'"{s1}", "{s2}", 1' for s1, s2 in pairs])

# === GENERATE NEGATIVE PAIRS (Different Genre) ===
print("Generating negative pairs...")
negative_pairs = []
all_genres = list(genre_to_songs.keys())

while len(negative_pairs) < NEGATIVE_PAIRS:
    # Pick two different genres
    genre1, genre2 = random.sample(all_genres, 2)
    if not genre_to_songs[genre1] or not genre_to_songs[genre2]:
        continue

    # Pick one song from each genre
    s1 = random.choice(genre_to_songs[genre1])
    s2 = random.choice(genre_to_songs[genre2])

    negative_pairs.append(f'"{s1}", "{s2}", 0')

# === WRITE TO FILE ===
print(f"Saving dataset with {len(positive_pairs)} positive and {len(negative_pairs)} negative pairs...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(positive_pairs + negative_pairs))

print(f"Dataset saved as {OUTPUT_FILE}.")
