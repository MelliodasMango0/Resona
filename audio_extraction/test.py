import essentia.standard as es
import numpy as np
import os
import subprocess

# Define file paths
mp3_file = "/Users/melliodasmango0/Documents/Senior Year Spring/Resona/audio_extraction/rally_house_like_that.mp3"
wav_file = "/Users/melliodasmango0/Documents/Senior Year Spring/Resona/audio_extraction/temp_like_that.wav"

# Ensure file exists
if not os.path.isfile(mp3_file):
    raise FileNotFoundError(f"Error: File not found -> {mp3_file}")

# Convert MP3 to WAV for better compatibility
if mp3_file.endswith(".mp3"):
    print("Converting MP3 to WAV...")
    subprocess.run(["ffmpeg", "-y", "-i", mp3_file, wav_file], check=True)

# Extract features using MusicExtractor
features, _ = es.MusicExtractor(
    lowlevelStats=['mean', 'stdev'],
    rhythmStats=['mean', 'stdev'],
    tonalStats=['mean', 'stdev']
)(wav_file)

# Define the expected feature structure
expected_features = {
    "rhythm.bpm": 1,
    "lowlevel.spectral_centroid.mean": 1,
    "lowlevel.spectral_contrast.mean": 1,
    "lowlevel.mfcc.mean": 13,  # MFCC has 13 coefficients
}

# Extract features while ensuring fixed-size vectors
feature_values = []
for feature, size in expected_features.items():
    if feature in features.descriptorNames():  # Check if feature exists
        value = features[feature]
    else:
        value = np.full(size, np.nan)  # Use NaN if feature is missing
    
    if isinstance(value, np.ndarray):
        if len(value) >= size:
            value = value[:size]  # Truncate if too long
        else:
            value = np.pad(value, (0, size - len(value)), constant_values=np.nan)  # Pad if too short
    else:
        value = np.array([value])  # Convert single values to arrays
    feature_values.append(value)

# Final standardized feature vector
feature_vector = np.concatenate(feature_values)
print("Final Feature Vector Shape:", feature_vector.shape)
print("Feature Vector:", feature_vector)

# Cleanup temporary WAV file
if os.path.exists(wav_file):
    os.remove(wav_file)
    print("Temporary WAV file deleted.")
