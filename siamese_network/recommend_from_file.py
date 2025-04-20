# recommend_from_file.py
import sys
import json
import librosa
import os
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn.functional as F
from CNN_Classification import SiameseNet

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SiameseNet(input_shape=(1, 13, 100)).to(device)
model.load_state_dict(torch.load("siamese_model.pth", map_location=device))
model.eval()

# Load DB features
with open("song_features_ext.json", "r") as f:
    song_db = json.load(f)

def extract(path):
    y, sr = librosa.load(path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return StandardScaler().fit_transform(mfcc.T).T

def pad(x, l):
    return F.pad(x, (0, l - x.shape[3])) if x.shape[3] < l else x[:, :, :, :l]

def recommend(features):
    x1 = torch.tensor(features, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    results = []
    for name, feat in song_db.items():
        x2 = torch.tensor(feat, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        max_len = max(x1.shape[3], x2.shape[3])
        x1p = pad(x1.clone(), max_len).to(device)
        x2p = pad(x2.clone(), max_len).to(device)
        with torch.no_grad():
            score = model(x1p, x2p).item()
            sim = torch.sigmoid(torch.tensor(score)).item()
            results.append((name, int(sim * 100)))
    return sorted(results, key=lambda x: x[1], reverse=True)[:10]

def parse_artist_title(filename):
    base = os.path.splitext(filename)[0]
    if "~" in base:
        artist, title = base.split("~", 1)
        return artist.strip(), title.strip()
    return "Unknown", base.strip()

if __name__ == "__main__":
    audio_file = sys.argv[1]
    feats = extract(audio_file)
    top_matches = recommend(feats)
    print(json.dumps([
        {
            "artist": parse_artist_title(name)[0],
            "title": parse_artist_title(name)[1],
            "matchScore": int(sim * 100)
        }
        for name, sim in top_matches
    ]))
