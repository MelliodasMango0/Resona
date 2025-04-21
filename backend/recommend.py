import torch
import torch.nn.functional as F
import json
import os
import numpy as np
import librosa
from sklearn.preprocessing import StandardScaler
from CNN_Classification import SiameseNet  # Replace with actual import if in different file


# === SETTINGS ===
MODEL_PATH = "siamese_model.pth"
FEATURES_PATH = "song_features_ext.json"
TOP_K = 10

# === LOAD MODEL ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SiameseNet(input_shape=(1, 13, 100)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

# === LOAD FEATURE DATABASE ===
with open(FEATURES_PATH, "r", encoding="utf-8") as f:
    song_features = json.load(f)

song_names = list(song_features.keys())

# === PAD MFCCs to uniform time dimension ===
def pad_tensor(tensor, length):
    if tensor.shape[2] >= length:
        return tensor[:, :, :length]
    pad_amt = length - tensor.shape[2]
    return F.pad(tensor, (0, pad_amt))

# === Takes file path and return features of the song ===
def extract_features_from_file(filepath):
    y, sr = librosa.load(filepath, sr=None)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    scaler = StandardScaler()
    mfccs_standardized = scaler.fit_transform(mfccs.T).T  # [13, T]
    return mfccs_standardized

# === MAIN LOOP ===
while True:
    query_path = input("\n🎧 Enter path to your song file (or 'exit'): ").strip()
    if query_path.lower() == "exit":
        break
    if not os.path.isfile(query_path):
        print("❌ File not found. Try again.")
        continue

    try:
        query_features = extract_features_from_file(query_path)
    except Exception as e:
        print(f"❌ Failed to extract features: {e}")
        continue

    x1_vec = torch.tensor(query_features, dtype=torch.float32).unsqueeze(0).unsqueeze(0)  # [1, 1, 13, T1]

    similarities = []
    for candidate in song_names:
        x2_vec = torch.tensor(song_features[candidate], dtype=torch.float32).unsqueeze(0).unsqueeze(0)  # [1, 1, 13, T2]

        # Pad both to same time dimension
        max_len = max(x1_vec.shape[3], x2_vec.shape[3])
        x1_padded = pad_tensor(x1_vec, max_len).to(device)
        x2_padded = pad_tensor(x2_vec, max_len).to(device)

        with torch.no_grad():
            score = model(x1_padded, x2_padded).item()
            similarity = torch.sigmoid(torch.tensor(score)).item()
            similarities.append((candidate, similarity))

    # === Recommend Top K ===
    top_recommendations = sorted(similarities, key=lambda x: x[1], reverse=True)[:TOP_K]

    print(f"\n🎵 Top {TOP_K} songs similar to your uploaded file:")
    for rank, (name, sim) in enumerate(top_recommendations, 1):
        print(f"{rank:2d}. {name} — Similarity: {sim:.4f}")

