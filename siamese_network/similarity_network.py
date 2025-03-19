import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import json
THRESHOLD = 0.5
import torch
from torch.utils.data import Dataset
import json
import csv

class SiameseDataset(Dataset):
    def __init__(self, dataset_file, feature_file):
        self.dataset_file = dataset_file

        # ✅ Load entire JSON file for fast lookups
        with open(feature_file, "r", encoding="utf-8") as f:
            self.song_features = json.load(f)

        # ✅ Use `csv.reader` to correctly parse song names (handles commas inside quotes)
        with open(dataset_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)  # CSV reader correctly handles quoted strings
            self.pairs = [row for row in reader if len(row) == 3]  # Ensure each row has 3 values

        # ✅ Debugging: Print incorrectly formatted lines
        for i, line in enumerate(self.pairs):
            if len(line) != 3:
                print(f"⚠️ Incorrect format at line {i+1}: {line}")

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        song1, song2, label = self.pairs[idx]

     # ✅ Fix: Strip spaces & quotes properly
        song1 = song1.strip('" ').strip()
        song2 = song2.strip('" ').strip()

        # ✅ Debugging: Check if songs exist in JSON
        if song1 not in self.song_features or song2 not in self.song_features:
             print(f"🚨 Skipping missing song pair: '{song1}' or '{song2}'")
             return None  # Skip invalid sample

        x1 = torch.tensor(self.song_features[song1], dtype=torch.float32)
        x2 = torch.tensor(self.song_features[song2], dtype=torch.float32)
        z = torch.abs(x1 - x2)
        y = torch.tensor(float(label), dtype=torch.float32)

        return z, y


   


# === CREATE DATALOADERS ===
batch_size = 32
train_dataset = SiameseDataset("train.csv", "song_features.json")
test_dataset = SiameseDataset("test.csv", "song_features.json")

def collate_fn(batch):
    batch = [b for b in batch if b is not None]  # ✅ Filter out None
    return torch.utils.data.default_collate(batch) if batch else None  # Avoid empty batch

# ✅ Use custom collate function in DataLoader
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)


train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)





# === CLASSIFIER NETWORK ===
class SimilarityClassifier(nn.Module):
    def __init__(self, input_dim=41):
        super(SimilarityClassifier, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Outputs a probability
        )

    def forward(self, z):
        return self.fc(z)

# === LOSS FUNCTION & OPTIMIZER ===
loss_function = nn.BCELoss()  # Binary Cross-Entropy Loss
classifier = SimilarityClassifier()
optimizer = optim.SGD(classifier.parameters(), lr=0.01, momentum=0.9)  # Stochastic Gradient Descent (SGD)


# === TRAINING FUNCTION ===
def train_model(model, train_loader, loss_function, optimizer, train_dataset, num_epochs=10):
    model.train()

    for epoch in range(num_epochs):
        total_loss = 0
        processed_samples = 0  # ✅ Track number of processed samples

        for z, y in train_loader:
            batch_size = z.shape[0]  # Number of samples in this batch
            processed_samples += batch_size  # ✅ Count processed samples

            optimizer.zero_grad()  # Reset gradients
            y_pred = model(z).squeeze()  # Forward pass
            loss = loss_function(y_pred, y)  # Compute loss
            loss.backward()  # Backpropagation
            optimizer.step()  # Update weights
            total_loss += loss.item()

        # ✅ Calculate number of skipped/missed samples
        total_samples = len(train_dataset)
        missed_samples = total_samples - processed_samples

        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss / len(train_loader):.4f}, "
              f"Processed: {processed_samples}/{total_samples}, Missed: {missed_samples}")


# === TRAIN MODEL ===
num_epochs = 25
train_model(classifier, train_loader, loss_function, optimizer, train_dataset, num_epochs)

# === TESTING FUNCTION ===
def evaluate_model(model, test_loader):
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for z, y in test_loader:
            y_pred = model(z).squeeze()
            predictions = (y_pred > THRESHOLD).float()  # Convert probabilities to 0/1 labels
            correct += (predictions == y).sum().item()
            total += y.size(0)

    accuracy = correct / total
    print(f"Test Accuracy: {accuracy:.4f}")

# === EVALUATE MODEL ===
evaluate_model(classifier, test_loader)


