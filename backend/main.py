from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import cv2
import json
import os
import sqlite3
import hashlib
import secrets
import uuid
import random
import datetime
import smtplib
import shutil
import tempfile
import numpy as np

from pathlib import Path
from pydantic import BaseModel
from email.message import EmailMessage

from dotenv import load_dotenv

# ------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------------------

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
GUARDIAN_EMAIL = os.getenv("GUARDIAN_EMAIL")

# DeepFace is disabled by default for Render stability.
# Change this to "true" later after the basic analysis works.
ENABLE_DEEPFACE = os.getenv("ENABLE_DEEPFACE", "false").lower() == "true"

# ------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------

app = FastAPI(
    title="FaceVision AI",
    description="AI-based face analysis API",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# STATIC DIRECTORY
# ------------------------------------------------------------

Path("static").mkdir(exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# ------------------------------------------------------------
# BASIC ROUTES
# ------------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "Backend is working",
        "service": "FaceVision-AI",
        "version": "1.0.1"
    }


@app.get("/healthz")
def healthz():
    return {
        "status": "healthy",
        "service": "FaceVision-AI"
    }


# ------------------------------------------------------------
# ANALYTICS
# ------------------------------------------------------------

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
            json.dump(data, f, indent=4)

    try:

        with open(ANALYTICS_FILE, "r") as f:
            return json.load(f)

    except Exception:

        data = {
            "smile_count": 0,
            "mask_count": 0,
            "emotion_count": {},
            "emotion_total": 0
        }

        save_analytics(data)

        return data


def save_analytics(data):

    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def update_analytics(smile, mask, emotion):

    try:

        data = load_analytics()

        if smile == "Smiling":
            data["smile_count"] += 1

        if mask == "Mask":
            data["mask_count"] += 1

        if emotion:

            data["emotion_count"][emotion] = (
                data["emotion_count"].get(emotion, 0) + 1
            )

        data["emotion_total"] = sum(
            data["emotion_count"].values()
        )

        save_analytics(data)

    except Exception as e:

        print("ANALYTICS ERROR:", str(e))


# ------------------------------------------------------------
# MESSAGES
# ------------------------------------------------------------

HAPPY_QUOTES = [
    "Keep smiling! Your happiness is contagious.",
    "A happy face can brighten the whole day.",
    "Keep spreading positive energy!",
    "Your smile looks amazing!",
    "Happiness looks great on you!"
]


SAD_JOKES = [
    "Why did the computer go to the doctor? Because it had a virus!",
    "What do you call a sleeping computer? A snooze processor!",
    "Why was the math book sad? Because it had too many problems.",
    "What did one wall say to the other wall? I'll meet you at the corner!",
    "Why don't scientists trust atoms? Because they make up everything!"
]


# ------------------------------------------------------------
# EMAIL ALERT
# ------------------------------------------------------------

def send_alert_email():

    if not SENDER_EMAIL or not SENDER_PASSWORD or not GUARDIAN_EMAIL:

        print("EMAIL ERROR: Email environment variables are not configured.")

        return False

    try:

        msg = EmailMessage()

        msg["Subject"] = "⚠ Fear Emotion Detected"

        msg["From"] = SENDER_EMAIL

        msg["To"] = GUARDIAN_EMAIL

        msg.set_content(
            "Fear emotion detected by FaceVision AI. "
            "Please check immediately."
        )

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=20
        ) as smtp:

            smtp.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )

            smtp.send_message(msg)

        print("ALERT EMAIL SENT SUCCESSFULLY.")

        return True

    except Exception as e:

        print("EMAIL ERROR:", str(e))

        return False


# ------------------------------------------------------------
# PEACEFUL MUSIC
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# SAVE ANALYZED IMAGE
# ------------------------------------------------------------

def save_image(frame):

    name = datetime.datetime.now().strftime(
        "img_%Y%m%d_%H%M%S_%f.jpg"
    )

    path = Path("static") / name

    success = cv2.imwrite(
        str(path),
        frame
    )

    if not success:

        print("WARNING: Could not save image.")

        return None

    return f"/static/{name}"


# ------------------------------------------------------------
# MODEL DIRECTORY
# ------------------------------------------------------------

MODEL_DIR = Path("models")


# ------------------------------------------------------------
# MODEL STATUS
# ------------------------------------------------------------

face_net = None
age_net = None
mask_model = None
smile_cascade = None

