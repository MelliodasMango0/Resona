import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from CNN_Classification import SiameseNet, SiameseImageDataset  # Adjust the import based on your module name
import matplotlib.pyplot as plt

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Hyperparameters
num_epochs = 2
batch_size = 64
learning_rate = 0.001

# Load datasets
train_dataset = SiameseImageDataset(csv_file='train_pairs.csv')
val_dataset = SiameseImageDataset(csv_file='val_pairs.csv')

img1, img2, label = train_dataset[0]
print(img1.shape, img2.shape, label)
log_interval = 2000  # Number of training samples between evaluations
samples_processed = 0
running_loss = 0.0
correct = 0
total = 0

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

model = SiameseNet().to(device)
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

train_losses, val_losses = [], []
train_accuracies, val_accuracies = [], []

model.train()
for epoch in range(num_epochs):
    print(f"\n--- Epoch {epoch+1}/{num_epochs} ---")
    for x1, x2, labels in train_loader:
        x1, x2, labels = x1.to(device), x2.to(device), labels.to(device).float()

        optimizer.zero_grad()
        outputs = model(x1, x2).squeeze()
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * labels.size(0)
        predictions = torch.sigmoid(outputs) > 0.5
        correct += (predictions == labels.byte()).sum().item()
        total += labels.size(0)
        samples_processed += labels.size(0)

        if samples_processed >= log_interval:
            epoch_loss = running_loss / samples_processed
            epoch_acc = correct / samples_processed
            train_losses.append(epoch_loss)
            train_accuracies.append(epoch_acc)

            print(f"[{samples_processed} samples] "
                  f"Train Loss: {epoch_loss:.4f}, Train Acc: {epoch_acc:.4f}")

            # Evaluate on validation set
            model.eval()
            val_running_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                for vx1, vx2, vlabels in val_loader:
                    vx1, vx2, vlabels = vx1.to(device), vx2.to(device), vlabels.to(device).float()
                    voutputs = model(vx1, vx2).squeeze()
                    vloss = criterion(voutputs, vlabels)
                    val_running_loss += vloss.item() * vlabels.size(0)
                    vpreds = torch.sigmoid(voutputs) > 0.5
                    val_correct += (vpreds == vlabels.byte()).sum().item()
                    val_total += vlabels.size(0)

            val_epoch_loss = val_running_loss / val_total
            val_epoch_acc = val_correct / val_total
            val_losses.append(val_epoch_loss)
            val_accuracies.append(val_epoch_acc)

            print(f"              Val Loss: {val_epoch_loss:.4f}, Val Acc: {val_epoch_acc:.4f}")

            # Reset counters
            model.train()
            running_loss = 0.0
            correct = 0
            total = 0
            samples_processed = 0


# Plotting
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(train_losses, label='Train Loss')
plt.plot(val_losses, label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss over Epochs')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(train_accuracies, label='Train Accuracy')
plt.plot(val_accuracies, label='Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title('Accuracy over Epochs')
plt.legend()

plt.tight_layout()
plt.show()
