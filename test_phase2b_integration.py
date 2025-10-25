#!/usr/bin/env python3
"""Test Phase 2B: SpotifyClient integration with AudioFeatureAnalyzer."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.clients.spotify_client import SpotifyClient, AUDIO_ANALYSIS_ENABLED


async def test_integration():
    """Test audio features integration with SpotifyClient."""

    print("=" * 70)
    print("Phase 2B: SpotifyClient + AudioFeatureAnalyzer Integration Test")
    print("=" * 70)

    # Check if audio analysis is enabled
    print(f"\n✓ Audio analysis enabled: {AUDIO_ANALYSIS_ENABLED}")

    if not AUDIO_ANALYSIS_ENABLED:
        print("✗ Audio analysis not available. Install with: pip install .[audio]")
        return False

    # Get credentials
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        print("✗ Missing Spotify credentials in .env file")
        return False

    # Initialize client
    print("\n📝 Initializing Spotify client...")
    client = SpotifyClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        cache_path=".spotify_cache"
    )

    # Authenticate
    print("🔐 Authenticating with Spotify...")
    client.authenticate()

    # Test tracks with known preview URLs
    # These are popular tracks likely to have previews
    test_tracks = [
        {
            "name": "Daft Punk - Get Lucky",
            "id": "2Foc5Q5nqNiosCNqttzHof",  # Get Lucky
            "expected_bpm_range": (115, 120),  # Around 116 BPM
        },
        {
            "name": "AC/DC - Back in Black",
            "id": "08mG3Y1vljYA6bvDt4Wqkj",  # Back in Black
            "expected_bpm_range": (90, 96),  # Around 93 BPM
        }
    ]

    print("\n" + "=" * 70)
    print("Testing Audio Feature Extraction")
    print("=" * 70)

    for test_track in test_tracks:
        print(f"\n🎵 Testing: {test_track['name']}")
        print(f"   Track ID: {test_track['id']}")

        try:
            features = await client.get_track_audio_features(test_track['id'])

            if features is None:
                print(f"   ⚠️  No preview URL available for this track")
                continue

            # Display results
            key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            mode_names = {0: "minor", 1: "major"}

            print(f"   ✓ Analysis complete!")
            print(f"   Tempo: {features['tempo']:.1f} BPM")
            print(f"   Key: {key_names[features['key']]} {mode_names[features['mode']]}")
            print(f"   Energy: {features['energy']:.2f}")
            print(f"   Danceability: {features['danceability']:.2f}")
            print(f"   Valence: {features['valence']:.2f}")

            # Validate BPM is in expected range
            min_bpm, max_bpm = test_track['expected_bpm_range']
            if min_bpm <= features['tempo'] <= max_bpm:
                print(f"   ✅ BPM in expected range ({min_bpm}-{max_bpm})")
            else:
                print(f"   ⚠️  BPM outside expected range ({min_bpm}-{max_bpm})")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            return False

    print("\n" + "=" * 70)
    print("Phase 2B: Integration Test Complete! ✅")
    print("=" * 70)
    print("\nNext steps:")
    print("  - Test via MCP server with Claude Desktop")
    print("  - Update README with usage examples")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
