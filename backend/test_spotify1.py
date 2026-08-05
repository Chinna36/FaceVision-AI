from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

print("Client ID loaded:", bool(client_id))
print("Client Secret loaded:", bool(client_secret))

auth = SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
)

sp = spotipy.Spotify(auth_manager=auth)

results = sp.search(
    q="calm peaceful relaxing",
    type="track",
    limit=5
)

for track in results["tracks"]["items"]:
    print(
        track["name"],
        "-",
        track["artists"][0]["name"]
    )