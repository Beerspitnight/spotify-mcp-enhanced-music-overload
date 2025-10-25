#!/usr/bin/env python3
"""Find tracks with preview URLs for testing."""

import os
from dotenv import load_dotenv
from src.clients.spotify_client import SpotifyClient

load_dotenv()

client = SpotifyClient(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
)

client.authenticate()

# Search for various tracks
searches = [
    "artist:Radiohead track:Creep",
    "artist:Beatles track:Yesterday",
    "artist:Queen track:Bohemian",
    "artist:Nirvana track:Smells Like Teen Spirit",
    "artist:Pink Floyd track:Comfortably Numb"
]

print("Searching for tracks with preview URLs...\n")

tracks_with_previews = []

for search in searches:
    results = client.search_tracks(search, limit=5)
    for track in results:
        # Check if track has preview
        track_info = client.sp.track(track['id'])
        if track_info.get('preview_url'):
            tracks_with_previews.append({
                'name': track['name'],
                'artist': track['artist'],
                'id': track['id'],
                'preview_url': track_info['preview_url']
            })
            print(f"✓ {track['artist']} - {track['name']}")
            print(f"  ID: {track['id']}")
            print(f"  Preview: {track_info['preview_url'][:50]}...")
            print()

            if len(tracks_with_previews) >= 3:
                break

    if len(tracks_with_previews) >= 3:
        break

if not tracks_with_previews:
    print("❌ No tracks with preview URLs found in searches")
else:
    print(f"\n✅ Found {len(tracks_with_previews)} tracks with preview URLs")
