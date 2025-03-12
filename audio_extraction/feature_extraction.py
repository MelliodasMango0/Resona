import librosa
import numpy as np

# Load an MP3 or WAV file
y, sr = librosa.load("songs/song.mp3", sr=None)

# Extract MFCCs (Mel-Frequency Cepstral Coefficients)
mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # Shape: (13, Time Frames)

# Extract Spectral Features
spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)  # (1, Time Frames)
spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)  # (1, Time Frames)
zcr = librosa.feature.zero_crossing_rate(y)  # (1, Time Frames)

# Extract Chroma Features
chroma = librosa.feature.chroma_stft(y=y, sr=sr)  # (12, Time Frames)

# Compute Mean and Variance for each feature across time
mfccs_mean = np.mean(mfccs, axis=1)
mfccs_var = np.var(mfccs, axis=1)

spectral_centroid_mean = np.mean(spectral_centroid)
spectral_bandwidth_mean = np.mean(spectral_bandwidth)
zcr_mean = np.mean(zcr)

chroma_mean = np.mean(chroma, axis=1)

# Concatenate all features into a single feature vector
feature_vector = np.concatenate([
    mfccs_mean, mfccs_var,  # MFCCs (13 + 13)
    [spectral_centroid_mean, spectral_bandwidth_mean, zcr_mean],  # Spectral Features (3)
    chroma_mean  # Chroma (12)
])

print("Feature Vector Shape:", feature_vector.shape)  # Example: (41,)

np.set_printoptions(threshold=np.inf)  # Ensures full array is printed
print("Feature Vector:", feature_vector)
