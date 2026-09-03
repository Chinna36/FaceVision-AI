from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

import cv2
import json
import os
import random
import datetime
import smtplib
import shutil
import tempfile
import numpy as np

from pathlib import Path
from email.message import EmailMessage

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
GUARDIAN_EMAIL = os.getenv("GUARDIAN_EMAIL")

# Maximum image upload size: 10 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024


# ============================================================
# TENSORFLOW / KERAS
# ============================================================

import tensorflow as tf

# We use tf_keras because the mask detector is an older Keras
# model saved with a non-standard ".model" extension.
try:
    import tf_keras
    from tf_keras.models import load_model as tf_keras_load_model
    from tf_keras.preprocessing.image import img_to_array

    TF_KERAS_AVAILABLE = True

    print("tf_keras imported successfully.")

except Exception as e:
    print("TF-KERAS IMPORT ERROR:")
    print(type(e).__name__)
    print(str(e))

    TF_KERAS_AVAILABLE = False

    from tensorflow.keras.models import load_model as tf_keras_load_model
    from tensorflow.keras.preprocessing.image import img_to_array


# ============================================================
# DEEPFACE
# ============================================================

try:
    from deepface import DeepFace

    DEEPFACE_AVAILABLE = True

    print("DeepFace imported successfully.")

except Exception as e:

    DeepFace = None
    DEEPFACE_AVAILABLE = False

    print("DeepFace import failed:")
    print(type(e).__name__)
    print(str(e))


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="FaceVision-AI API",
    description="AI-based face, age, smile, mask and emotion analysis API",
    version="1.0.1"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC DIRECTORY
# ============================================================

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "Backend is working",
        "service": "FaceVision-AI",
        "version": "1.0.1"
    }


# ============================================================
# RENDER HEALTH CHECK
# ============================================================

@app.get("/healthz")
def healthz():
    """
    Lightweight health endpoint for Render.
    This endpoint intentionally does not run AI inference.
    """

    return {
        "status": "healthy",
        "service": "FaceVision-AI"
    }


# ============================================================
# ANALYTICS
# ============================================================

ANALYTICS_FILE = "analytics.json"


def create_default_analytics():
    return {
        "smile_count": 0,
        "mask_count": 0,
        "emotion_count": {},
        "emotion_total": 0
    }