FACE_DETECTION_AVAILABLE = False
AGE_DETECTION_AVAILABLE = False
SMILE_DETECTION_AVAILABLE = False
MASK_DETECTION_AVAILABLE = False


# ------------------------------------------------------------
# FACE DETECTION MODEL
# ------------------------------------------------------------

print("")
print("============================================================")
print("LOADING FACE DETECTION MODEL")
print("============================================================")

try:

    face_prototxt = MODEL_DIR / "deploy.prototxt"

    face_weights = (
        MODEL_DIR /
        "res10_300x300_ssd_iter_140000.caffemodel"
    )

    print("Face prototxt:", face_prototxt)
    print("Face weights:", face_weights)

    if not face_prototxt.exists():

        raise FileNotFoundError(
            f"Missing file: {face_prototxt}"
        )

    if not face_weights.exists():

        raise FileNotFoundError(
            f"Missing file: {face_weights}"
        )

    face_net = cv2.dnn.readNet(
        str(face_prototxt),
        str(face_weights)
    )

    FACE_DETECTION_AVAILABLE = True

    print("Face detection model loaded successfully.")

except Exception as e:

    print(
        "FACE MODEL ERROR:",
        repr(e)
    )

    face_net = None


# ------------------------------------------------------------
# AGE DETECTION MODEL
# ------------------------------------------------------------

print("")
print("============================================================")
print("LOADING AGE DETECTION MODEL")
print("============================================================")

try:

    age_prototxt = MODEL_DIR / "age_deploy.prototxt"

    # Your models folder contains age_net.caffemodel.
    age_weights = MODEL_DIR / "age_net.caffemodel"

    # Fallback to age_net (1).caffemodel if necessary.
    if not age_weights.exists():

        fallback_age_weights = (
            MODEL_DIR / "age_net (1).caffemodel"
        )

        if fallback_age_weights.exists():

            age_weights = fallback_age_weights

    print("Age prototxt:", age_prototxt)
    print("Age weights:", age_weights)

    if not age_prototxt.exists():

        raise FileNotFoundError(
            f"Missing file: {age_prototxt}"
        )

    if not age_weights.exists():

        raise FileNotFoundError(
            f"Missing age model file: {age_weights}"
        )

    age_net = cv2.dnn.readNet(
        str(age_prototxt),
        str(age_weights)
    )

    AGE_DETECTION_AVAILABLE = True

    print("Age detection model loaded successfully.")

except Exception as e:

    print(
        "AGE MODEL ERROR:",
        repr(e)
    )

    age_net = None


# ------------------------------------------------------------
# SMILE DETECTION MODEL
# ------------------------------------------------------------

print("")
print("============================================================")
print("LOADING SMILE DETECTION MODEL")
print("============================================================")

try:

    smile_path = MODEL_DIR / "haarcascade_smile.xml"

    print("Smile cascade:", smile_path)

    if not smile_path.exists():

        raise FileNotFoundError(
            f"Missing file: {smile_path}"
        )

    smile_cascade = cv2.CascadeClassifier(
        str(smile_path)
    )

    if smile_cascade.empty():

        raise RuntimeError(
            "Smile cascade could not be loaded."
        )

    SMILE_DETECTION_AVAILABLE = True

    print("Smile detection model loaded successfully.")

except Exception as e:

    print(
        "SMILE MODEL ERROR:",
        repr(e)
    )

    smile_cascade = None


# ------------------------------------------------------------
# MASK MODEL
# ------------------------------------------------------------

