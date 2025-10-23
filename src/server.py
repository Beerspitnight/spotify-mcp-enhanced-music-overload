"""Spotify MCP Server - Exposes Spotify API as MCP tools."""

import asyncio
import os
import sys
from typing import Any
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from spotify_client import SpotifyClient


# Load environment variables
load_dotenv()

# Initialize MCP server
server = Server("spotify-mcp")

# Global Spotify client (initialized in main)
spotify_client: SpotifyClient = None


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
    global spotify_client
    
    # Get credentials from environment
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    cache_path = os.getenv("SPOTIFY_CACHE_PATH", ".spotify_cache")
    
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
        cache_path=cache_path
    )
    
    # Authenticate (will open browser on first run)
    try:
        spotify_client.authenticate()
    except Exception as e:
        print(f"❌ Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)
    
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