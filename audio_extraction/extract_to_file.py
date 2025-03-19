import librosa
import numpy as np
import os
import json

# Directory containing songs
songs_dir = "music/rock"
output_file = "song_features.json"

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
        
        # Extract features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)

        # Compute mean and variance for MFCCs
        mfccs_mean = np.mean(mfccs, axis=1).tolist()
        mfccs_var = np.var(mfccs, axis=1).tolist()

        # Compute mean values for other features
        spectral_centroid_mean = np.mean(spectral_centroid).tolist()
        spectral_bandwidth_mean = np.mean(spectral_bandwidth).tolist()
        zcr_mean = np.mean(zcr).tolist()
        chroma_mean = np.mean(chroma, axis=1).tolist()

        # Concatenate all features into a single vector
        feature_vector = (
            mfccs_mean + mfccs_var +  # MFCCs (13 + 13)
            [spectral_centroid_mean, spectral_bandwidth_mean, zcr_mean] +  # Spectral (3)
            chroma_mean  # Chroma (12)
        )

        # Store in dictionary
        song_features[filename] = feature_vector

        print(f"Processed {filename}")

# Save updated features to a file
with open(output_file, "w") as f:
    json.dump(song_features, f, indent=4)

print(f"Feature extraction complete. Data saved in {output_file}.")