def load_mask_model():

    """
    Loads the mask detector.

    The project contains:
        models/mask_detector.model

    Keras 3 expects .keras or .h5 extensions, while this
    project uses the .model extension.

    We therefore detect an HDF5 model and temporarily copy it
    to a .h5 file before loading it with tf_keras.
    """

    mask_path = MODEL_DIR / "mask_detector.model"

    print("")
    print("============================================================")
    print("LOADING MASK DETECTION MODEL")
    print("============================================================")

    print("Mask model path:", mask_path)

    if not mask_path.exists():

        raise FileNotFoundError(
            f"Missing mask model: {mask_path}"
        )

    # --------------------------------------------------------
    # Try legacy tf_keras first.
    # --------------------------------------------------------

    try:

        from tf_keras.models import load_model

        print("Trying tf_keras legacy loader...")

        # Check whether the file is an HDF5 file.
        with open(mask_path, "rb") as f:

            header = f.read(8)

        is_hdf5 = (
            header == b"\x89HDF\r\n\x1a\n"
        )

        print("HDF5 model detected:", is_hdf5)

        if is_hdf5:

            temp_dir = Path(
                tempfile.mkdtemp(
                    prefix="facevision_mask_"
                )
            )

            temp_h5 = temp_dir / "mask_detector.h5"

            shutil.copy2(
                mask_path,
                temp_h5
            )

            print(
                "Temporary H5 model:",
                temp_h5
            )

            try:

                model = load_model(
                    str(temp_h5),
                    compile=False
                )

            finally:

                try:

                    shutil.rmtree(
                        temp_dir,
                        ignore_errors=True
                    )

                except Exception:

                    pass

        else:

            model = load_model(
                str(mask_path),
                compile=False
            )

        print(
            "MASK MODEL LOADED SUCCESSFULLY USING TF-KERAS."
        )

        return model

    except Exception as e:

        print(
            "TF-KERAS MASK LOADING ERROR:",
            repr(e)
        )

    # --------------------------------------------------------
    # Fallback to TensorFlow Keras.
    # --------------------------------------------------------

    try:

        from tensorflow.keras.models import load_model

        print(
            "Trying TensorFlow Keras fallback loader..."
        )

        temp_dir = None

        try:

            with open(mask_path, "rb") as f:

                header = f.read(8)

            is_hdf5 = (
                header == b"\x89HDF\r\n\x1a\n"
            )

            if is_hdf5:

                temp_dir = Path(
                    tempfile.mkdtemp(
                        prefix="facevision_mask_tf_"
                    )
                )

                temp_h5 = temp_dir / "mask_detector.h5"

                shutil.copy2(
                    mask_path,
                    temp_h5
                )

                model_path = temp_h5

            else:

                model_path = mask_path

            model = load_model(
                str(model_path),
                compile=False
            )

            print(
                "MASK MODEL LOADED SUCCESSFULLY USING "
                "TENSORFLOW KERAS."
            )

            return model

        finally:

            if temp_dir is not None:

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

    except Exception as e:

        print(
            "TENSORFLOW KERAS MASK LOADING ERROR:",
            repr(e)
        )

    raise RuntimeError(
        "Could not load mask_detector.model."
    )


try:

    mask_model = load_mask_model()

    MASK_DETECTION_AVAILABLE = True

except Exception as e:

    print(
        "MASK MODEL ERROR:",
        repr(e)
    )

    mask_model = None


# ------------------------------------------------------------
# MODEL SUMMARY
# ------------------------------------------------------------

print("")
print("============================================================")
print("ALL AVAILABLE MODELS")
print("============================================================")

print(
    "Face detection:",
    FACE_DETECTION_AVAILABLE
)

print(
    "Age detection:",
    AGE_DETECTION_AVAILABLE
)

print(
    "Smile detection:",
    SMILE_DETECTION_AVAILABLE
)

print(
    "Mask detection:",
    MASK_DETECTION_AVAILABLE
)

print(
    "DeepFace enabled:",
    ENABLE_DEEPFACE
)

print("============================================================")
print("")


# ------------------------------------------------------------
# AGE LABELS
# ------------------------------------------------------------

AGE_LIST = [
    "0-2",
    "4-6",
    "8-12",
    "15-20",
    "21-24",
    "25-32",
    "33-37",
    "38-43",
    "44-47",
    "48-53",
    "54-59",
    "60+"
]


# ------------------------------------------------------------
# EMOTION DETECTION
# ------------------------------------------------------------

def detect_emotion(face):

    print("STEP 5: Emotion detection...")

    # --------------------------------------------------------
    # Render stability mode
    # --------------------------------------------------------

    if not ENABLE_DEEPFACE:

        print(
            "DeepFace disabled. Returning neutral emotion."
        )

        return "neutral"

    # --------------------------------------------------------
    # Lazy import
    #
    # DeepFace is NOT imported during application startup.
    # It is imported only when an analysis request actually
    # needs emotion detection.
    # --------------------------------------------------------

    try:

        print("Loading DeepFace on demand...")

        from deepface import DeepFace

        print("DeepFace imported successfully.")

        result = DeepFace.analyze(
            img_path=face,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="skip",
            silent=True
        )

        if isinstance(result, list):

            if len(result) == 0:

                emotion = "neutral"

            else:

                emotion = result[0].get(
                    "dominant_emotion",
                    "neutral"
                )

        else:

            emotion = result.get(
                "dominant_emotion",
                "neutral"
            )

        if not emotion:

            emotion = "neutral"

        emotion = str(emotion).lower()

        print(
            "EMOTION:",
            emotion
        )

        return emotion

    except Exception as e:

        print(
            "DEEPFACE ERROR:",
            repr(e)
        )

        # Never allow emotion failure to break
        # the complete image analysis.

        return "neutral"


# ------------------------------------------------------------
# FACE BOX HELPER
# ------------------------------------------------------------

def get_safe_face_box(
    detection,
    width,
    height
):

    box = (
        detection[3:7] *
        np.array(
            [width, height, width, height]
        )
    ).astype(int)

    x1, y1, x2, y2 = box

    # Add small padding around face.
    padding_x = int(
        (x2 - x1) * 0.10
    )

    padding_y = int(
        (y2 - y1) * 0.10
    )

    x1 -= padding_x
    y1 -= padding_y
    x2 += padding_x
    y2 += padding_y

    # Clip to image boundaries.
    x1 = max(
        0,
        min(x1, width - 1)
    )

    y1 = max(
        0,
        min(y1, height - 1)
    )

    x2 = max(
        0,
        min(x2, width)
    )

    y2 = max(
        0,
        min(y2, height)
    )

    if x2 <= x1 or y2 <= y1:

        return None

    return x1, y1, x2, y2


# ------------------------------------------------------------
# ANALYZE ENDPOINT
# ------------------------------------------------------------

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...)
):

    print("")
    print("============================================================")
    print("NEW ANALYZE REQUEST")
    print("============================================================")

    try:

        # ----------------------------------------------------
        # Validate upload
        # ----------------------------------------------------

        if file is None:

            return {
                "success": False,
                "error": "No file was uploaded."
            }

        print(
            "Uploaded filename:",
            file.filename
        )

        print(
            "Uploaded content type:",
            file.content_type
        )

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        contents = await file.read()

        if not contents:

            return {
                "success": False,
                "error": "Uploaded file is empty."
            }

        print(
            "Uploaded file size:",
            len(contents),
            "bytes"
        )

        # ----------------------------------------------------
        # Decode image
        # ----------------------------------------------------

        frame = cv2.imdecode(
            np.frombuffer(
                contents,
                np.uint8
            ),
            cv2.IMREAD_COLOR
        )

        if frame is None:

            return {
                "success": False,
                "error": "Could not decode uploaded image."
            }

        height, width = frame.shape[:2]

        if height <= 0 or width <= 0:

            return {
                "success": False,
                "error": "Invalid image dimensions."
            }

        print(
            f"IMAGE RECEIVED: {width}x{height}"
        )

        # ----------------------------------------------------
        # STEP 1 — FACE DETECTION
        # ----------------------------------------------------

        print(
            "STEP 1: Running face detection..."
        )

        if not FACE_DETECTION_AVAILABLE:

            return {
                "success": False,
                "error": "Face detection model is unavailable."
            }

        # THIS WAS MISSING IN THE OLD CODE.
        # Create the face detection blob.
        blob = cv2.dnn.blobFromImage(
            frame,
            scalefactor=1.0,
            size=(300, 300),
            mean=(104.0, 117.0, 123.0),
            swapRB=False,
            crop=False
        )

        face_net.setInput(blob)

        detections = face_net.forward()

        print(
            "STEP 1 DONE: Face detection completed."
        )

        # ----------------------------------------------------
        # Find best face
        # ----------------------------------------------------

        face = None
        face_box = None
        highest_confidence = 0.0

        for i in range(
            detections.shape[2]
        ):

            confidence = float(
                detections[0, 0, i, 2]
            )

            if confidence > 0.60:

                current_box = get_safe_face_box(
                    detections[0, 0, i],
                    width,
                    height
                )

                if current_box is None:

                    continue

                x1, y1, x2, y2 = current_box

                current_face = frame[
                    y1:y2,
                    x1:x2
                ]

                if current_face.size == 0:

                    continue

                if confidence > highest_confidence:

                    highest_confidence = confidence

                    face = current_face

                    face_box = current_box

        if face is None:

            print(
                "NO FACE DETECTED."
            )

            return {
                "success": False,
                "error": "No face detected. Please upload a clear face image."
            }

        print(
            "Face detected with confidence:",
            round(
                highest_confidence,
                4
            )
        )

        # ----------------------------------------------------
        # STEP 2 — AGE DETECTION
        # ----------------------------------------------------

        print(
            "STEP 2: Running age detection..."
        )

        age = "Unknown"

        if AGE_DETECTION_AVAILABLE:

            try:

                age_blob = cv2.dnn.blobFromImage(
                    cv2.resize(
                        face,
                        (227, 227)
                    ),
                    scalefactor=1.0,
                    size=(227, 227),
                    mean=(
                        78.4263377603,
                        87.7689143744,
                        114.895847746
                    ),
                    swapRB=False
                )

                age_net.setInput(
                    age_blob
                )

                age_predictions = age_net.forward()

                age_index = int(
                    np.argmax(
                        age_predictions[0]
                    )
                )

                if (
                    0 <= age_index
                    < len(AGE_LIST)
                ):

                    age = AGE_LIST[
                        age_index
                    ]

            except Exception as e:

                print(
                    "AGE DETECTION ERROR:",
                    repr(e)
                )

                age = "Unknown"

        print(
            "AGE:",
            age
        )

        # ----------------------------------------------------
        # STEP 3 — SMILE DETECTION
        # ----------------------------------------------------

        print(
            "STEP 3: Running smile detection..."
        )

        smile = "Not Smiling"

        if SMILE_DETECTION_AVAILABLE:

            try:

                gray = cv2.cvtColor(
                    face,
                    cv2.COLOR_BGR2GRAY
                )

                smiles = (
                    smile_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.7,
                        minNeighbors=20
                    )
                )

                if len(smiles) > 0:

                    smile = "Smiling"

            except Exception as e:

                print(
                    "SMILE DETECTION ERROR:",
                    repr(e)
                )

                smile = "Not Smiling"

        print(
            "SMILE:",
            smile
        )

        # ----------------------------------------------------
        # STEP 4 — MASK DETECTION
        # ----------------------------------------------------

        print(
            "STEP 4: Running mask detection..."
        )

        mask = "Unknown"

        if MASK_DETECTION_AVAILABLE:

            try:

                mask_face = cv2.resize(
                    face,
                    (224, 224)
                )

                # Keep the original project's input format.
                arr = (
                    mask_face.astype(
                        np.float32
                    ) / 255.0
                )

                arr = np.expand_dims(
                    arr,
                    axis=0
                )

                prediction = mask_model.predict(
                    arr,
                    verbose=0
                )

                prediction = np.asarray(
                    prediction
                )

                print(
                    "Mask prediction:",
                    prediction
                )

                # ------------------------------------------------
                # Handle common model output shapes.
                # ------------------------------------------------

                if prediction.ndim == 2:

                    values = prediction[0]

                else:

                    values = prediction.flatten()

                if len(values) >= 2:

                    mask_val = float(
                        values[0]
                    )

                    no_mask_val = float(
                        values[1]
                    )

                    if mask_val > no_mask_val:

                        mask = "Mask"

                    else:

                        mask = "No Mask"

                elif len(values) == 1:

                    value = float(
                        values[0]
                    )

                    # Binary sigmoid output.
                    mask = (
                        "Mask"
                        if value >= 0.5
                        else "No Mask"
                    )

                else:

                    mask = "Unknown"

            except Exception as e:

                print(
                    "MASK DETECTION ERROR:",
                    repr(e)
                )

                mask = "Unknown"

        print(
            "MASK:",
            mask
        )

        # ----------------------------------------------------
        # STEP 5 — EMOTION
        # ----------------------------------------------------

        emotion = detect_emotion(
            face
        )

        # ----------------------------------------------------
        # MESSAGE / MUSIC / EMAIL
        # ----------------------------------------------------

        message = ""
        music = []

        if emotion == "happy":

            message = random.choice(
                HAPPY_QUOTES
            )

        elif emotion == "sad":

            message = random.choice(
                SAD_JOKES
            )

        elif emotion == "fear":

            email_sent = send_alert_email()

            if email_sent:

                message = (
                    "Fear detected. "
                    "Email sent to guardian."
                )

            else:

                message = (
                    "Fear detected. "
                    "Guardian email could not be sent."
                )

        elif emotion == "angry":

            music = get_peace_songs()

            message = (
                "You seem angry. "
                "Please relax and listen to peaceful music."
            )

        elif emotion == "surprise":

            message = (
                "You look surprised!"
            )

        elif emotion == "disgust":

            message = (
                "You seem uncomfortable."
            )

        else:

            message = (
                "You seem calm and neutral."
            )

        # ----------------------------------------------------
        # SPEECH TEXT
        # ----------------------------------------------------

        speech_text = (
            f"Emotion detected {emotion}. "
            f"{message}"
        )

        # ----------------------------------------------------
        # UPDATE ANALYTICS
        # ----------------------------------------------------

        update_analytics(
            smile,
            mask,
            emotion
        )

        # ----------------------------------------------------
        # SAVE IMAGE
        # ----------------------------------------------------

        image_path = save_image(
            frame
        )

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        analytics = load_analytics()

        response = {

            "success": True,

            "age": age,

            "smile": smile,

            "mask": mask,

            "emotion": emotion,

            "message": message,

            "music": music,

            "speech_text": speech_text,

            "image_path": image_path,

            "analytics": analytics

        }

        print(
            "ANALYSIS COMPLETED SUCCESSFULLY."
        )

        print(
            "Result:",
            {
                "age": age,
                "smile": smile,
                "mask": mask,
                "emotion": emotion
            }
        )

        print(
            "============================================================"
        )

        return response

    # --------------------------------------------------------
    # Unexpected application error
    # --------------------------------------------------------

    except Exception as e:

        print("")
        print(
            "============================================================"
        )
        print(
            "ANALYZE ERROR"
        )
        print(
            "============================================================"
        )

        print(
            "ERROR TYPE:",
            type(e).__name__
        )

        print(
            "ERROR:",
            repr(e)
        )

        print(
            "============================================================"
        )

        return {
            "success": False,
            "error": (
                "Image analysis failed. "
                "Please check the Render logs for details."
            ),
            "error_type": type(e).__name__
        }


