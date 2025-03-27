import librosa
import numpy as np
import os
import json
from sklearn.preprocessing import StandardScaler

# Directory containing songs
songs_dir = "music/rock"
output_file = "song_features_ext.json"

# Load existing features if the file exists
if os.path.exists(output_file):
    with open(output_file, "r") as f:
        try:
            song_features = json.load(f)
        except json.JSONDecodeError:
            song_features = {}  # Handle case where file is empty or corrupted
else:
    song_features = {}

# Process each song in the directory
for filename in os.listdir(songs_dir):
    if filename.endswith(".mp3") or filename.endswith(".wav"):  # Ensure it's an audio file
        if filename in song_features:
            print(f"Skipping {filename} (already processed)")
            continue  # Skip if already processed

        song_path = os.path.join(songs_dir, filename)
        
        # Load the song
        y, sr = librosa.load(song_path, sr=None)
        
        # Extract MFCCs (13 coefficients for each frame)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

        # Standardize MFCCs
        scaler = StandardScaler()
        mfccs_standardized = scaler.fit_transform(mfccs.T).T  # Transpose so that scaling is per feature

        # Store the MFCC matrix for the song
        song_features[filename] = mfccs_standardized.tolist()  # Storing as a 2D list

        print(f"Processed {filename}")

# Save updated features to a file
with open(output_file, "w") as f:
    json.dump(song_features, f, indent=4)

print(f"Feature extraction complete. Data saved in {output_file}.")
