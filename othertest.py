import os

mp3_file = "/Users/melliodasmango0/Documents/Senior Year Spring/Resona/audio_extraction/rally_house_like_that.mp3"

if os.path.isfile(mp3_file):
    print("File exists! ✅")
else:
    print("File not found ❌")
