import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="383cf15215324134ae6c830ed5bfb035",
    client_secret="1dea2fb7199540639df241286aae8bd4",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-playback-state user-modify-playback-state"
))

# PRINT DEVICES
devices = sp.devices()
print("Devices:", devices)

if not devices['devices']:
    print("\n❌ No active Spotify device found.")
    print("➡ Open Spotify on your phone or desktop")
    print("➡ Play any song, then pause it")
else:
    device_id = devices['devices'][0]['id']
    print("➡ Using device:", device_id)

    # Play a test song
    sp.start_playback(
        device_id=device_id,
        uris=["spotify:track:4VqPORuhp5EdPbeR92tGlQ"]  # test track
    )
    print("🎶 Playing song!")
