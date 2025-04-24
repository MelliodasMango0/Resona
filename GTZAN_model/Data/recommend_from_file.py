import os
import sys
import json
import torch
import librosa
import numpy as np
import torch.nn.functional as F
import torchvision.transforms as transforms
from CNN_Classification import SiameseImageDataset
from PIL import Image

# CONFIG
MODEL_PATH = os.path.join(os.path.dirname(__file__), "GTZAN_30SEC_MODEL.pth")
SPECTROGRAM_DIR = os.path.join(os.path.dirname(__file__), "../../spectrograms_png")
SAMPLE_RATE = 22050
IMG_SIZE = (224, 224)
TOP_K = 5

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SiameseImageDataset()
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.to(device)
model.eval()

# Transforms
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize(IMG_SIZE),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

def extract_mel_spectrogram(path):
    y, sr = librosa.load(path, sr=SAMPLE_RATE)
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=224)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    img = Image.fromarray(mel_db).convert("L")
    return transform(img).unsqueeze(0)  # Shape: (1, 1, 224, 224)

def load_db_spectrograms():
    database = {}
    for fname in os.listdir(SPECTROGRAM_DIR):
        if fname.endswith(".png"):
            path = os.path.join(SPECTROGRAM_DIR, fname)
            img = Image.open(path).convert("L")
            tensor = transform(img).unsqueeze(0)
            database[fname] = tensor
    return database

def recommend(query_tensor, database):
    similarities = []
    with torch.no_grad():
        for name, db_tensor in database.items():
            input1 = query_tensor.to(device)
            input2 = db_tensor.to(device)
            score = model(input1, input2).item()
            sim = torch.sigmoid(torch.tensor(score)).item()
            similarities.append((name, int(sim * 100)))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:TOP_K]

def parse_artist_title(filename):
    base = os.path.splitext(filename)[0]
    if "~" in base:
        artist, title = base.split("~", 1)
        return artist.strip(), title.strip()
    return "Unknown", base.strip()

if __name__ == "__main__":
    try:
        audio_path = sys.argv[1]
        print("Processing input:", audio_path)
        query_tensor = extract_mel_spectrogram(audio_path)
        db = load_db_spectrograms()
        top_matches = recommend(query_tensor, db)

        output = []
        for name, score in top_matches:
            artist, title = parse_artist_title(name)
            output.append({
                "artist": artist,
                "title": title,
                "matchScore": score
            })

        print(json.dumps(output))
        sys.stdout.flush()

    except Exception as e:
        print("Fatal error:", str(e), file=sys.stderr)
        sys.exit(1)
