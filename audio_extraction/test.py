import essentia.standard as es
import numpy as np
import pickle

# Load the MP3 file
audio = es.MonoLoader(filename="RALLY HOUSE — UNDERGROUND ⧸⧸ nuphory x THIRST [501Ck8eXpvs].mp3")()

# Extract Features
mfcc_extractor = es.MFCC()
mfccs, _ = mfcc_extractor(audio)

spectral_centroid = es.Centroid()(audio)
spectral_bandwidth = es.SpectralBandwidth()(audio)
zcr = es.ZeroCrossingRate()(audio)
bpm, _ = es.RhythmExtractor2013(method="multifeature")(audio)

# Aggregate Features
mfcc_mean = np.mean(mfccs, axis=1)
mfcc_var = np.var(mfccs, axis=1)

# Final Feature Vector
feature_vector = np.concatenate([
    mfcc_mean, mfcc_var,
    [spectral_centroid, spectral_bandwidth, zcr],
    [bpm]
])

# Save Feature Vector
with open("song_features.pkl", "wb") as f:
    pickle.dump(feature_vector, f)

print("Feature Vector Created:", feature_vector.shape)
