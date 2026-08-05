#!/usr/bin/env python
"""
Demo version of emotion detection - uses a test image instead of webcam.
Use this to test the system without a physical camera.
"""

import cv2
import numpy as np
from deepface import DeepFace
import pyttsx3
import random
import smtplib
from email.message import EmailMessage
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import webbrowser
import requests
import tempfile
import time
import threading
import datetime
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from pathlib import Path
import os
import traceback

# LOAD .ENV
def load_env():
    try:
        from dotenv import load_dotenv, find_dotenv
        dotenv_path = find_dotenv()
        if dotenv_path:
            load_dotenv(dotenv_path, override=True)
            print(f"[INFO] Loaded .env from: {dotenv_path}")
        else:
            print("[WARNING] .env file not found, checking environment variables...")
    except Exception as e:
        print(f"[WARNING] python-dotenv not available or failed: {e}")
        try:
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        line = line.split("#")[0].strip()
                        if "=" in line:
                            k, v = line.split("=", 1)
                            os.environ[k.strip()] = v.strip().strip('"').strip("'")
                print(f"[INFO] Manually loaded .env")
        except Exception as e2:
            print(f"[WARNING] Failed to load .env manually: {e2}")

load_env()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
GUARDIAN_EMAIL = os.getenv("GUARDIAN_EMAIL")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# EMAIL ALERT
def send_alert_email(emotion):
    try:
        if not SENDER_EMAIL or not SENDER_PASSWORD or not GUARDIAN_EMAIL:
            print("Email Error: Missing email credentials in .env file")
            return
        msg = EmailMessage()
        msg["Subject"] = f"Alert: {emotion} detected!"
        msg["From"] = SENDER_EMAIL
        msg["To"] = GUARDIAN_EMAIL
        msg.set_content(f"Emotion detected: {emotion}")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Alert email sent successfully!")
    except Exception as e:
        print("Email Error:", e)

# SPEAK
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# HAPPY QUOTES
happy_quotes = [
    "Happiness is a journey, not a destination.",
    "Smile! It's free therapy.",
    "Today is a good day to be happy.",
    "Every moment is a fresh beginning.",
    "You are stronger than you think.",
]

# SAD JOKES
sad_jokes = [
    "Why don't skeletons fight? They don't have guts!",
    "Why was the math book sad? It had too many problems.",
    "Parallel lines have so much in common. They never meet.",
]

# FETCH PEACE SONGS FROM SPOTIFY
def get_peace_songs():
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        results = sp.search(q="calm relaxing peace", type="track", limit=5)
        songs = []
        for item in results["tracks"]["items"]:
            track_id = item["id"]
            embed_url = f"https://open.spotify.com/embed/track/{track_id}"
            songs.append({
                "name": item["name"] + " - " + item["artists"][0]["name"],
                "embed_url": embed_url
            })
        return songs
    except Exception as e:
        print("Spotify Error:", e)
        return []

# SEND SONG LIST TO FLASK BACKEND
def send_songs_to_flask(song_list, emotion_analysis=None, quote_or_joke="", captured_image=""):
    try:
        payload = {
            "songs": song_list,
            "emotion_analysis": emotion_analysis or {},
            "quote_or_joke": quote_or_joke,
            "captured_image": captured_image
        }
        requests.post("http://127.0.0.1:5000/update_songs", json=payload)
        print("Data sent to Flask server.")
    except Exception as e:
        print("Flask communication error:", e)

# SAVE CAPTURED IMAGE
def save_captured_image(frame):
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"captured_{timestamp}.jpg"
    image_path = static_dir / image_filename
    cv2.imwrite(str(image_path), frame)
    return f"/static/{image_filename}"

# LOAD MODELS
face_proto = "models/deploy.prototxt"
face_model = "models/res10_300x300_ssd_iter_140000.caffemodel"
age_proto = "models/age_deploy.prototxt"
age_model = "models/age_net.caffemodel"
mask_model = load_model("models/mask_detector.model")

face_net = cv2.dnn.readNet(face_proto, face_model)
age_net = cv2.dnn.readNet(age_proto, age_model)

age_list = ['0-2','4-6','8-12','15-20','21-24','25-32','33-37','38-43','44-47','48-53','54-59','60-100']
smile_cascade = cv2.CascadeClassifier("models/haarcascade_smile.xml")

# EMOTION
def get_emotion(face):
    try:
        result = DeepFace.analyze(face, actions=['emotion'], enforce_detection=False)
        return result[0]["dominant_emotion"]
    except:
        return "N/A"

# MAIN DEMO - Uses a test image instead of webcam
def demo():
    print("\n>>> DEMO MODE - USING TEST IMAGE (No Webcam Required) <<<\n")
    
    # Create a test image (simple colored image with a face region)
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 50  # Gray background
    
    # Add some colored regions to simulate a face
    cv2.rectangle(frame, (150, 100), (500, 400), (100, 150, 200), -1)  # Face region
    cv2.putText(frame, "Test Face Region", (180, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    print("Using test image for emotion detection demo...")
    print("Note: Real emotion detection requires an actual face image.\n")
    
    # Save test frame
    image_path = save_captured_image(frame)
    
    # Simulate emotion detection
    emotions = ["happy", "sad", "fear", "angry", "neutral"]
    emotion = random.choice(emotions)
    
    print("\n----------- DEMO RESULT -----------")
    print(f"Age: 25-32 (demo)")
    print(f"Smile: Smiling (demo)")
    print(f"Mask: No Mask (demo)")
    print(f"Emotion: {emotion}")
    print("-------------------------------\n")
    
    # Process based on emotion
    if emotion == "happy":
        quote = random.choice(happy_quotes)
        speak(f"You look happy. {quote}")
        emotion_analysis = {"age": "25-32", "smile": "Smiling", "mask": "No Mask", "emotion": emotion}
        send_songs_to_flask([], emotion_analysis, quote, image_path)
        webbrowser.open("http://127.0.0.1:5000/songs")
    
    elif emotion == "sad":
        joke = random.choice(sad_jokes)
        speak(f"You look sad. Let me cheer you up. {joke}")
        emotion_analysis = {"age": "25-32", "smile": "Smiling", "mask": "No Mask", "emotion": emotion}
        send_songs_to_flask([], emotion_analysis, joke, image_path)
        webbrowser.open("http://127.0.0.1:5000/songs")
    
    elif emotion == "fear":
        speak("Fear detected. Sending alert message to guardian.")
        send_alert_email(emotion)
        emotion_analysis = {"age": "25-32", "smile": "Smiling", "mask": "No Mask", "emotion": emotion}
        send_songs_to_flask([], emotion_analysis, "Alert sent to guardian!", image_path)
        webbrowser.open("http://127.0.0.1:5000/songs")
    
    elif emotion == "angry":
        speak("You look angry. Opening peaceful music page.")
        emotion_analysis = {"age": "25-32", "smile": "Smiling", "mask": "No Mask", "emotion": emotion}
        songs = get_peace_songs()
        send_songs_to_flask(songs, emotion_analysis, "", image_path)
        webbrowser.open("http://127.0.0.1:5000/songs")
    
    else:
        speak(f"Emotion detected as {emotion}")
        emotion_analysis = {"age": "25-32", "smile": "Smiling", "mask": "No Mask", "emotion": emotion}
        send_songs_to_flask([], emotion_analysis, "", image_path)
        webbrowser.open("http://127.0.0.1:5000/songs")
    
    print("[SUCCESS] Demo completed!")

if __name__ == "__main__":
    demo()
