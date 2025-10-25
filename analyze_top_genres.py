#!/usr/bin/env python3
"""Analyze user's top genres from listening history."""

import sys
import os
from collections import Counter
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

    # Get top tracks from last 6 months (medium_term)
    print("📊 Fetching your top 50 tracks from the past 6 months...")
    top_tracks = client.get_top_tracks(limit=50, time_range="medium_term")

    if not top_tracks:
        print("❌ No top tracks found")
        sys.exit(1)

    print(f"✅ Found {len(top_tracks)} top tracks\n")

    # Get artist details to extract genres
    print("🎭 Analyzing artist genres...\n")

    genre_counter = Counter()
    artist_ids = set()

    # Extract unique artist IDs from tracks
    for track in top_tracks:
        # Get full track details to access artist IDs
        track_id = track['uri'].split(':')[-1]
        track_details = client.sp.track(track_id)

        for artist in track_details['artists']:
            artist_ids.add(artist['id'])

    # Get artist details in batches (max 50 per request)
    artist_ids_list = list(artist_ids)
    all_genres = []

    for i in range(0, len(artist_ids_list), 50):
        batch = artist_ids_list[i:i+50]
        artists = client.sp.artists(batch)['artists']

        for artist in artists:
            if artist and artist['genres']:
                all_genres.extend(artist['genres'])
                genre_counter.update(artist['genres'])

    if not genre_counter:
        print("❌ No genre data found for your top tracks")
        sys.exit(1)

    # Get top 5 genres
    top_5_genres = genre_counter.most_common(5)

    print("="*60)
    print("🎵 YOUR TOP 5 GENRES (Past 6 Months)")
    print("="*60)
    print()

    for i, (genre, count) in enumerate(top_5_genres, 1):
        percentage = (count / len(all_genres)) * 100
        print(f"{i}. {genre.title()}")
        print(f"   Occurrences: {count} ({percentage:.1f}% of all genres)")
        print()

    print("="*60)
    print(f"📊 Analysis based on {len(top_tracks)} top tracks")
    print(f"🎭 From {len(artist_ids)} unique artists")
    print(f"🏷️  Total genre tags: {len(all_genres)}")
    print(f"🎯 Unique genres found: {len(genre_counter)}")
    print("="*60)

    # Show some example artists for top genre
    if top_5_genres:
        top_genre = top_5_genres[0][0]
        print(f"\n💡 Sample artists in '{top_genre}':")

        count = 0
        for track in top_tracks[:20]:  # Check first 20 tracks
            if count >= 5:
                break
            track_id = track['uri'].split(':')[-1]
            track_details = client.sp.track(track_id)

            for artist in track_details['artists']:
                artist_details = client.sp.artist(artist['id'])
                if top_genre in artist_details['genres']:
                    print(f"   - {artist['name']}")
                    count += 1
                    break

if __name__ == "__main__":
    main()
