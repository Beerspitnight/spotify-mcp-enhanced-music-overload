"""Spotify MCP Server - Exposes Spotify API as MCP tools."""

import asyncio
import os
import sys
from typing import Any

# Print startup message immediately for debugging
print("🚀 Starting Spotify MCP Server...", file=sys.stderr, flush=True)

try:
    from dotenv import load_dotenv
except ImportError as e:
    print(f"⚠️  dotenv not available: {e}", file=sys.stderr, flush=True)
    # Define dummy load_dotenv if not available
    def load_dotenv(): pass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    print("✓ MCP imports successful", file=sys.stderr, flush=True)
except ImportError as e:
    print(f"❌ Failed to import MCP: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    from clients.spotify_client import SpotifyClient
    from logic.playlist_logic import PlaylistLogic
    from logic.artist_logic import ArtistLogic
    print("✓ Local imports successful", file=sys.stderr, flush=True)
except ImportError as e:
    print(f"❌ Failed to import local modules: {e}", file=sys.stderr, flush=True)
    sys.exit(1)


# Load environment variables
load_dotenv()

# Initialize MCP server
server = Server("spotify-mcp")

# Global clients and logic (initialized in main)
spotify_client: SpotifyClient = None
playlist_logic: PlaylistLogic = None
artist_logic: ArtistLogic = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Spotify tools."""
    return [
        Tool(
            name="create_playlist",
            description="Create a new Spotify playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the playlist"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the playlist (optional)"
                    },
                    "public": {
                        "type": "boolean",
                        "description": "Whether the playlist is public (default: false)"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="search_tracks",
            description="Search for tracks on Spotify by name, artist, or other criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'artist:Queen track:Bohemian Rhapsody')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (1-50, default: 20)",
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add_tracks_to_playlist",
            description="Add tracks to an existing playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Spotify playlist ID"
                    },
                    "track_uris": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Spotify track URIs (e.g., ['spotify:track:...'])"
                    }
                },
                "required": ["playlist_id", "track_uris"]
            }
        ),
        Tool(
            name="remove_tracks_from_playlist",
            description="Remove tracks from an existing playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Spotify playlist ID"
                    },
                    "track_uris": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Spotify track URIs to remove (e.g., ['spotify:track:...'])"
                    }
                },
                "required": ["playlist_id", "track_uris"]
            }
        ),
        Tool(
            name="get_user_playlists",
            description="Get the current user's playlists",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of playlists to return (default: 50)",
                        "minimum": 1,
                        "maximum": 50
                    }
                }
            }
        ),
        Tool(
            name="get_playlist_tracks",
            description="Get all tracks from a specific playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Spotify playlist ID"
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        Tool(
            name="get_recommendations",
            description="Get track recommendations based on seed tracks, artists, or genres",
            inputSchema={
                "type": "object",
                "properties": {
                    "seed_tracks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of track IDs for recommendations (max 5 total seeds)"
                    },
                    "seed_artists": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of artist IDs for recommendations (max 5 total seeds)"
                    },
                    "seed_genres": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of genre names for recommendations (max 5 total seeds)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recommendations (1-100, default: 20)",
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            }
        ),
        Tool(
            name="find_duplicates",
            description="Find duplicate tracks in a playlist based on track name and artist",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Spotify playlist ID"
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        Tool(
            name="get_top_tracks",
            description="Get user's top tracks based on listening history. Returns tracks the user has listened to most frequently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of tracks to return (1-50, default: 20)",
                        "minimum": 1,
                        "maximum": 50
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time period: 'short_term' (~4 weeks), 'medium_term' (~6 months, default), 'long_term' (all time)",
                        "enum": ["short_term", "medium_term", "long_term"]
                    }
                }
            }
        ),
        Tool(
            name="create_curated_playlist_from_top_tracks",
            description="Create an intelligent curated playlist based on user's top tracks plus similar recommendations. Automatically gets top tracks, finds recommendations, creates playlist, and adds all tracks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_name": {
                        "type": "string",
                        "description": "Name for the new curated playlist"
                    },
                    "num_top_tracks": {
                        "type": "integer",
                        "description": "Number of user's top tracks to include (1-50, default: 20)",
                        "minimum": 1,
                        "maximum": 50
                    },
                    "num_recommendations": {
                        "type": "integer",
                        "description": "Number of recommended similar tracks to add (1-100, default: 30)",
                        "minimum": 1,
                        "maximum": 100
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time period for top tracks: 'short_term' (~4 weeks), 'medium_term' (~6 months, default), 'long_term' (all time)",
                        "enum": ["short_term", "medium_term", "long_term"]
                    },
                    "playlist_description": {
                        "type": "string",
                        "description": "Optional custom description for the playlist (auto-generated if not provided)"
                    },
                    "public": {
                        "type": "boolean",
                        "description": "Whether the playlist should be public (default: false)"
                    }
                },
                "required": ["playlist_name"]
            }
        ),
        # Phase 1 - Playlist Intelligence Tools
        Tool(
            name="get_playlist_stats",
            description="Get comprehensive statistics for a playlist including duration, genre breakdown, and average release year",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Spotify playlist ID"
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        Tool(
            name="merge_playlists",
            description="Merge multiple playlists into a new playlist with optional deduplication",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Spotify playlist IDs to merge"
                    },
                    "new_playlist_name": {
                        "type": "string",
                        "description": "Name for the new merged playlist"
                    },
                    "remove_duplicates": {
                        "type": "boolean",
                        "description": "Whether to remove duplicate tracks (default: true)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description for the new playlist (optional)"
                    },
                    "public": {
                        "type": "boolean",
                        "description": "Whether the playlist should be public (default: false)"
                    }
                },
                "required": ["playlist_ids", "new_playlist_name"]
            }
        ),
        Tool(
            name="compare_playlists",
            description="Compare two playlists to find shared tracks and unique tracks in each",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id_1": {
                        "type": "string",
                        "description": "First Spotify playlist ID"
                    },
                    "playlist_id_2": {
                        "type": "string",
                        "description": "Second Spotify playlist ID"
                    }
                },
                "required": ["playlist_id_1", "playlist_id_2"]
            }
        ),
        Tool(
            name="set_collaborative",
            description="Set the collaborative status of a playlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Spotify playlist ID"
                    },
                    "collaborative": {
                        "type": "boolean",
                        "description": "Whether the playlist should be collaborative"
                    }
                },
                "required": ["playlist_id", "collaborative"]
            }
        ),
        # Phase 1 - Artist Deep Dive Tools
        Tool(
            name="get_artist_discography",
            description="Get an artist's complete discography grouped by album type (albums, singles, compilations)",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_id": {
                        "type": "string",
                        "description": "Spotify artist ID"
                    },
                    "include_groups": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Album types to include: album, single, compilation, appears_on (default: album, single, compilation)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum albums per group (default: 50)",
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["artist_id"]
            }
        ),
        Tool(
            name="get_related_artists",
            description="Get artists related to a given artist based on Spotify's analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_id": {
                        "type": "string",
                        "description": "Spotify artist ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of related artists (max: 20, default: 20)",
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["artist_id"]
            }
        ),
        Tool(
            name="get_artist_top_tracks",
            description="Get an artist's top tracks by popularity",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_id": {
                        "type": "string",
                        "description": "Spotify artist ID"
                    },
                    "country": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 country code (default: US)"
                    }
                },
                "required": ["artist_id"]
            }
        ),
        # Phase 2 - Audio Analysis Tool
        Tool(
            name="get_audio_features",
            description="Get audio features (tempo/BPM, key, mode, danceability, acousticness, energy, valence, etc.) for a track from multiple sources (GetSongBPM, MusicBrainz, AcousticBrainz). Returns None if features unavailable. Coverage varies by track - popular tracks more likely to have data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "track_id": {
                        "type": "string",
                        "description": "Spotify track ID"
                    }
                },
                "required": ["track_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls from Claude."""
    
    try:
        if name == "create_playlist":
            result = spotify_client.create_playlist(
                name=arguments["name"],
                description=arguments.get("description", ""),
                public=arguments.get("public", False)
            )
            return [TextContent(
                type="text",
                text=f"✅ Created playlist: {result['name']}\n"
                     f"URL: {result['url']}\n"
                     f"ID: {result['playlist_id']}"
            )]
        
        elif name == "search_tracks":
            tracks = spotify_client.search_tracks(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            
            if not tracks:
                return [TextContent(type="text", text="No tracks found.")]
            
            result_text = f"Found {len(tracks)} track(s):\n\n"
            for i, track in enumerate(tracks, 1):
                result_text += (
                    f"{i}. {track['name']} by {track['artist']}\n"
                    f"   Album: {track['album']}\n"
                    f"   URI: {track['uri']}\n"
                    f"   URL: {track['url']}\n\n"
                )
            
            return [TextContent(type="text", text=result_text)]
        
        elif name == "add_tracks_to_playlist":
            result = spotify_client.add_tracks_to_playlist(
                playlist_id=arguments["playlist_id"],
                track_uris=arguments["track_uris"]
            )
            return [TextContent(
                type="text",
                text=f"✅ Added {result['tracks_added']} track(s) to playlist {result['playlist_id']}"
            )]

        elif name == "remove_tracks_from_playlist":
            result = spotify_client.remove_tracks_from_playlist(
                playlist_id=arguments["playlist_id"],
                track_uris=arguments["track_uris"]
            )
            return [TextContent(
                type="text",
                text=f"✅ Removed {result['tracks_removed']} track(s) from playlist {result['playlist_id']}"
            )]

        elif name == "get_user_playlists":
            playlists = spotify_client.get_user_playlists(
                limit=arguments.get("limit", 50)
            )
            
            if not playlists:
                return [TextContent(type="text", text="No playlists found.")]
            
            result_text = f"Found {len(playlists)} playlist(s):\n\n"
            for i, playlist in enumerate(playlists, 1):
                visibility = "Public" if playlist['public'] else "Private"
                result_text += (
                    f"{i}. {playlist['name']} ({visibility})\n"
                    f"   Description: {playlist['description']}\n"
                    f"   Tracks: {playlist['tracks_total']}\n"
                    f"   ID: {playlist['id']}\n"
                    f"   URL: {playlist['url']}\n\n"
                )
            
            return [TextContent(type="text", text=result_text)]
        
        elif name == "get_playlist_tracks":
            tracks = spotify_client.get_playlist_tracks(
                playlist_id=arguments["playlist_id"]
            )
            
            if not tracks:
                return [TextContent(type="text", text="Playlist is empty.")]
            
            result_text = f"Found {len(tracks)} track(s):\n\n"
            for i, track in enumerate(tracks, 1):
                result_text += (
                    f"{i}. {track['name']} by {track['artist']}\n"
                    f"   Album: {track['album']}\n"
                    f"   URI: {track['uri']}\n\n"
                )
            
            return [TextContent(type="text", text=result_text)]
        
        elif name == "get_recommendations":
            tracks = spotify_client.get_recommendations(
                seed_tracks=arguments.get("seed_tracks"),
                seed_artists=arguments.get("seed_artists"),
                seed_genres=arguments.get("seed_genres"),
                limit=arguments.get("limit", 20)
            )

            if not tracks:
                return [TextContent(type="text", text="No recommendations found.")]

            result_text = f"Found {len(tracks)} recommendation(s):\n\n"
            for i, track in enumerate(tracks, 1):
                result_text += (
                    f"{i}. {track['name']} by {track['artist']}\n"
                    f"   Album: {track['album']}\n"
                    f"   URI: {track['uri']}\n"
                    f"   URL: {track['url']}\n\n"
                )

            return [TextContent(type="text", text=result_text)]

        elif name == "find_duplicates":
            result = spotify_client.find_duplicates(
                playlist_id=arguments["playlist_id"]
            )

            if result["duplicate_count"] == 0:
                return [TextContent(
                    type="text",
                    text=f"✅ No duplicates found in playlist ({result['total_tracks']} total tracks)"
                )]

            result_text = (
                f"Found {result['duplicate_count']} duplicate track(s) "
                f"in playlist ({result['total_tracks']} total tracks):\n\n"
            )

            for i, dup in enumerate(result["duplicates"], 1):
                result_text += (
                    f"{i}. {dup['name']} by {dup['artist']}\n"
                    f"   Occurrences: {dup['occurrences']}\n"
                    f"   URIs: {', '.join(dup['uris'])}\n\n"
                )

            return [TextContent(type="text", text=result_text)]

        elif name == "get_top_tracks":
            tracks = spotify_client.get_top_tracks(
                limit=arguments.get("limit", 20),
                time_range=arguments.get("time_range", "medium_term")
            )

            if not tracks:
                return [TextContent(type="text", text="No top tracks found.")]

            time_labels = {
                "short_term": "last 4 weeks",
                "medium_term": "last 6 months",
                "long_term": "all time"
            }
            time_range = arguments.get("time_range", "medium_term")

            result_text = f"Your top {len(tracks)} tracks ({time_labels.get(time_range)}):\n\n"
            for i, track in enumerate(tracks, 1):
                result_text += (
                    f"{i}. {track['name']} by {track['artist']}\n"
                    f"   Album: {track['album']}\n"
                    f"   URI: {track['uri']}\n"
                    f"   URL: {track['url']}\n\n"
                )

            return [TextContent(type="text", text=result_text)]

        elif name == "create_curated_playlist_from_top_tracks":
            result = spotify_client.create_curated_playlist_from_top_tracks(
                playlist_name=arguments["playlist_name"],
                num_top_tracks=arguments.get("num_top_tracks", 20),
                num_recommendations=arguments.get("num_recommendations", 30),
                time_range=arguments.get("time_range", "medium_term"),
                playlist_description=arguments.get("playlist_description", ""),
                public=arguments.get("public", False)
            )

            result_text = (
                f"✅ Created curated playlist: {result['playlist_name']}\n\n"
                f"📊 Summary:\n"
                f"   - Total tracks added: {result['tracks_added']}\n"
                f"   - Your top tracks: {result['top_tracks_count']}\n"
                f"   - Recommendations: {result['recommendations_count']}\n\n"
                f"🔗 Playlist URL: {result['playlist_url']}\n\n"
                f"📝 Description: {result['description']}"
            )

            return [TextContent(type="text", text=result_text)]

        # Phase 1 - Playlist Intelligence Tools
        elif name == "get_playlist_stats":
            stats = playlist_logic.get_playlist_stats(arguments["playlist_id"])

            # Format genres for display
            genres_display = ", ".join(list(stats['genre_breakdown'].keys())[:5])

            result_text = (
                f"📊 Playlist Stats: {stats['playlist_name']}\n\n"
                f"📝 Description: {stats['playlist_description']}\n"
                f"👤 Owner: {stats['owner']}\n"
                f"🔓 Visibility: {'Public' if stats['public'] else 'Private'}\n"
                f"🤝 Collaborative: {'Yes' if stats['collaborative'] else 'No'}\n\n"
                f"📀 Total Tracks: {stats['total_tracks']}\n"
                f"⏱️  Duration: {stats['total_duration_formatted']}\n"
                f"📅 Avg Release Year: {stats['avg_release_year']}\n\n"
                f"🎸 Top Genres: {genres_display}\n\n"
            )

            if stats.get('earliest_track'):
                result_text += (
                    f"📜 Oldest Track: {stats['earliest_track']['name']} by {stats['earliest_track']['artist']} "
                    f"({stats['earliest_track']['release_date']})\n"
                )

            if stats.get('newest_track'):
                result_text += (
                    f"🆕 Newest Track: {stats['newest_track']['name']} by {stats['newest_track']['artist']} "
                    f"({stats['newest_track']['release_date']})\n"
                )

            return [TextContent(type="text", text=result_text)]

        elif name == "merge_playlists":
            result = playlist_logic.merge_playlists(
                playlist_ids=arguments["playlist_ids"],
                new_playlist_name=arguments["new_playlist_name"],
                remove_duplicates=arguments.get("remove_duplicates", True),
                description=arguments.get("description", ""),
                public=arguments.get("public", False)
            )

            source_list = "\n".join([
                f"   - {p['name']} ({p['track_count']} tracks)"
                for p in result['source_playlists']
            ])

            result_text = (
                f"✅ Merged Playlists Successfully!\n\n"
                f"🎵 New Playlist: {result['playlist_name']}\n"
                f"🔗 URL: {result['playlist_url']}\n\n"
                f"📊 Summary:\n"
                f"   - Tracks Added: {result['tracks_added']}\n"
                f"   - Duplicates Removed: {result['duplicates_removed']}\n\n"
                f"📋 Source Playlists:\n{source_list}"
            )

            return [TextContent(type="text", text=result_text)]

        elif name == "compare_playlists":
            result = playlist_logic.compare_playlists(
                playlist_id_1=arguments["playlist_id_1"],
                playlist_id_2=arguments["playlist_id_2"]
            )

            result_text = (
                f"🔍 Playlist Comparison\n\n"
                f"📋 Playlist 1: {result['playlist_1_name']}\n"
                f"📋 Playlist 2: {result['playlist_2_name']}\n\n"
                f"📊 Summary:\n"
                f"   - Shared Tracks: {result['shared_count']}\n"
                f"   - Unique to '{result['playlist_1_name']}': {result['unique_1_count']}\n"
                f"   - Unique to '{result['playlist_2_name']}': {result['unique_2_count']}\n\n"
            )

            if result['shared_count'] > 0:
                result_text += f"🤝 Shared Tracks (showing first 5):\n"
                for i, track in enumerate(result['shared_tracks'][:5], 1):
                    result_text += f"   {i}. {track['name']} by {track['artist']}\n"

            return [TextContent(type="text", text=result_text)]

        elif name == "set_collaborative":
            result = playlist_logic.set_collaborative(
                playlist_id=arguments["playlist_id"],
                collaborative=arguments["collaborative"]
            )

            status = "collaborative" if result['collaborative'] else "non-collaborative"
            result_text = (
                f"✅ Successfully updated playlist!\n\n"
                f"🎵 Playlist: {result['playlist_name']}\n"
                f"🤝 Status: Now {status}\n"
                f"📋 ID: {result['playlist_id']}"
            )

            return [TextContent(type="text", text=result_text)]

        # Phase 1 - Artist Deep Dive Tools
        elif name == "get_artist_discography":
            result = artist_logic.get_artist_discography(
                artist_id=arguments["artist_id"],
                include_groups=arguments.get("include_groups"),
                limit=arguments.get("limit", 50)
            )

            result_text = (
                f"🎸 Artist Discography: {result['artist_name']}\n\n"
                f"📊 Stats:\n"
                f"   - Total Releases: {result['total_releases']}\n"
                f"   - Popularity: {result['popularity']}/100\n"
                f"   - Followers: {result['followers']:,}\n"
                f"   - Genres: {', '.join(result['genres'][:5]) if result['genres'] else 'N/A'}\n\n"
            )

            if 'albums' in result and result['albums']:
                result_text += f"💿 Albums ({len(result['albums'])}):\n"
                for album in result['albums'][:5]:
                    result_text += f"   - {album['name']} ({album['release_date'][:4]})\n"
                if len(result['albums']) > 5:
                    result_text += f"   ... and {len(result['albums']) - 5} more\n"
                result_text += "\n"

            if 'singles' in result and result['singles']:
                result_text += f"💽 Singles ({len(result['singles'])}) - showing first 5:\n"
                for single in result['singles'][:5]:
                    result_text += f"   - {single['name']} ({single['release_date'][:4]})\n"
                if len(result['singles']) > 5:
                    result_text += f"   ... and {len(result['singles']) - 5} more\n"

            return [TextContent(type="text", text=result_text)]

        elif name == "get_related_artists":
            result = artist_logic.get_related_artists(
                artist_id=arguments["artist_id"],
                limit=arguments.get("limit", 20)
            )

            result_text = (
                f"🔗 Artists Related to: {result['original_artist']['name']}\n\n"
                f"Found {result['count']} related artist(s):\n\n"
            )

            for i, artist in enumerate(result['related_artists'], 1):
                genres = ", ".join(artist['genres'][:3]) if artist['genres'] else "N/A"
                result_text += (
                    f"{i}. {artist['name']}\n"
                    f"   Popularity: {artist['popularity']}/100\n"
                    f"   Genres: {genres}\n"
                    f"   Followers: {artist['followers']:,}\n"
                    f"   URL: {artist['url']}\n\n"
                )

            return [TextContent(type="text", text=result_text)]

        elif name == "get_artist_top_tracks":
            result = artist_logic.get_artist_top_tracks(
                artist_id=arguments["artist_id"],
                country=arguments.get("country", "US")
            )

            result_text = (
                f"⭐ Top Tracks: {result['artist_name']}\n"
                f"🌍 Country: {result['country']}\n\n"
                f"Found {result['count']} track(s):\n\n"
            )

            for i, track in enumerate(result['tracks'], 1):
                duration_min = track['duration_ms'] // 60000
                duration_sec = (track['duration_ms'] % 60000) // 1000
                result_text += (
                    f"{i}. {track['name']}\n"
                    f"   Album: {track['album']}\n"
                    f"   Popularity: {track['popularity']}/100\n"
                    f"   Duration: {duration_min}:{duration_sec:02d}\n"
                    f"   URL: {track['url']}\n\n"
                )

            return [TextContent(type="text", text=result_text)]

        # Phase 2 - Audio Analysis Tool
        elif name == "get_audio_features":
            features = await spotify_client.get_track_audio_features(
                track_id=arguments["track_id"]
            )

            if not features:
                return [TextContent(
                    type="text",
                    text="❌ No audio features available. The track may not have a preview URL."
                )]

            # Format for display
            key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            mode_names = {0: "minor", 1: "major"}

            result_text = (
                f"🎵 Audio Features (Track: {arguments['track_id']})\n\n"
                f"🎼 Musical Properties:\n"
                f"   - Tempo: {features['tempo']:.1f} BPM\n"
                f"   - Key: {key_names[features['key']]} {mode_names[features['mode']]}\n\n"
                f"📊 Energy & Mood:\n"
                f"   - Energy: {features['energy']:.2f} (0=calm, 1=intense)\n"
                f"   - Danceability: {features['danceability']:.2f} (0=low, 1=high)\n"
                f"   - Valence: {features['valence']:.2f} (0=sad, 1=happy)\n\n"
                f"ℹ️  Analysis Method: {features['analysis_method']}\n"
                f"⚠️  Note: Based on 30-second preview\n"
            )

            return [TextContent(type="text", text=result_text)]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server."""
    global spotify_client, playlist_logic, artist_logic

    # Get credentials from environment
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    cache_path = os.getenv("SPOTIFY_CACHE_PATH", ".spotify_cache")
    getsongbpm_api_key = os.getenv("GETSONGBPM_API_KEY")

    if not client_id or not client_secret:
        print("❌ Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set", file=sys.stderr)
        print("Create a .env file based on .env.example", file=sys.stderr)
        sys.exit(1)

    # Initialize Spotify client
    print("🎵 Initializing Spotify MCP Server...", file=sys.stderr)
    spotify_client = SpotifyClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        cache_path=cache_path,
        getsongbpm_api_key=getsongbpm_api_key
    )

    # Try to authenticate (will skip if credentials are invalid/dummy)
    try:
        spotify_client.authenticate()
    except Exception as e:
        print(f"⚠️  Authentication skipped: {e}", file=sys.stderr)
        print(f"ℹ️  Server will start but API calls will fail until authenticated", file=sys.stderr)

    # Initialize business logic
    playlist_logic = PlaylistLogic(spotify_client)
    artist_logic = ArtistLogic(spotify_client)

    print("✅ Spotify MCP Server ready!", file=sys.stderr)
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())