# ------------------------------------------------------------
# MODELS STATUS
# ------------------------------------------------------------

@app.get("/models")
def models_status():

    return {

        "face_detection":
            FACE_DETECTION_AVAILABLE,

        "age_detection":
            AGE_DETECTION_AVAILABLE,

        "smile_detection":
            SMILE_DETECTION_AVAILABLE,

        "mask_detection":
            MASK_DETECTION_AVAILABLE,

        "emotion_detection":
            ENABLE_DEEPFACE,

        "emotion_note":
            (
                "DeepFace emotion detection is enabled."
                if ENABLE_DEEPFACE
                else
                "Emotion detection is temporarily set to neutral "
                "for Render deployment stability."
            ),

        "api_status":
            "ready"

    }


# ============================================================
# AUTHENTICATION
# ============================================================

AUTH_DB = "users.db"


def get_db():
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            guardian_email TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.
    """
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310000
    )

    return (
        salt.hex()
        + "$"
        + password_hash.hex()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against the stored PBKDF2 hash.
    """

    try:
        salt_hex, hash_hex = stored_hash.split("$")

        salt = bytes.fromhex(salt_hex)

        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            310000
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:
        return False


class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str
    guardianEmail: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# Initialize authentication database
init_auth_db()


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register_user(data: RegisterRequest):

    full_name = data.fullName.strip()
    email = data.email.strip().lower()
    password = data.password

    guardian_email = (
        data.guardianEmail.strip().lower()
        if data.guardianEmail
        else None
    )

    if len(full_name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Full name must be at least 2 characters."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters."
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required."
        )

    conn = get_db()

    try:

        existing_user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists."
            )

        user_id = str(uuid.uuid4())

        password_hash = hash_password(password)

        created_at = datetime.datetime.utcnow().isoformat()

        conn.execute(
            """
            INSERT INTO users
            (
                id,
                full_name,
                email,
                password_hash,
                guardian_email,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                full_name,
                email,
                password_hash,
                guardian_email,
                created_at
            )
        )

        conn.commit()

        return {
            "success": True,
            "message": "Account created successfully.",
            "user": {
                "id": user_id,
                "fullName": full_name,
                "email": email,
                "guardianEmail": guardian_email
            }
        }

    finally:
        conn.close()


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login_user(data: LoginRequest):

    email = data.email.strip().lower()
    password = data.password

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        if not verify_password(
            password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": user["id"],
                "fullName": user["full_name"],
                "email": user["email"],
                "guardianEmail": user["guardian_email"]
            }
        }

    finally:
        conn.close()