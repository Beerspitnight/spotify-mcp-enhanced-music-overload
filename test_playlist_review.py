#!/usr/bin/env python3
"""Test script to connect to Spotify and review the [TEST] MCP Test Playlist."""

import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from spotify_client import SpotifyClient

def main():
    # Load environment
    load_dotenv()

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    cache_path = os.getenv("SPOTIFY_CACHE_PATH", ".spotify_cache")

    if not client_id or not client_secret:
        print("❌ Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")
        sys.exit(1)

    # Initialize and authenticate
    print("🎵 Connecting to Spotify...")
    client = SpotifyClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        cache_path=cache_path
    )

    try:
        client.authenticate()
        print("✅ Connected to Spotify!\n")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    # Get all playlists
    print("📋 Fetching playlists...")
    playlists = client.get_user_playlists(limit=50)

    # Find the [TEST] MCP Test Playlist
    test_playlist = None
    for playlist in playlists:
        if "[TEST]" in playlist['name'] or "MCP Test" in playlist['name']:
            test_playlist = playlist
            break

    if not test_playlist:
        print("\n❌ Could not find [TEST] MCP Test Playlist")
        print("\nAvailable playlists:")
        for i, p in enumerate(playlists, 1):
            print(f"  {i}. {p['name']}")
        sys.exit(1)

    # Display playlist details
    print(f"\n{'='*60}")
    print(f"📝 PLAYLIST REVIEW: {test_playlist['name']}")
    print(f"{'='*60}\n")

    print(f"🔗 URL: {test_playlist['url']}")
    print(f"🆔 ID: {test_playlist['id']}")
    print(f"👁️  Visibility: {'Public' if test_playlist['public'] else 'Private'}")
    print(f"📊 Total Tracks: {test_playlist['tracks_total']}")
    print(f"📄 Description: {test_playlist['description'] or '(no description)'}\n")

    # Get tracks
    if test_playlist['tracks_total'] > 0:
        print(f"{'='*60}")
        print(f"🎵 TRACKS IN PLAYLIST ({test_playlist['tracks_total']} total)")
        print(f"{'='*60}\n")

        tracks = client.get_playlist_tracks(test_playlist['id'])

        for i, track in enumerate(tracks, 1):
            print(f"{i:2d}. {track['name']}")
            print(f"    Artist: {track['artist']}")
            print(f"    Album: {track['album']}")
            print(f"    URI: {track['uri']}\n")
    else:
        print("📭 Playlist is empty\n")

    print(f"{'='*60}")
    print("✅ Review Complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
