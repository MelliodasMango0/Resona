import librosa
import numpy as np
import os
import json
from sklearn.preprocessing import StandardScaler
# Directory containing songs
songs_dir = "music/rap"
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

        feature_vector = mfccs.flatten()
        #==== NEW ADDITION: FEATURE STANDARDIZATION =======
        scaler = StandardScaler()
        feature_vector = np.array(feature_vector)
        feature_vector_standardized = scaler.fit_transform(feature_vector.reshape(-1, 1)).flatten()
        feature_vector_standardized = feature_vector_standardized.tolist()

        # Store in dictionary
        song_features[filename] = feature_vector_standardized

        print(f"Processed {filename}")

# Save updated features to a file
with open(output_file, "w") as f:
    json.dump(song_features, f, indent=4)

print(f"Feature extraction complete. Data saved in {output_file}.")
