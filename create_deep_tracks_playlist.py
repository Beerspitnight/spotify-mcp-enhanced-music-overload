#!/usr/bin/env python3
"""Create a playlist with deep/obscure punk tracks."""

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

    # Create the playlist
    playlist_name = "Deep Cuts: Punk Vault"
    playlist_description = "Deep tracks, B-sides, and album cuts from punk, skate punk, melodic hardcore, and post-hardcore artists. No hits, just the good stuff."

    print(f"📝 Creating playlist: {playlist_name}...")
    playlist_result = client.create_playlist(
        name=playlist_name,
        description=playlist_description,
        public=False
    )

    playlist_id = playlist_result['playlist_id']
    print(f"✅ Created playlist: {playlist_result['url']}\n")

    # Deep track search queries - focusing on album cuts and lesser-known songs
    # Using specific album names and avoiding their hit singles
    deep_track_searches = [
        # Hot Water Music - deep cuts
        "artist:Hot Water Music track:Rooftops",
        "artist:Hot Water Music track:Manual",
        "artist:Hot Water Music track:Wayfarer",

        # The Flatliners - album cuts
        "artist:The Flatliners track:Shithawks",
        "artist:The Flatliners track:Resuscitation of the Year",
        "artist:The Flatliners track:Sleep Your Life Away",

        # Iron Chic - lesser known
        "artist:Iron Chic track:Timecop",
        "artist:Iron Chic track:Bogus Journey",
        "artist:Iron Chic track:Spooky Scary",

        # Lawrence Arms - deep cuts
        "artist:The Lawrence Arms track:The Devil's Takin' Names",
        "artist:The Lawrence Arms track:Seventeener",
        "artist:The Lawrence Arms track:Beyond The Embarrassing Style",

        # Smoking Popes - obscure
        "artist:Smoking Popes track:Pretty Pathetic",
        "artist:Smoking Popes track:Welcome to Janesville",

        # Jawbreaker - album tracks
        "artist:Jawbreaker track:Accident Prone",
        "artist:Jawbreaker track:Condition Oakland",
        "artist:Jawbreaker track:Chesterfield King",

        # The Menzingers - B-sides
        "artist:The Menzingers track:Gates",
        "artist:The Menzingers track:Rivalries",
        "artist:The Menzingers track:Nice Things",

        # Bouncing Souls - lesser known
        "artist:Bouncing Souls track:Gone",
        "artist:Bouncing Souls track:Manthem",
        "artist:Bouncing Souls track:Kate Is Great",

        # Less Than Jake - album cuts
        "artist:Less Than Jake track:Nervous in the Alley",
        "artist:Less Than Jake track:Soundtrack of My Life",

        # Propagandhi - deep cuts
        "artist:Propagandhi track:Apparently I'm a PC Fascist",
        "artist:Propagandhi track:Iteration",

        # Against Me! - album tracks
        "artist:Against Me! track:Joy",
        "artist:Against Me! track:Borne on the FM Waves",
        "artist:Against Me! track:Walking Is Still Honest",

        # Alkaline Trio - B-sides
        "artist:Alkaline Trio track:Nose Over Tail",
        "artist:Alkaline Trio track:Steamer Trunk",
        "artist:Alkaline Trio track:Armageddon",

        # Paint It Black - obscure
        "artist:Paint It Black track:Exit Wounds",
        "artist:Paint It Black track:Bliss",

        # Latterman - deep cuts
        "artist:Latterman track:My Bedroom Is Like For Artists",

        # Dillinger Four - album cuts
        "artist:Dillinger Four track:Doublewhiskeycokenoice",
        "artist:Dillinger Four track:Let Them Eat Thomas Paine",
    ]

    print("🔍 Searching for deep tracks...\n")

    track_uris = []
    found_tracks = []

    for search_query in deep_track_searches:
        try:
            results = client.search_tracks(query=search_query, limit=1)
            if results:
                track = results[0]
                # Avoid duplicates
                if track['uri'] not in track_uris:
                    track_uris.append(track['uri'])
                    found_tracks.append(track)
                    print(f"✓ Found: {track['name']} - {track['artist']}")
        except Exception as e:
            print(f"✗ Search failed: {search_query[:50]}... ({str(e)})")

    print(f"\n✅ Found {len(track_uris)} deep tracks\n")

    if not track_uris:
        print("❌ No tracks found to add")
        sys.exit(1)

    # Add tracks to playlist
    print(f"📥 Adding {len(track_uris)} tracks to playlist...\n")

    result = client.add_tracks_to_playlist(
        playlist_id=playlist_id,
        track_uris=track_uris
    )

    print("="*60)
    print("✅ PLAYLIST CREATED SUCCESSFULLY!")
    print("="*60)
    print(f"\n🎵 Playlist: {playlist_name}")
    print(f"🔗 URL: {playlist_result['url']}")
    print(f"📊 Tracks Added: {result['tracks_added']}")
    print(f"\n📝 Description: {playlist_description}")
    print("\n" + "="*60)

    print("\n🎸 Track List:")
    print("="*60)
    for i, track in enumerate(found_tracks, 1):
        print(f"{i:2d}. {track['name']} - {track['artist']}")
        print(f"    Album: {track['album']}")

if __name__ == "__main__":
    main()
