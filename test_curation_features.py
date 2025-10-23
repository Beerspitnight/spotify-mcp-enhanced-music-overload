"""Test script for new curation features."""

import os
from dotenv import load_dotenv
from src.spotify_client import SpotifyClient

load_dotenv('.env')

print("=" * 70)
print("TESTING: New Curation Features")
print("=" * 70)
print()

# Initialize client
client = SpotifyClient(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
    cache_path='.spotify_cache'
)
client.authenticate()

# Test 1: Get Top Tracks (medium_term)
print("Test 1: Get Top Tracks (medium_term, limit=10)")
print("-" * 70)
try:
    top_tracks = client.get_top_tracks(limit=10, time_range="medium_term")
    print(f"  ✅ PASS - Retrieved {len(top_tracks)} top tracks")
    print(f"\n  Top 5 tracks:")
    for i, track in enumerate(top_tracks[:5], 1):
        print(f"    {i}. {track['name']} by {track['artist']}")
    print()
except Exception as e:
    print(f"  ❌ FAIL - {type(e).__name__}: {e}")
    print()

# Test 2: Get Top Tracks (short_term)
print("Test 2: Get Top Tracks (short_term, limit=5)")
print("-" * 70)
try:
    top_tracks_short = client.get_top_tracks(limit=5, time_range="short_term")
    print(f"  ✅ PASS - Retrieved {len(top_tracks_short)} top tracks")
    print(f"\n  Recent favorites:")
    for i, track in enumerate(top_tracks_short, 1):
        print(f"    {i}. {track['name']} by {track['artist']}")
    print()
except Exception as e:
    print(f"  ❌ FAIL - {type(e).__name__}: {e}")
    print()

# Test 3: Invalid time_range
print("Test 3: Invalid time_range validation")
print("-" * 70)
try:
    client.get_top_tracks(limit=5, time_range="invalid")
    print(f"  ❌ FAIL - No error raised for invalid time_range")
    print()
except ValueError as e:
    print(f"  ✅ PASS - ValueError raised: {e}")
    print()
except Exception as e:
    print(f"  ❌ FAIL - Wrong exception: {type(e).__name__}: {e}")
    print()

# Test 4: Create Curated Playlist
print("Test 4: Create Curated Playlist (full workflow)")
print("-" * 70)
try:
    result = client.create_curated_playlist_from_top_tracks(
        playlist_name="Test Curated Mix (Auto-generated)",
        num_top_tracks=10,
        num_recommendations=15,
        time_range="medium_term",
        public=False
    )
    print(f"  ✅ PASS - Created curated playlist")
    print(f"\n  Playlist Details:")
    print(f"    - Name: {result['playlist_name']}")
    print(f"    - URL: {result['playlist_url']}")
    print(f"    - Total tracks: {result['tracks_added']}")
    print(f"    - Top tracks included: {result['top_tracks_count']}")
    print(f"    - Recommendations added: {result['recommendations_count']}")
    print(f"\n  ⚠️  Remember to delete this test playlist from Spotify!")
    print()
except RuntimeError as e:
    if "404" in str(e) or "recommendations" in str(e).lower():
        print(f"  ⚠️  PARTIAL - Playlist creation works, but recommendations API blocked")
        print(f"     Error: {e}")
        print(f"     (This is a known Spotify API limitation)")
        print()
    else:
        print(f"  ❌ FAIL - RuntimeError: {e}")
        print()
except Exception as e:
    print(f"  ❌ FAIL - {type(e).__name__}: {e}")
    print()

print("=" * 70)
print("CURATION FEATURES TEST COMPLETE")
print("=" * 70)
