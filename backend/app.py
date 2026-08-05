from flask import Flask, render_template, request
import os

app = Flask(__name__, static_folder='static')

# Create static folder if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

peace_songs_global = []
emotion_data_global = {}  # Store emotion analysis results
quote_or_joke_global = ""  # Store quote or joke for happy/sad
captured_image_global = ""  # Store path to captured image


@app.route("/songs")
def show_songs():
    return render_template("songs.html", songs=peace_songs_global, emotion_data=emotion_data_global, quote_or_joke=quote_or_joke_global, captured_image=captured_image_global)


@app.route("/update_songs", methods=["POST"])
def update_songs():
    global peace_songs_global, emotion_data_global, quote_or_joke_global, captured_image_global
    data = request.json
    
    # If data is a dict with 'songs' key, extract all data
    if isinstance(data, dict) and "songs" in data:
        peace_songs_global = data.get("songs", [])
        emotion_data_global = data.get("emotion_analysis", {})
        quote_or_joke_global = data.get("quote_or_joke", "")
        captured_image_global = data.get("captured_image", "")
    else:
        # Assume it's just the songs list
        peace_songs_global = data if isinstance(data, list) else []
    
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
