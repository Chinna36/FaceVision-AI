# Emotion Detection with Webcam

A Python application that detects emotions, age, smile status, and mask detection from webcam feed using deep learning models. Results are displayed on a modern web interface with Spotify integration.

## Features

- **Real-time Emotion Detection** - Detects emotions (happy, sad, fear, angry, neutral/other)
- **Age Detection** - Estimates age from facial features
- **Smile Detection** - Detects if person is smiling
- **Mask Detection** - Identifies if person is wearing a face mask
- **Web Interface** - Modern, interactive results page
- **Email Alerts** - Sends alert email when fear is detected
- **Spotify Integration** - Plays calming songs when anger is detected
- **Text-to-Speech** - Announces detected emotions
- **Image Capture** - Saves and displays the detected frame
- **Auto-Download Models** - Models automatically download on first run

## Installation

### 1. Clone/Download the Project

```bash
cd ml-project
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv310
venv310\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file in the project root with your credentials:

```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
GUARDIAN_EMAIL=guardian@example.com
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

**Important Notes:**
- For Gmail: Use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password
- For Spotify: Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Auto-Download Models

Models are **automatically downloaded** from their official sources on first run. No need to manually download or push large files to Git.

### What Gets Downloaded:

| Model | Size | Source |
|-------|------|--------|
| Face Detection (SSD) | ~10 MB | [OpenCV](https://github.com/opencv/opencv_3rdparty) |
| Age Detection | ~44 MB | [OpenCV](https://github.com/opencv/opencv_3rdparty) |
| Mask Detection | ~11 MB | [GitHub](https://github.com/chandrikadeb7/Face-Mask-Detection) |
| Cascades | ~1 MB | [OpenCV](https://github.com/opencv/opencv) |
| **Total** | **~66 MB** | **Public sources** |

### First Run:

When you run the program for the first time, you'll see:

```
[INFO] Some models are missing. Starting download...
[DOWNLOAD] Face Detection Model (Caffe)
  URL: https://raw.githubusercontent.com/...
  Progress: 100% (10MB / 10MB)
  [OK] Downloaded to models\res10_300x300_ssd_iter_140000.caffemodel
...
[SUCCESS] All models downloaded successfully!
```

### Manual Download:

To download models manually (without running the main program):

```bash
python download_models.py
```

This will download all models and show detailed progress.

## Usage

### Option 1: Using `main.py`

```bash
python main.py
```

This script will:
1. Auto-download models if missing
2. Start webcam capture
3. Detect emotions and other attributes
4. Start Flask server (in background)
5. Display results in web browser
6. Send email alerts if fear detected
7. Play Spotify songs if anger detected

### Option 2: Using Flask + Frontend Separately

**Terminal 1 - Start Flask Server:**
```bash
python app.py
```
Server runs on `http://127.0.0.1:5000`

**Terminal 2 - Run Detection Script:**
```bash
python main.py
```
This will capture and send data to the Flask server.

## Project Structure

```
ml-project/
├── main.py                 # Main emotion detection script
├── app.py                  # Flask backend server
├── download_models.py      # Auto-download models from internet
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in Git)
├── .gitignore             # Git ignore file (includes models/)
├── models/                # ML Models (auto-downloaded, not in Git)
│   ├── deploy.prototxt
│   ├── res10_300x300_ssd_iter_140000.caffemodel
│   ├── age_deploy.prototxt
│   ├── age_net.caffemodel
│   ├── mask_detector.model
│   ├── haarcascade_smile.xml
│   └── haarcascade_frontalface_default.xml
├── static/               # Web assets (images saved here)
│   └── captured_YYYYMMDD_HHMMSS.jpg
├── templates/            # HTML templates
│   └── songs.html
└── venv310/             # Virtual environment (not in Git)
```

## How It Works

1. **Capture Frame** - Reads from webcam
2. **Detect Face** - Uses SSD face detector (OpenCV DNN)
3. **Extract Attributes**:
   - Age detection (Age Net)
   - Smile detection (Haar Cascade)
   - Mask detection (Keras CNN)
   - Emotion detection (DeepFace)
4. **Route by Emotion**:
   - **Happy** → Display motivational quotes
   - **Sad** → Display jokes
   - **Fear** → Send email alert
   - **Angry** → Play calm Spotify songs
   - **Neutral/Other** → Display detected attributes
5. **Display Results** - Opens web page with results and captured image

## Troubleshooting

### Models Not Downloading

**Error:** `[ERROR] Failed to download models`

**Solution:**
- Check internet connection
- Manually run: `python download_models.py`
- Verify GitHub/raw.githubusercontent.com is accessible

### Flask Server Not Running

**Error:** `Flask communication error`

**Solution:**
- Flask must be running: Start `python app.py` in separate terminal before `main.py`
- Or just run `python main.py` (starts Flask automatically in background)

### Email Not Sending

**Error:** `Email Error: Missing email credentials`

**Solution:**
- Check `.env` file has SENDER_EMAIL, SENDER_PASSWORD, GUARDIAN_EMAIL
- For Gmail: Use [App Password](https://support.google.com/accounts/answer/185833), not regular password
- Verify credentials are correct: `python test_email_credentials.py`

### Spotify Songs Not Playing

**Error:** `Spotify Error`

**Solution:**
- Check SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in `.env`
- Get credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Script will play audio preview from Spotify embed

### Webcam Not Opening

**Error:** `Cannot open webcam`

**Solution:**
- Ensure webcam is not used by another application
- Check camera permissions in Windows Settings
- Try pressing 'q' to close and restart

## Git Workflow

The `models/` directory is excluded from Git via `.gitignore`. This means:

✅ **Good**: Small repo (~1 MB instead of 108 MB)
✅ **Good**: Models auto-download on first run
✅ **Good**: Each developer gets latest models

⚠️ **Note**: Models must exist in `models/` before running. The script auto-downloads them.

## Requirements

See `requirements.txt` for full list:
- OpenCV (cv2) - Computer vision
- TensorFlow/Keras - Mask detection
- DeepFace - Emotion detection (~550 MB auto-download on first use)
- Flask - Web backend
- pyttsx3 - Text-to-speech
- spotipy - Spotify API
- python-dotenv - Environment variables
- numpy - Numerical operations

## Advanced Usage

### Download Models Only (Without Running Detection)

```bash
python download_models.py
```

### Start Flask Server Only

```bash
python app.py
```
Then access `http://127.0.0.1:5000/songs` in browser (no data until main.py runs)

### Run Without Email/Spotify

Edit `main.py` and comment out the email/Spotify sections if credentials unavailable.

### Custom Model Sources

Edit `download_models.py` to use different model sources:

```python
{
    "url": "your_custom_model_url",
    "filepath": self.models_dir / "your_model.caffemodel",
    "description": "Your Model Description"
}
```

## Performance Notes

- **First Run**: ~5-10 minutes (66 MB model download + 550 MB DeepFace emotion model)
- **Subsequent Runs**: ~30 seconds startup
- **Real-time Detection**: 15-30 FPS on modern GPU, 2-5 FPS on CPU
- **DeepFace**: Auto-downloads emotion model (~550 MB) on first use

## License

This project uses models from:
- OpenCV (BSD License)
- TensorFlow/Keras (Apache 2.0)
- DeepFace (MIT License)

## Support

For issues:
1. Check the Troubleshooting section
2. Verify all environment variables are set
3. Run test files: `python test_email_credentials.py`, `python test_spotify.py`
4. Check internet connection for model downloads

## Future Enhancements

- [ ] Support for multiple faces in one frame
- [ ] Real-time streaming to web dashboard
- [ ] Model fine-tuning on custom data
- [ ] Docker containerization
- [ ] Mobile app integration
- [ ] Advanced emotion analytics dashboard
