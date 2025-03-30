import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import json
import csv

THRESHOLD = 0.5

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


def pad_mfcc(mfcc, target_length):
    """
    Pads the MFCC matrix with zeros along the time axis to match the target length.
    """
    current_length = mfcc.shape[1]
    if current_length < target_length:
        padding = target_length - current_length
        mfcc = torch.nn.functional.pad(mfcc, (0, padding))  # Pad only along the time dimension
    return mfcc

class SiameseDataset(Dataset):
    def __init__(self, dataset_file, feature_file):
        self.dataset_file = dataset_file

        # Load song features JSON
        with open(feature_file, 'r', encoding='utf-8') as f:
            self.song_features = json.load(f)

        # Load CSV-style dataset
        with open(dataset_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.pairs = []
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    song1 = parts[0].strip().strip('"')
                    song2 = parts[1].strip().strip('"')
                    label = int(parts[2].strip())
                    self.pairs.append((song1, song2, torch.tensor(label, dtype=torch.float32)))

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        song1, song2, label = self.pairs[idx]

        # Look up and convert to tensors
        if song1 not in self.song_features or song2 not in self.song_features:
            return None  # Will be filtered by collate_fn

        x1 = torch.tensor(self.song_features[song1], dtype=torch.float32).unsqueeze(0)
        x2 = torch.tensor(self.song_features[song2], dtype=torch.float32).unsqueeze(0)

        return x1, x2, label



class SiameseNet(nn.Module):
    def __init__(self, input_shape=(1, 13, 100), fc_output_dim=256):
        super(SiameseNet, self).__init__()
        print("✅ NEW SiameseCNN initialized")
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((3, 25))  # or any consistent shape
        # 🔍 Auto-infer flattened feature size from dummy input
        dummy_input = torch.zeros(1, *input_shape)
        dummy_out = self._extract_features(dummy_input)
        flattened_size = dummy_out.shape[1]

        self.fc = nn.Sequential(
            nn.Linear(flattened_size, fc_output_dim),
            nn.ReLU(),
            nn.Linear(fc_output_dim, 1)
        )
    
    def _extract_features(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.adaptive_pool(x)  # Force output to fixed size
        return x.view(x.size(0), -1)

    def forward(self, x1, x2):
        f1 = self._extract_features(x1)
        f2 = self._extract_features(x2)
        diff = torch.abs(f1 - f2)
        return self.fc(diff)


# Define loss function and optimizer
loss_function = nn.BCEWithLogitsLoss()
model = SiameseNet(input_shape=(1, 13, 100), fc_output_dim=256).to(device)
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Create DataLoader
batch_size = 32
train_dataset = SiameseDataset("train.csv", "song_features_ext.json")
test_dataset = SiameseDataset("test.csv", "song_features_ext.json")


#====== CUSTOM COLLATE FN that pads all MFCC matrices to the largest size matrix (song)
def collate_fn(batch):
    batch = [b for b in batch if b is not None]
    if len(batch) == 0:
        return None

    x1_batch, x2_batch, y_batch = zip(*batch)

    max_len = max([x.shape[2] for x in x1_batch + x2_batch])  # Time dimension

    def pad_batch(batch, max_len):
        return torch.stack([
            F.pad(x, (0, max_len - x.shape[2])) for x in batch
        ])

    x1_padded = pad_batch(x1_batch, max_len)
    x2_padded = pad_batch(x2_batch, max_len)
    y_tensor = torch.stack(y_batch)

    return x1_padded, x2_padded, y_tensor


train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
model.eval()

# --- Step 4: Grab a Batch and Check Shapes ---
batch = next(iter(train_loader))
if batch is not None:
    x1, x2, y = batch
    print("✅ Batch loaded")
    print("x1 shape:", x1.shape)  # Expected: (B, 1, 13, T)
    print("x2 shape:", x2.shape)
    print("y shape: ", y.shape)

    # --- Step 5: Dummy Forward Pass ---
    x1, x2 = x1.to(device), x2.to(device)
    with torch.no_grad():
        output = model(x1, x2)
        print("✅ Forward pass succeeded")
        print("Model output shape:", output.shape)  # Expected: (B, 1)
        print("Predictions:", torch.sigmoid(output).squeeze())
else:
    print("❌ No batch returned from DataLoader (check for invalid samples)")

test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

# Training function
def train_model(model, train_loader, loss_function, optimizer, num_epochs=10):
    model.train()

    for epoch in range(num_epochs):
        total_loss = 0
        processed = 0
        correct = 0

        for batch in train_loader:
            if batch is None:
                continue
            x1, x2, y = batch
            x1, x2, y = x1.to(device), x2.to(device), y.to(device)
            optimizer.zero_grad()
            y_pred = model(x1, x2).squeeze()

            loss = loss_function(y_pred, y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            # Accuracy
            predicted = (torch.sigmoid(y_pred) > 0.5).float()
            correct += (predicted == y).float().sum().item()
            processed += y.size(0)

        acc = correct / processed
        avg_loss = total_loss / len(train_loader)
        print(f"Epoch [{epoch+1}/{num_epochs}] | Loss: {avg_loss:.4f} | Accuracy: {acc:.4f}")



# Train the model
num_epochs = 25
train_model(model, train_loader, loss_function, optimizer, num_epochs)

#save this model to import later
torch.save(model.state_dict(), "siamese_model.pth")

#ensure that we can safely import the network for later use
model = SiameseNet(input_shape=(1, 13, 100), fc_output_dim=256).to(device)
model.load_state_dict(torch.load("siamese_model.pth"))
model.eval()

# Evaluate function
def evaluate_model(model, test_loader):
    model.eval()
    total = 0
    correct = 0

    with torch.no_grad():
        for batch in test_loader:
            if batch is None:
                continue

            x1, x2, y = batch
            x1, x2, y = x1.to(device), x2.to(device), y.to(device)

            y_pred = model(x1, x2).squeeze()
            predictions = (torch.sigmoid(y_pred) > 0.5).float()

            correct += (predictions == y).sum().item()
            total += y.size(0)

    acc = correct / total
    print(f"Test Accuracy: {acc:.4f}")
    return acc

# Evaluate the model
evaluate_model(model, test_loader)