def load_analytics():

    if not os.path.exists(ANALYTICS_FILE):

        data = create_default_analytics()

        try:
            with open(ANALYTICS_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("ANALYTICS CREATE ERROR:", str(e))

        return data

    try:

        with open(ANALYTICS_FILE, "r") as f:
            data = json.load(f)

        # Protect against old/incomplete analytics files.
        defaults = create_default_analytics()

        for key, value in defaults.items():
            if key not in data:
                data[key] = value

        return data

    except Exception as e:

        print("ANALYTICS READ ERROR:")
        print(type(e).__name__)
        print(str(e))

        return create_default_analytics()


def save_analytics(data):

    try:

        with open(ANALYTICS_FILE, "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:

        print("ANALYTICS SAVE ERROR:")
        print(type(e).__name__)
        print(str(e))


def update_analytics(smile, mask, emotion):

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


# ============================================================
# CONTENT
# ============================================================

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


# ============================================================
# EMAIL ALERT
# ============================================================

def send_alert_email():

    try:

        if not SENDER_EMAIL:
            print("EMAIL ERROR: SENDER_EMAIL is not configured.")
            return False

        if not SENDER_PASSWORD:
            print("EMAIL ERROR: SENDER_PASSWORD is not configured.")
            return False

        if not GUARDIAN_EMAIL:
            print("EMAIL ERROR: GUARDIAN_EMAIL is not configured.")
            return False

        msg = EmailMessage()

        msg["Subject"] = "Fear Emotion Detected"
        msg["From"] = SENDER_EMAIL
        msg["To"] = GUARDIAN_EMAIL

        msg.set_content(
            "Fear emotion detected by FaceVision-AI. "
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

        print("ALERT EMAIL SENT")

        return True

    except Exception as e:

        print("EMAIL ERROR:")
        print(type(e).__name__)
        print(str(e))

        return False


# ============================================================
# PEACEFUL MUSIC
# ============================================================

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


# ============================================================
# SAVE IMAGE
# ============================================================

def save_image(frame):

    name = datetime.datetime.now().strftime(
        "img_%Y%m%d_%H%M%S_%f.jpg"
    )

    path = STATIC_DIR / name

    try:

        success = cv2.imwrite(
            str(path),
            frame
        )

        if not success:
            print("WARNING: Could not save image.")
            return None

        return f"/static/{name}"

    except Exception as e:

        print("IMAGE SAVE ERROR:")
        print(type(e).__name__)
        print(str(e))

        return None


# ============================================================
# MODEL PATHS
# ============================================================

MODEL_DIR = Path("models")

FACE_PROTO = MODEL_DIR / "deploy.prototxt"

FACE_MODEL = (
    MODEL_DIR /
    "res10_300x300_ssd_iter_140000.caffemodel"
)

AGE_PROTO = MODEL_DIR / "age_deploy.prototxt"

AGE_MODEL = MODEL_DIR / "age_net.caffemodel"

MASK_MODEL = MODEL_DIR / "mask_detector.model"

SMILE_MODEL = MODEL_DIR / "haarcascade_smile.xml"


# ============================================================
# MODEL STATUS
# ============================================================

FACE_MODEL_AVAILABLE = False
AGE_MODEL_AVAILABLE = False
MASK_MODEL_AVAILABLE = False
SMILE_MODEL_AVAILABLE = False


face_net = None
age_net = None
mask_model = None
smile_cascade = None


# ============================================================
# FILE CHECK
# ============================================================

def check_model_file(path, model_name):

    if not path.exists():

        print(
            f"WARNING: {model_name} not found:"
        )

        print(
            f"       {path}"
        )

        return False

    if path.is_dir():

        print(
            f"WARNING: {model_name} is a directory:"
        )

        print(
            f"       {path}"
        )

        return False

    print(
        f"{model_name} found:"
    )

    print(
        f"       {path}"
    )

    return True


# ============================================================
# FACE MODEL
# ============================================================

print()
print("=" * 60)
print("LOADING FACE DETECTION MODEL")
print("=" * 60)

try:

    if (
        check_model_file(
            FACE_PROTO,
            "Face prototxt"
        )
        and
        check_model_file(
            FACE_MODEL,
            "Face caffemodel"
        )
    ):

        face_net = cv2.dnn.readNet(
            str(FACE_PROTO),
            str(FACE_MODEL)
        )

        FACE_MODEL_AVAILABLE = True

        print(
            "Face detection model loaded successfully."
        )

except Exception as e:

    print("FACE MODEL LOAD ERROR:")
    print(type(e).__name__)
    print(str(e))


# ============================================================
# AGE MODEL
# ============================================================

print()
print("=" * 60)
print("LOADING AGE DETECTION MODEL")
print("=" * 60)

try:

    if (
        check_model_file(
            AGE_PROTO,
            "Age prototxt"
        )
        and
        check_model_file(
            AGE_MODEL,
            "Age caffemodel"
        )
    ):

        age_net = cv2.dnn.readNet(
            str(AGE_PROTO),
            str(AGE_MODEL)
        )

        AGE_MODEL_AVAILABLE = True

        print(
            "Age detection model loaded successfully."
        )

except Exception as e:

    print("AGE MODEL LOAD ERROR:")
    print(type(e).__name__)
    print(str(e))


# ============================================================
# SMILE MODEL
# ============================================================

print()
print("=" * 60)
print("LOADING SMILE DETECTION MODEL")
print("=" * 60)

try:

    if check_model_file(
        SMILE_MODEL,
        "Smile cascade"
    ):

        smile_cascade = cv2.CascadeClassifier(
            str(SMILE_MODEL)
        )

        if smile_cascade.empty():

            print(
                "Smile cascade failed to load."
            )

        else:

            SMILE_MODEL_AVAILABLE = True

            print(
                "Smile detection model loaded successfully."
            )

except Exception as e:

    print("SMILE MODEL LOAD ERROR:")
    print(type(e).__name__)
    print(str(e))


# ============================================================
# MASK MODEL
# ============================================================

print()
print("=" * 60)
print("LOADING MASK DETECTION MODEL")
print("=" * 60)

print(
    f"Mask model path: {MASK_MODEL}"
)


def load_mask_detector():

    global MASK_MODEL_AVAILABLE

    MASK_MODEL_AVAILABLE = False

    if not MASK_MODEL.exists():

        print()
        print("MASK MODEL NOT FOUND")
        print(
            f"Expected file: {MASK_MODEL}"
        )

        return None

    # --------------------------------------------------------
    # Method 1:
    # tf_keras directly
    # --------------------------------------------------------

    if TF_KERAS_AVAILABLE:

        try:

            print()
            print(
                "Trying tf_keras legacy loader..."
            )

            model = tf_keras_load_model(
                str(MASK_MODEL),
                compile=False
            )

            MASK_MODEL_AVAILABLE = True

            print(
                "MASK MODEL LOADED SUCCESSFULLY "
                "USING TF-KERAS."
            )

            return model

        except Exception as e:

            print()
            print(
                "TF-KERAS MASK LOAD FAILED:"
            )

            print(type(e).__name__)
            print(str(e))

    # --------------------------------------------------------
    # Method 2:
    # Check if it is actually HDF5 and make .h5 copy
    # --------------------------------------------------------

    temporary_h5 = None

    try:

        import h5py

        print()
        print(
            "Checking whether mask_detector.model "
            "is an HDF5 model..."
        )

        with h5py.File(
            str(MASK_MODEL),
            "r"
        ) as f:

            print(
                "HDF5 model detected."
            )

            print(
                "HDF5 keys:",
                list(f.keys())
            )

        # Create temporary H5 file.
        fd, temporary_h5_path = tempfile.mkstemp(
            suffix=".h5"
        )

        os.close(fd)

        temporary_h5 = Path(
            temporary_h5_path
        )

        shutil.copyfile(
            str(MASK_MODEL),
            str(temporary_h5)
        )

        print(
            "Temporary H5 copy created:"
        )

        print(
            temporary_h5
        )

        # Try tf_keras first.
        if TF_KERAS_AVAILABLE:

            try:

                model = tf_keras_load_model(
                    str(temporary_h5),
                    compile=False
                )

                MASK_MODEL_AVAILABLE = True

                print(
                    "MASK MODEL LOADED SUCCESSFULLY "
                    "FROM TEMPORARY H5 FILE."
                )

                return model

            except Exception as e:

                print(
                    "Temporary H5 tf_keras loading failed:"
                )

                print(type(e).__name__)
                print(str(e))

        # Final fallback.
        try:

            model = tf.keras.models.load_model(
                str(temporary_h5),
                compile=False
            )

            MASK_MODEL_AVAILABLE = True

            print(
                "MASK MODEL LOADED SUCCESSFULLY "
                "USING TEMPORARY H5 FILE."
            )

            return model

        except Exception as e:

            print(
                "TensorFlow temporary H5 loading failed:"
            )

            print(type(e).__name__)
            print(str(e))

    except Exception as e:

        print()
        print(
            "MASK MODEL HDF5 CHECK FAILED:"
        )

        print(type(e).__name__)
        print(str(e))

    finally:

        # Remove temporary file.
        if temporary_h5 is not None:

            try:

                if temporary_h5.exists():
                    temporary_h5.unlink()

            except Exception as e:

                print(
                    "WARNING: Could not delete temporary H5 file:",
                    str(e)
                )

    print()
    print("=" * 60)
    print("MASK MODEL COULD NOT BE LOADED")
    print("=" * 60)

    MASK_MODEL_AVAILABLE = False

    return None


mask_model = load_mask_detector()


# ============================================================
# AGE LIST
# ============================================================

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


# ============================================================
# FINAL MODEL STATUS
# ============================================================

print()
print("=" * 60)
print("ALL AVAILABLE MODELS")
print("=" * 60)

print(
    "Face detection:",
    FACE_MODEL_AVAILABLE
)

print(
    "Age detection:",
    AGE_MODEL_AVAILABLE
)

print(
    "Smile detection:",
    SMILE_MODEL_AVAILABLE
)

print(
    "Mask detection:",
    MASK_MODEL_AVAILABLE
)

print(
    "Emotion detection:",
    DEEPFACE_AVAILABLE
)

print("=" * 60)
print()


# ============================================================
# MODELS STATUS API
# ============================================================

@app.get("/models")
def models_status():

    return {
        "face_detection": FACE_MODEL_AVAILABLE,
        "age_detection": AGE_MODEL_AVAILABLE,
        "smile_detection": SMILE_MODEL_AVAILABLE,
        "mask_detection": MASK_MODEL_AVAILABLE,
        "emotion_detection": DEEPFACE_AVAILABLE,

        "emotion_note": (
            "Emotion detection is enabled using DeepFace."
            if DEEPFACE_AVAILABLE
            else
            "DeepFace could not be loaded. Emotion will return neutral."
        ),

        "models_directory": str(MODEL_DIR),

        "api_status": "ready"
    }


# ============================================================
# HEALTH API
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",

        "models": {
            "face": FACE_MODEL_AVAILABLE,
            "age": AGE_MODEL_AVAILABLE,
            "smile": SMILE_MODEL_AVAILABLE,
            "mask": MASK_MODEL_AVAILABLE,
            "emotion": DEEPFACE_AVAILABLE
        }
    }


# ============================================================
# EMOTION DETECTION
# ============================================================

def detect_emotion(face):

    print(
        "STEP 5: Running emotion detection..."
    )

    if not DEEPFACE_AVAILABLE:

        print(
            "DeepFace is unavailable."
        )

        return "neutral"

    try:

        # Face is already cropped.
        # DeepFace does not need another detector.

        emotion_result = DeepFace.analyze(
            img_path=face,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend="skip"
        )

        # DeepFace normally returns a list.
        if isinstance(
            emotion_result,
            list
        ):

            if len(emotion_result) == 0:
                return "neutral"

            emotion_result = emotion_result[0]

        if not isinstance(
            emotion_result,
            dict
        ):

            return "neutral"

        emotion = emotion_result.get(
            "dominant_emotion",
            "neutral"
        )

        emotion = str(
            emotion
        ).lower()

        print(
            "EMOTION:",
            emotion
        )

        return emotion

    except Exception as e:

        print()
        print(
            "EMOTION DETECTION ERROR"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "Falling back to neutral."
        )

        return "neutral"


# ============================================================
# MASK DETECTION
# ============================================================

def detect_mask(face):

    print(
        "STEP 4: Running mask detection..."
    )

    if mask_model is None:

        print(
            "MASK MODEL IS NOT AVAILABLE."
        )

        return "Unknown"

    try:

        resized_face = cv2.resize(
            face,
            (224, 224)
        )

        arr = img_to_array(
            resized_face
        )

        arr = arr.astype(
            "float32"
        ) / 255.0

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
            "MASK RAW PREDICTION:",
            prediction
        )

        # Expected output:
        #
        # [mask_probability, no_mask_probability]
        #
        # Some old models may return a nested array.

        if prediction.ndim < 2:

            print(
                "Unexpected mask prediction dimensions."
            )

            return "Unknown"

        values = prediction[0]

        if len(values) < 2:

            print(
                "Unexpected mask model output."
            )

            return "Unknown"

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

        print(
            "MASK:",
            mask
        )

        return mask

    except Exception as e:

        print()
        print(
            "MASK DETECTION ERROR"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        return "Unknown"


# ============================================================
# FACE DETECTION
# ============================================================

def detect_face(frame):

    if face_net is None:

        print(
            "FACE MODEL IS NOT AVAILABLE."
        )

        return None

    try:

        h, w = frame.shape[:2]

        # IMPORTANT:
        # This blob creation was missing in the older version.
        blob = cv2.dnn.blobFromImage(
            frame,
            scalefactor=1.0,
            size=(300, 300),
            mean=(104, 117, 123)
        )

        face_net.setInput(
            blob
        )

        detections = face_net.forward()

        best_face = None
        best_confidence = 0.0

        for i in range(
            detections.shape[2]
        ):

            confidence = float(
                detections[
                    0,
                    0,
                    i,
                    2
                ]
            )

            if confidence < 0.60:
                continue

            box = (
                detections[
                    0,
                    0,
                    i,
                    3:7
                ]
                *
                np.array(
                    [
                        w,
                        h,
                        w,
                        h
                    ]
                )
            ).astype(int)

            x1, y1, x2, y2 = box

            # Clamp coordinates.
            x1 = max(
                0,
                min(x1, w - 1)
            )

            y1 = max(
                0,
                min(y1, h - 1)
            )

            x2 = max(
                0,
                min(x2, w)
            )

            y2 = max(
                0,
                min(y2, h)
            )

            if x2 <= x1:
                continue

            if y2 <= y1:
                continue

            current_face = frame[
                y1:y2,
                x1:x2
            ]

            if current_face.size == 0:
                continue

            if confidence > best_confidence:

                best_confidence = confidence

                best_face = current_face

        print(
            "BEST FACE CONFIDENCE:",
            best_confidence
        )

        return best_face

    except Exception as e:

        print(
            "FACE DETECTION ERROR:"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        return None


# ============================================================
# ANALYZE API
# ============================================================

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...)
):

    print()
    print("=" * 60)
    print("NEW ANALYZE REQUEST")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # Check filename
        # ----------------------------------------------------

        print(
            "Received file:",
            file.filename
        )

        # ----------------------------------------------------
        # Read uploaded file
        # ----------------------------------------------------

        contents = await file.read()

        print(
            "File size:",
            len(contents),
            "bytes"
        )

        if not contents:

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "Uploaded file is empty"
                }
            )

        # ----------------------------------------------------
        # Protect server from huge uploads
        # ----------------------------------------------------

        if len(contents) > MAX_IMAGE_SIZE:

            return JSONResponse(
                status_code=413,
                content={
                    "error":
                        "Image is too large. "
                        "Maximum size is 10 MB."
                }
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

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "Could not decode uploaded image."
                }
            )

        h, w = frame.shape[:2]

        if h == 0 or w == 0:

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "Invalid image dimensions."
                }
            )

        print(
            f"IMAGE RECEIVED: {w}x{h}"
        )

        # ----------------------------------------------------
        # FACE DETECTION
        # ----------------------------------------------------

        print(
            "STEP 1: Running face detection..."
        )

        if not FACE_MODEL_AVAILABLE:

            return JSONResponse(
                status_code=503,
                content={
                    "error":
                        "Face detection model is not available."
                }
            )

        face = detect_face(
            frame
        )

        print(
            "STEP 1 DONE: Face detection completed"
        )

        if face is None:

            print(
                "NO FACE DETECTED"
            )

            return JSONResponse(
                status_code=400,
                content={
                    "error":
                        "No face detected. "
                        "Please upload a clear image "
                        "with a visible face."
                }
            )

        # ----------------------------------------------------
        # AGE
        # ----------------------------------------------------

        print(
            "STEP 2: Running age detection..."
        )

        age = "Unknown"

        if AGE_MODEL_AVAILABLE:

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

                age_predictions = (
                    age_net.forward()[0]
                )

                age_index = int(
                    np.argmax(
                        age_predictions
                    )
                )

                if (
                    0 <= age_index <
                    len(AGE_LIST)
                ):

                    age = AGE_LIST[
                        age_index
                    ]

            except Exception as e:

                print(
                    "AGE DETECTION ERROR:"
                )

                print(
                    type(e).__name__
                )

                print(
                    str(e)
                )

                age = "Unknown"

        print(
            "AGE:",
            age
        )

        # ----------------------------------------------------
        # SMILE
        # ----------------------------------------------------

        print(
            "STEP 3: Running smile detection..."
        )

        smile = "Not Smiling"

        if SMILE_MODEL_AVAILABLE:

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
                    "SMILE DETECTION ERROR:"
                )

                print(
                    type(e).__name__
                )

                print(
                    str(e)
                )

                smile = "Not Smiling"

        print(
            "SMILE:",
            smile
        )

        # ----------------------------------------------------
        # MASK
        # ----------------------------------------------------

        mask = detect_mask(
            face
        )

        # ----------------------------------------------------
        # EMOTION
        # ----------------------------------------------------

        emotion = detect_emotion(
            face
        )

        # ----------------------------------------------------
        # RESPONSE MESSAGE
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
                    "Fear detected, "
                    "but the guardian email "
                    "could not be sent."
                )

        elif emotion == "angry":

            music = get_peace_songs()

            print(
                "Music:",
                music
            )

            message = (
                "You seem angry. "
                "Please relax and listen "
                "to peaceful music."
            )

        elif emotion == "surprise":

            message = (
                "You seem surprised. "
                "Take a moment to understand "
                "what happened."
            )

        elif emotion == "disgust":

            message = (
                "You seem uncomfortable. "
                "Take a short break if needed."
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
        # ANALYTICS
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
        # SUCCESS RESPONSE
        # ----------------------------------------------------

        result = {

            "success": True,

            "age":
                age,

            "smile":
                smile,

            "mask":
                mask,

            "emotion":
                emotion,

            "message":
                message,

            "music":
                music,

            "speech_text":
                speech_text,

            "image_path":
                image_path,

            "analytics":
                load_analytics()
        }

        print()
        print(
            "ANALYZE SUCCESS"
        )

        print(
            result
        )

        print("=" * 60)

        return result

    except Exception as e:

        print()
        print("=" * 60)
        print("ANALYZE ERROR")
        print("=" * 60)

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print("=" * 60)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error":
                    "Analysis failed",
                "details":
                    str(e)
            }
        )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )