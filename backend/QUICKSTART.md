# Quick Start Guide - Emotion Detection System

## 1. Initial Setup (One-time)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create .env File
Create a `.env` file in the project root:

```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
GUARDIAN_EMAIL=guardian@example.com
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

Get credentials:
- **Gmail App Password**: https://support.google.com/accounts/answer/185833
- **Spotify Credentials**: https://developer.spotify.com/dashboard

## 2. Run the Program

### Option A: Quick Start (Recommended)
Just run this and everything starts automatically:
```bash
python main.py
```

This will:
- ✅ Auto-download models (66 MB) if missing
- ✅ Start Flask server
- ✅ Open webcam
- ✅ Detect emotions
- ✅ Display results in web browser

### Option B: Manual (Two Terminals)
**Terminal 1** - Start Flask server:
```bash
python app.py
```

**Terminal 2** - Run detection:
```bash
python main.py
```

## 3. Using the Program

1. **Face the Webcam** - Make sure your face is clearly visible
2. **Press 'q'** - Once detected emotion is shown to capture and analyze
3. **View Results** - Automatic web page opens with:
   - Captured image
   - Age, Smile status, Mask status
   - Detected emotion
   - Quotes (if happy), Jokes (if sad), Alert (if scared), Songs (if angry)

## 4. What to Expect

### First Run (~5-10 minutes)
```
[INFO] Some models are missing. Starting download...
[DOWNLOAD] Face Detection Model (Caffe)
  Progress: 100% (10MB / 10MB)
[DOWNLOAD] Age Detection Model (Caffe)
  Progress: 100% (44MB / 44MB)
... (downloads all models)
[SUCCESS] All models downloaded successfully!
```

### Subsequent Runs (~30 seconds)
```
[INFO] All models found locally.
[INFO] Webcam opened...
[FACE] Detected face in frame
[EMOTION] Happy - Showing motivational quote
[EMAIL] (If scared, email sent to guardian)
[SPOTIFY] (If angry, calm songs displayed)
[WEB] Opening http://127.0.0.1:5000/songs
```

## 5. Troubleshooting

| Issue | Solution |
|-------|----------|
| Models not downloading | Check internet, run `python download_models.py` manually |
| Flask error | Run `python app.py` in separate terminal |
| Email not sending | Check `.env` credentials with `python test_email_credentials.py` |
| Spotify not showing | Verify Spotify credentials in `.env` |
| Webcam not opening | Close other apps using camera, check permissions |

## 6. File Structure After First Run

```
ml-project/
├── main.py                 # Main script
├── app.py                  # Flask server
├── download_models.py      # Auto-downloader
├── requirements.txt
├── .env                    # Your credentials (don't share!)
├── models/                 # Models (auto-downloaded)
│   ├── *.caffemodel        # Downloaded automatically
│   ├── *.prototxt          # Downloaded automatically
│   ├── *.xml               # Downloaded automatically
│   └── *.model             # Downloaded automatically
├── static/                 # Captured images
│   └── captured_20251208_143022.jpg
├── templates/
│   └── songs.html
└── README.md
```

## 7. Testing

Before first run, you can test credentials:

```bash
# Test email
python test_email_credentials.py

# Test Spotify
python test_spotify.py
```

## 8. Tips & Tricks

- **Better Detection**: Good lighting, center face in frame
- **Change Music**: Edit `get_peace_songs()` in `main.py`
- **Change Quotes**: Edit `happy_quotes` list in `main.py`
- **Change Jokes**: Edit `sad_jokes` list in `main.py`
- **Custom Models**: Edit `download_models.py` to use your own models

## 9. Next Steps

After getting it working:
1. Test all 5 emotions (happy, sad, fear, angry, neutral)
2. Verify email sends when fear detected
3. Check Spotify songs play when angry
4. Customize quotes/jokes/songs to your preference

## 10. Help & Support

- **README.md**: Full documentation
- **test_*.py**: Test specific features
- **error_log.txt**: Check logs if something fails

---

**That's it!** You're ready to go. Run `python main.py` and enjoy! 🚀
