import sys
import json
import librosa
import os
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn.functional as F
from CNN_Classification import SiameseNet

print("Starting recommend_from_file.py")
sys.stdout.flush()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
features_path = os.path.join(BASE_DIR, "song_features_ext.json")
model_path = os.path.join(BASE_DIR, "siamese_model.pth")

print("Model path:", model_path.encode('ascii', 'replace').decode())
print("Features path:", features_path.encode('ascii', 'replace').decode())
sys.stdout.flush()

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", str(device))
sys.stdout.flush()

model = SiameseNet(input_shape=(1, 13, 100)).to(device)
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()
print("Model loaded and set to eval mode")
sys.stdout.flush()

# Load DB features
with open(features_path, "r") as f:
    song_db = json.load(f)
print(f"Loaded database features for {len(song_db)} songs")
sys.stdout.flush()

def extract(path):
    print("Loading audio file:", path.encode('ascii', 'replace').decode())
    sys.stdout.flush()
    y, sr = librosa.load(path, sr=None)
    print(f"Extracting MFCCs (len={len(y)}, sr={sr})")
    sys.stdout.flush()
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    print("MFCC extraction complete")
    sys.stdout.flush()
    return StandardScaler().fit_transform(mfcc.T).T

def pad(x, l):
    return F.pad(x, (0, l - x.shape[3])) if x.shape[3] < l else x[:, :, :, :l]

def recommend(features):
    print("Starting recommendation computation...")
    sys.stdout.flush()
    x1 = torch.tensor(features, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    results = []
    print(f"Comparing against {len(song_db)} songs...")
    for name, feat in song_db.items():
        print("Comparing with:", name.encode('ascii', 'replace').decode())
        x2 = torch.tensor(feat, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        max_len = max(x1.shape[3], x2.shape[3])
        x1p = pad(x1.clone(), max_len).to(device)
        x2p = pad(x2.clone(), max_len).to(device)
        with torch.no_grad():
            score = model(x1p, x2p).item()
            sim = torch.sigmoid(torch.tensor(score)).item()
            results.append((name, int(sim * 100)))
    print("Recommendation computation complete")
    sys.stdout.flush()
    return sorted(results, key=lambda x: x[1], reverse=True)[:5]

def parse_artist_title(filename):
    base = os.path.splitext(filename)[0]
    if "~" in base:
        artist, title = base.split("~", 1)
        return artist.strip(), title.strip()
    return "Unknown", base.strip()

if __name__ == "__main__":
    try:
        audio_file = sys.argv[1]
        print("Received input file:", audio_file.encode('ascii', 'replace').decode())
        sys.stdout.flush()

        feats = extract(audio_file)
        print("Feature extraction successful")
        sys.stdout.flush()

        top_matches = recommend(feats)

        if not top_matches:
            print("No matches found", file=sys.stderr)
            sys.exit(1)

        output = []
        for name, sim in top_matches:
            try:
                artist, title = parse_artist_title(name)
            except Exception as e:
                print("Failed to parse artist/title for:", name.encode('ascii', 'replace').decode(), "-", e, file=sys.stderr)
                continue

            output.append({
                "artist": artist,
                "title": title,
                "matchScore": sim 
            })

        print(json.dumps(output))
        sys.stdout.flush()

    except Exception as e:
        print("Fatal error:", str(e).encode('ascii', 'replace').decode(), file=sys.stderr)
        sys.exit(1)
