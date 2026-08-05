from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import cv2
import json
import os
import random
import datetime
import smtplib
import numpy as np

from pathlib import Path
from deepface import DeepFace
from email.message import EmailMessage
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import pyttsx3

# ================== ENV ==================
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
GUARDIAN_EMAIL = os.getenv("GUARDIAN_EMAIL")

# SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
# SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# ================== APP ==================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Path("static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================== TTS (FIXED) ==================
def speak(text: str):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("TTS ERROR:", e)

# ================== ANALYTICS ==================
ANALYTICS_FILE = "analytics.json"

def load_analytics():
    if not os.path.exists(ANALYTICS_FILE):
        data = {
            "smile_count": 0,
            "mask_count": 0,
            "emotion_count": {},
            "emotion_total": 0
        }
        with open(ANALYTICS_FILE, "w") as f:
            json.dump(data, f)

    with open(ANALYTICS_FILE) as f:
        return json.load(f)

def save_analytics(data):
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_analytics(smile, mask, emotion):
    data = load_analytics()

    if smile == "Smiling":
        data["smile_count"] += 1

    if mask == "Mask":
        data["mask_count"] += 1

    data["emotion_count"][emotion] = data["emotion_count"].get(emotion, 0) + 1
    data["emotion_total"] = sum(data["emotion_count"].values())

    save_analytics(data)

# ================== CONTENT ==================
HAPPY_QUOTES = [
    "Happiness is a journey, not a destination.",
    "Smile! It's free therapy.",
    "Good things are on the way.",
    "Every day may not be good, but there's something good in every day.",
    "Happiness is homemade.",
    "Choose joy every day.",
    "Keep smiling, because life is a beautiful thing and there's so much to smile about.",
    "The best way to cheer yourself up is to try to cheer somebody else up.",
    "Happiness is not by chance, but by choice.",
    "Do more of what makes you happy."
]

SAD_JOKES = [
    "Why was the math book sad? Too many problems.",
    "Why don't skeletons fight? They don't have guts!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why did the bicycle fall over? Because it was two-tired!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the tomato turn red? Because it saw the salad dressing!",
    "Why did the golfer bring two pairs of pants? In case he got a hole in one!",
    "Why did the coffee file a police report? It got mugged!",
    "Why did the cookie go to the hospital? Because he felt crummy!",
    "Why was the computer cold? It left its Windows open!"
]

# ================== EMAIL ==================
def send_alert_email():
    try:
        msg = EmailMessage()
        msg["Subject"] = "⚠ Fear Emotion Detected"
        msg["From"] = SENDER_EMAIL
        msg["To"] = GUARDIAN_EMAIL
        msg.set_content("Fear emotion detected. Please check immediately.")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)

    except Exception as e:
        print("EMAIL ERROR:", e)

# ================== SPOTIFY ==================
# def get_peace_songs():
#     try:
#         auth = SpotifyClientCredentials(
#             client_id=SPOTIFY_CLIENT_ID,
#             client_secret=SPOTIFY_CLIENT_SECRET
#         )
#         sp = spotipy.Spotify(auth_manager=auth)

#         results = sp.search(
#             q="calm peaceful relaxing",
#             type="track",
#             limit=5
#         )

#         songs = []
#         for t in results["tracks"]["items"]:
#             songs.append({
#                 "name": f"{t['name']} - {t['artists'][0]['name']}",
#                 "embed_url": f"https://open.spotify.com/embed/track/{t['id']}"
#             })

#         return songs

#     except Exception as e:
#         print("SPOTIFY ERROR:", e)
#         return []

def get_peace_songs():
    return [
        {
            "name": "Weightless - Marconi Union",
            "url": "https://www.youtube.com/results?search_query=Weightless+Marconi+Union"
        },
        {
            "name": "Relaxing Piano Music",
            "url": "https://www.youtube.com/results?search_query=Relaxing+Piano+Music"
        },
        {
            "name": "Nature Sounds",
            "url": "https://www.youtube.com/results?search_query=Nature+Sounds"
        },
        {
            "name": "Calm Meditation Music",
            "url": "https://www.youtube.com/results?search_query=Calm+Meditation+Music"
        },
        {
            "name": "Peaceful Instrumental Music",
            "url": "https://www.youtube.com/results?search_query=Peaceful+Instrumental+Music"
        }
    ]

# ================== SAVE IMAGE ==================
def save_image(frame):
    name = datetime.datetime.now().strftime("img_%Y%m%d_%H%M%S.jpg")
    path = Path("static") / name
    cv2.imwrite(str(path), frame)
    return f"/static/{name}"

# ================== MODELS ==================
MODEL_DIR = Path("models")

face_net = cv2.dnn.readNet(
    str(MODEL_DIR / "deploy.prototxt"),
    str(MODEL_DIR / "res10_300x300_ssd_iter_140000.caffemodel")
)

age_net = cv2.dnn.readNet(
    str(MODEL_DIR / "age_deploy.prototxt"),
    str(MODEL_DIR / "age_net.caffemodel")
)

mask_model = load_model(str(MODEL_DIR / "mask_detector.model"))
smile_cascade = cv2.CascadeClassifier(str(MODEL_DIR / "haarcascade_smile.xml"))

AGE_LIST = [
    "0-2", "4-6", "8-12", "15-20", "21-24",
    "25-32", "33-37", "38-43", "44-47",
    "48-53", "54-59", "60+"
]

# ================== API ==================
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    frame = cv2.imdecode(
        np.frombuffer(await file.read(), np.uint8),
        cv2.IMREAD_COLOR
    )

    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        frame, 1.0, (300, 300), (104, 117, 123)
    )
    face_net.setInput(blob)
    detections = face_net.forward()

    face = None
    for i in range(detections.shape[2]):
        if detections[0, 0, i, 2] > 0.6:
            box = (detections[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
            face = frame[box[1]:box[3], box[0]:box[2]]
            break

    if face is None:
        return {"error": "No face detected"}

    # AGE
    age_blob = cv2.dnn.blobFromImage(cv2.resize(face, (227, 227)), 1, (227, 227))
    age_net.setInput(age_blob)
    age = AGE_LIST[np.argmax(age_net.forward()[0])]

    # SMILE
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    smile = "Smiling" if len(smile_cascade.detectMultiScale(gray, 1.7, 20)) else "Not Smiling"

    # MASK
    arr = img_to_array(cv2.resize(face, (224, 224))) / 255.0
    arr = np.expand_dims(arr, 0)
    mask_val, no_mask_val = mask_model.predict(arr)[0]
    mask = "Mask" if mask_val > no_mask_val else "No Mask"

    # EMOTION
    emotion = DeepFace.analyze(
        face,
        actions=["emotion"],
        enforce_detection=False
    )[0]["dominant_emotion"]

    message = ""
    music = []

    if emotion == "happy":
        message = random.choice(HAPPY_QUOTES)

    elif emotion == "sad":
        message = random.choice(SAD_JOKES)

    elif emotion == "fear":
        send_alert_email()
        message = "Fear detected. Email sent to guardian."

    elif emotion == "angry":
        music = get_peace_songs()
        print("Music:", music)
        message = "You seem angry. Please relax and listen to peaceful music."

    else:
        message = "You seem calm and neutral."

    speech_text = f"Emotion detected {emotion}. {message}"
    speak(speech_text)

    update_analytics(smile, mask, emotion)

    return {
        "age": age,
        "smile": smile,
        "mask": mask,
        "emotion": emotion,
        "message": message,
        "music": music,
        "speech_text": speech_text,
        "image_path": save_image(frame),
        "analytics": load_analytics()
    }
