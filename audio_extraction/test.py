import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

def plot_audio_features(file_path):
    """Extracts and plots waveform, spectrogram, MFCCs, and chroma features."""
    try:
        print(f"Extracting and plotting features for: {file_path}")

        # Load audio
        y, sr = librosa.load(file_path, sr=22050)

        # Compute features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        spectrogram = librosa.feature.melspectrogram(y=y, sr=sr)

        # Create subplots
        fig, ax = plt.subplots(4, 1, figsize=(10, 12))

        # 1️⃣ Plot Waveform
        librosa.display.waveshow(y, sr=sr, ax=ax[0])
        ax[0].set(title="Waveform", xlabel="Time (s)", ylabel="Amplitude")

        # 2️⃣ Plot Spectrogram
        img = librosa.display.specshow(librosa.power_to_db(spectrogram, ref=np.max), sr=sr, x_axis="time", y_axis="mel", ax=ax[1])
        ax[1].set(title="Mel Spectrogram")
        fig.colorbar(img, ax=ax[1])

        # 3️⃣ Plot MFCCs
        img = librosa.display.specshow(mfccs, x_axis="time", sr=sr, ax=ax[2])
        ax[2].set(title="MFCCs")
        fig.colorbar(img, ax=ax[2])

        # 4️⃣ Plot Chroma Features
        img = librosa.display.specshow(chroma, x_axis="time", y_axis="chroma", sr=sr, ax=ax[3])
        ax[3].set(title="Chroma Features")
        fig.colorbar(img, ax=ax[3])

        # Show plots
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error visualizing features for {file_path}: {e}")

# Run the function
if __name__ == "__main__":
    query_song = "songs/song.mp3"  # Change to your file
    plot_audio_features(query_song)
