import csv
from collections import Counter

csv_file = './face_log.csv'

def load_emotion_counts(csv_file):
    emotion_counts = Counter()

    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            emotion = row['emotion']
            emotion_counts[emotion] += 1
    optimal_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None
    return emotion_counts, optimal_emotion

        
print(load_emotion_counts(csv_file))