import librosa
import numpy as np
import os
import psycopg2

# PostgreSQL connection config
DB_NAME = "resona_db"
DB_USER = "postgres"
# DB_PASSWORD = 
DB_HOST = "localhost"
DB_PORT = "5432"

# Path to the base music directory (each subfolder is a genre)
music_root = "music"

# Character that splits the artist and title in the filename
DELIMITER = '~'

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cursor = conn.cursor()

# function to extract the features of a file
def extract_feature_vector(file_path):
    y, sr = librosa.load(file_path, sr=None)

    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    mfccs_mean = np.mean(mfccs, axis=1).tolist()
    mfccs_var = np.var(mfccs, axis=1).tolist()

    spectral_centroid_mean = np.mean(spectral_centroid).tolist()
    spectral_bandwidth_mean = np.mean(spectral_bandwidth).tolist()
    zcr_mean = np.mean(zcr).tolist()
    chroma_mean = np.mean(chroma, axis=1).tolist()

    return (
        mfccs_mean +
        mfccs_var +
        [spectral_centroid_mean, spectral_bandwidth_mean, zcr_mean] +
        chroma_mean
    )

# Walk through genre folders and process audio files
for genre in os.listdir(music_root):
    genre_path = os.path.join(music_root, genre)
    if not os.path.isdir(genre_path):
        continue

    for filename in os.listdir(genre_path):
        if not filename.lower().endswith((".mp3", ".wav", ".flac", ".ogg")):
            continue

        try:

            name = os.path.splitext(filename)[0]
            file_path = os.path.join(genre_path, filename)

            if DELIMITER not in name:
                print(f"⚠️ Skipping {filename} (missing delimiter '{DELIMITER}')")
                continue

            artist, title = map(str.strip, name.split(DELIMITER, 1))

            # Check if the song is already in the database
            cursor.execute("""
                SELECT 1 FROM songs WHERE title = %s AND artists = %s AND genre = %s
            """, (title, artist, genre))
            if cursor.fetchone():
                print(f"⚠️ Skipping '{artist} {DELIMITER} {title}' in genre '{genre}' (already in database)")
                continue

            print(f"🎵 Processing '{artist} {DELIMITER} {title}' in genre '{genre}'...")
            features = extract_feature_vector(file_path)
            vector_str = "[" + ", ".join([f"{v:.6f}" for v in features]) + "]"

            # Insert song with artist, title, genre, and features
            cursor.execute("""
                INSERT INTO songs (title, artists, genre, feature_vector)
                VALUES (%s, %s, %s, %s)
            """, (title, artist, genre, vector_str))

            conn.commit()

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

# Clean up
cursor.close()
conn.close()
print("✅ All songs processed and stored in the database.")
