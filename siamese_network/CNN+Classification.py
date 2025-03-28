import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import json
import csv

THRESHOLD = 0.5


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
    def __getitem__(self, idx):
        song1, song2, label = self.pairs[idx]

        song1 = song1.strip('" ').strip()
        song2 = song2.strip('" ').strip()

        if song1 not in self.song_features or song2 not in self.song_features:
            print(f"Skipping missing song pair: '{song1}' or '{song2}'")
            return None

        x1 = torch.tensor(self.song_features[song1], dtype=torch.float32)
        x2 = torch.tensor(self.song_features[song2], dtype=torch.float32)

        # Pad the MFCCs to the same length
        max_length = max(x1.shape[1], x2.shape[1])
        x1 = self.pad_mfcc(x1, max_length)
        x2 = self.pad_mfcc(x2, max_length)

        # Compute the absolute difference between the two MFCCs
        z = torch.abs(x1 - x2)

        # Reshape z into [batch_size, 1, channels, length] for CNN
        z = z.unsqueeze(1)  # Add a channel dimension

        y = torch.tensor(float(label), dtype=torch.float32)

        return z, y

# Define a simple CNN model for feature extraction
class SiameseCNN(nn.Module):
    def __init__(self):
        super(SiameseCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=(3, 3), padding=1)  # 1 channel (13 MFCCs), 32 filters
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 13 * 50, 64)  # Example of final output size after conv

    def forward(self, x):
        # Reshape the input to be [batch_size, channels, height, width]
        x = x.unsqueeze(1)  # Add a channel dimension (1, 13, N)
        x = self.pool(nn.ReLU()(self.conv1(x)))  # Apply conv and pooling
        x = x.view(x.size(0), -1)  # Flatten the output for the fully connected layer
        x = self.fc1(x)  # Fully connected layer
        return x


# Siamese network architecture with CNN-based feature extraction
class SiameseNetwork(nn.Module):
    def __init__(self, feature_extractor):
        super(SiameseNetwork, self).__init__()
        self.feature_extractor = feature_extractor

    def forward(self, input1, input2):
        # Extract features for both songs
        feature1 = self.feature_extractor(input1)
        feature2 = self.feature_extractor(input2)

        # Compute the absolute difference between the feature vectors
        diff = torch.abs(feature1 - feature2)
        return diff


# Define loss function and optimizer
loss_function = nn.BCELoss()
model = SiameseNetwork(SiameseCNN(input_channels=1, num_features=13))
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Create DataLoader
batch_size = 32
train_dataset = SiameseDataset("train.csv", "song_features_ext.json")
test_dataset = SiameseDataset("test.csv", "song_features_ext.json")


#====== CUSTOM COLLATE FN that pads all MFCC matrices to the largest size matrix (song)
def collate_fn(batch):
    batch = [b for b in batch if b is not None]  # Filter out any None samples

    # Find the max sequence length in the batch for padding
    max_length = max([x[0].shape[1] for x in batch])  # Max length of the MFCC time dimension

    # Pad all MFCCs in the batch to the max length
    z_batch = []
    y_batch = []
    for z, y in batch:
        z = torch.nn.functional.pad(z, (0, max_length - z.shape[1]))  # Pad to max_length
        z_batch.append(z)
        y_batch.append(y)

    return torch.stack(z_batch, 0), torch.stack(y_batch, 0)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

# Training function
def train_model(model, train_loader, loss_function, optimizer, num_epochs=10):
    model.train()

    for epoch in range(num_epochs):
        total_loss = 0
        processed_samples = 0  # Track number of processed samples

        for z, y in train_loader:
            batch_size = z.shape[0]
            processed_samples += batch_size

            optimizer.zero_grad()
            y_pred = model(z[:, 0], z[:, 1]).squeeze()  # Forward pass through the network
            loss = loss_function(y_pred, y)  # Compute the loss
            loss.backward()  # Backpropagation
            optimizer.step()  # Update weights
            total_loss += loss.item()

        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss / len(train_loader):.4f}")


# Train the model
num_epochs = 10
train_model(model, train_loader, loss_function, optimizer, num_epochs)

# Evaluate function
def evaluate_model(model, test_loader):
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for z, y in test_loader:
            y_pred = model(z[:, 0], z[:, 1]).squeeze()
            predictions = (y_pred > THRESHOLD).float()
            correct += (predictions == y).sum().item()
            total += y.size(0)

    accuracy = correct / total
    print(f"Test Accuracy: {accuracy:.4f}")


# Evaluate the model
evaluate_model(model, test_loader)
