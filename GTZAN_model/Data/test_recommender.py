import os
import torch
import torch.nn.functional as F
from PIL import Image
from pathlib import Path
from torchvision import transforms
from CNN_Classification import SiameseNet  # Make sure this matches your model class
import heapq

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load trained model
model = SiameseNet().to(device)
model.load_state_dict(torch.load(r"C:/Users/Joe/Documents/GitHub/Resona/GTZAN_model/Data/GTZAN_30SEC_MODEL.pth", map_location=device))
model.eval()

# Define image transformation
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# === LOAD QUERY IMAGE ===
query = input("🎧 Enter your query (filename with extension): ").strip()
print(f"User entered: '{query}'")
spectrogram_dir = Path("C:/Users/Joe/Documents/GitHub/Resona/spectrograms_png")
query_path = spectrogram_dir / query
print(f"Resolved path: {query_path}")

if not os.path.exists(query_path):
    print(f"❌ Spectrogram for '{query}' not found.")
    exit()

query_img = Image.open(query_path).convert('RGB')
query_tensor = transform(query_img).unsqueeze(0).to(device)  # shape: [1, 1, 224, 224]

# === SCAN MUSIC FOLDER ===
music_root = "spectrograms_png"
song_scores = []

for root, _, files in os.walk(music_root):
    for fname in files:
        print(f"🔍 Comparing: {fname}")
        if not fname.endswith(".png"):
            continue
        full_path = os.path.join(root, fname)
        #print(f"Full path of candidate: {full_path}")
        if full_path == query_path:
            continue

        try:
            print("Made it here!")
            candidate_img = Image.open(full_path).convert('RGB')
            candidate_tensor = transform(candidate_img).unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(query_tensor, candidate_tensor).item()
                print(output)
                similarity = torch.sigmoid(torch.tensor(output)).item()
                print(similarity)
                song_scores.append((similarity, full_path))

        except Exception as e:
            print(f"⚠️ Skipping {fname}: {e}")

# === SHOW TOP K ===
top_k = 10
top_matches = heapq.nlargest(top_k, song_scores, key=lambda x: x[0])

print(f"\n🎯 Top {top_k} similar songs to '{query}':")
for i, (sim, path) in enumerate(top_matches, 1):
    print(f"{i:2d}. {os.path.basename(path)} — Match: {sim:.2%}")
