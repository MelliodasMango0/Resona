import os
import librosa
import numpy as np
import matplotlib.pyplot as plt

music_root = "music"
spectrogram_output_dir = "spectrograms_png"
os.makedirs(spectrogram_output_dir, exist_ok=True)

def save_mel_spectrogram_png(audio_path, output_path):
    y, sr = librosa.load(audio_path, sr=22050)
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=224)
    mel_db = librosa.power_to_db(mel, ref=np.max)

    # Pad or crop to 224 width
    if mel_db.shape[1] < 224:
        mel_db = np.pad(mel_db, ((0, 0), (0, 224 - mel_db.shape[1])), mode='constant')
    else:
        mel_db = mel_db[:, :224]

    # Save as PNG
    plt.imsave(output_path, mel_db, cmap='magma')

for root, _, files in os.walk(music_root):
    for file in files:
        if file.lower().endswith(('.mp3', '.wav', '.flac', '.m4a')):
            input_path = os.path.join(root, file)
            filename_wo_ext = os.path.splitext(file)[0]
            sanitized_name = filename_wo_ext.replace("/", "_").replace("\\", "_")
            output_path = os.path.join(spectrogram_output_dir, f"{sanitized_name}.png")

            try:
                print(f"Processing {input_path}")
                save_mel_spectrogram_png(input_path, output_path)
            except Exception as e:
                print(f"Error processing {input_path}: {e}")
