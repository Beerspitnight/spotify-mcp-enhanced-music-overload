# Spotify-mcp-Overload

A Model Context Protocol (MCP) server that enables Claude Code CLI or Desktop to interact with Spotify for playlist curation and management, among other goodies.

### Rock Out with The Following Features:
- 🧠 Smart playlist curation 
- 🛤️ Deep track identification 
- 🕺 Song analysis (bpm, danceability, etc.)
- 🚀 Discovery & Recommendation (w/ seed validation)

## Features

### Core Playlist Management
- ✅ Create playlists
- ✅ Search for tracks
- ✅ Add tracks to playlists (with automatic rate limit handling)
- ✅ Remove tracks from playlists (with automatic rate limit handling)
- ✅ Get user playlists
- ✅ Get playlist tracks

### Smart Curation & Discovery
- ✅ **Get your top tracks** - See what you listen to most (by time period)
- ✅ Get track recommendations (with seed validation)
- ✅ **Create curated playlists** - Automated playlist based on your top tracks + recommendations
- ✅ Find duplicate tracks in playlists

### Audio Analysis (Phase 2 - Complete! 🎵)
- **Get audio features** - BPM, musical key, energy, danceability, valence, acousticness
- **Multi-source data** - GetSongBPM API + MusicBrainz/AcousticBrainz waterfall
-  **Smart caching** - 30-day TTL, positive/negative caching to reduce API calls
-  **No preview required** - Works with ISRC lookups, not dependent on 30s previews
-  **Coverage**: ~70-90% for popular/older tracks, ~20-40% for recent releases (2020+)

### Reliability Features
-  Automatic retry on Spotify API rate limits (HTTP 429)
-  Batch processing for large operations (100+ tracks)
-  Async execution - Audio analysis runs in thread pool (no blocking)

## Prerequisites

- Python 3.10 or higher
- Spotify account
- Spotify Developer App (for API credentials)

## Setup

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create app"
3. Fill in:
   - **App name**: "spotify-mcp-enhanced-music-overload" 
   - **App description**: "MCP server for Claude integration"
   - **Redirect URI**: `http://127.0.0.1:8888/callback`
   - **APIs used**: Check "Web API"
4. Accept terms and click "Save"
5. Click "Settings" to view your **Client ID** and **Client Secret**

### 2. Install Dependencies

```bash
cd spotify-mcp
pip install -e .
```

This installs all required dependencies including audio features support.

### 3. Get Your Free GetSongBPM API Key (Optional but Recommended)

For enhanced audio features coverage:
1. Go to [GetSongBPM API](https://getsongbpm.com/api)
2. Sign up for a free API key

### 4. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your credentials:
# SPOTIFY_CLIENT_ID=your_actual_client_id
# SPOTIFY_CLIENT_SECRET=your_actual_client_secret
# GETSONGBPM_API_KEY=your_api_key (optional but recommended)
```

### 5. First Run Authentication

The first time you run the server, it will:
1. Open your browser automatically
2. Ask you to authorize the application
3. Redirect to `http://127.0.0.1:8888/callback`
4. Save the authentication token locally in `.spotify_cache`

**Note**: The redirect URL will show an error in your browser (this is normal). The authentication token is extracted from the URL automatically.

After the first run, the token is cached and you won't need to authenticate again unless it expires.

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "spotify": {
      "command": "/opt/miniconda3/bin/python",
      "args": ["/absolute/path/to/spotify-mcp/src/server.py"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIFY_CACHE_PATH": "/absolute/path/to/.spotify_cache"
      }
    }
  }
}
```

**Important**:
- Use **absolute path to Python** (e.g., `/opt/miniconda3/bin/python` or `/usr/bin/python3`) - find it with `which python`
- Use absolute paths for all file paths, not relative paths
- Replace `/absolute/path/to/spotify-mcp` with your actual path
- Replace `your_client_id` and `your_client_secret` with your actual credentials

Restart Claude Desktop after adding the configuration.

**Tip**: See `TESTING_GUIDE.md` for comprehensive Claude Desktop setup instructions.

### With Claude Code CLI

**Recommended for large playlists and complex workflows!** Claude Code CLI has a much larger context window than Claude Desktop, making it ideal for:
- Creating playlists with 100+ tracks
- Multi-step curation workflows
- Batch operations across multiple playlists

Add to your settings file:

**Location**: `~/.claude/settings.json`

```json
{
  "mcpServers": {
    "spotify": {
      "description": "Spotify playlist curation and management. 10 tools for smart playlist creation.",
      "command": "/opt/miniconda3/bin/python",
      "args": ["/absolute/path/to/spotify-mcp/src/server.py"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIFY_CACHE_PATH": "/absolute/path/to/.spotify_cache"
      },
      "enabled": true
    }
  }
}
```

**Important**:
- Use **absolute path to Python** - find it with `which python`
- Use absolute paths for all file paths
- Restart Claude Code CLI after adding configuration
- See `CLAUDE_CODE_CLI_SETUP.md` for detailed setup guide

## Example Conversations with Claude

Once configured, you can ask Claude things like:

### Create a Playlist
```
You: Create a workout playlist called "Morning Energy" with an upbeat description

Claude: [Uses create_playlist tool]
✅ Created playlist: Morning Energy
URL: https://open.spotify.com/playlist/abc123
```

### Search and Add Tracks
```
You: Find some high-energy electronic music and add the top 5 tracks to my Morning Energy playlist

Claude: [Uses search_tracks and add_tracks_to_playlist tools]
Found 20 tracks. Adding top 5 to your playlist...
✅ Added 5 tracks to playlist
```

### Get Recommendations
```
You: Based on my current "Psychedelic" playlist, recommend 10 similar songs

Claude: [Uses get_playlist_tracks and get_recommendations tools]
Here are 10 recommendations based on your playlist...
```

### List Your Playlists
```
You: Show me all my playlists

Claude: [Uses get_user_playlists tool]
Found 15 playlists:
1. Psychedelic (Public) - 25 tracks
2. Dub Reggae (Private) - 40 tracks
...
```

### Remove Tracks
```
You: Remove all tracks by "Black Sabbath" from my workout playlist

Claude: [Uses get_playlist_tracks and remove_tracks_from_playlist tools]
Found 3 tracks by Black Sabbath. Removing...
✅ Removed 3 tracks from playlist
```

### Find Duplicates
```
You: Find duplicate songs in my "Favorites" playlist

Claude: [Uses find_duplicates tool]
Found 5 duplicate tracks:
1. "I Was On A Mountain" by Hot Water Music - 2 occurrences
2. "Suffer" by Bad Religion - 2 occurrences
...
```

### Get Your Top Tracks
```
You: Show me my top 20 most-played tracks from the last 6 months

Claude: [Uses get_top_tracks tool]
Your top 20 tracks (last 6 months):
1. Saboteurs by Dave Hause
2. Web in Front by Archers Of Loaf
3. Cabin Fever by Slomosa
...
```

### Create Curated Playlist
```
You: Create a personalized playlist based on my top tracks from the last month, including similar recommendations

Claude: [Uses create_curated_playlist_from_top_tracks tool]
✅ Created curated playlist: Personalized Mix

📊 Summary:
   - Total tracks added: 50
   - Your top tracks: 20
   - Recommendations: 30

🔗 Playlist URL: https://open.spotify.com/playlist/abc123
```

### Get Audio Features 🎵
```
You: Analyze the audio features for Hot Water Music's "I Was On A Mountain"

Claude: [Uses search_tracks and get_audio_features tools]
🎵 Audio Features (The Mighty Mighty Bosstones - I Hope I Never Lose My Wallet)

🎼 Musical Properties:
   - Tempo: 102.0 BPM
   - Key: A minor
   - Time Signature: 4/4

📊 Energy & Mood:
   - Danceability: 0.440 (moderate)
   - Acousticness: 0.010 (very electric)

ℹ️  Data Source: GetSongBPM API
```

**Use Cases**:
- Find tracks with similar BPM for DJ mixes and workout playlists
- Detect musical key for harmonic mixing (DJs)
- Filter tracks by energy/danceability for themed playlists
- Analyze mood (valence) and acousticness for curation
- Build setlists with consistent tempo/energy flow

## Available Tools

| Tool | Description | Features |
|------|-------------|----------|
| `create_playlist` | Create a new Spotify playlist | - |
| `search_tracks` | Search for tracks by name, artist, album, etc. | - |
| `add_tracks_to_playlist` | Add tracks to an existing playlist | Auto-batching (100 tracks/batch), Rate limit retry |
| `remove_tracks_from_playlist` | Remove tracks from a playlist | Auto-batching (100 tracks/batch), Rate limit retry |
| `get_user_playlists` | List all user playlists | - |
| `get_playlist_tracks` | Get all tracks from a playlist | Pagination handling |
| `get_recommendations` | Get track recommendations based on seeds | Seed validation (requires at least one seed) |
| `find_duplicates` | Find duplicate tracks in a playlist | Case-insensitive matching |
| **`get_top_tracks`** | **Get user's most-played tracks** | **Time periods: 4 weeks, 6 months, all time** |
| **`create_curated_playlist_from_top_tracks`** | **Auto-create playlist from top tracks + recommendations** | **One-command automation** |
| **`get_audio_features`** 🎵 | **Analyze track audio (BPM, key, energy, etc.)** | **Multi-source (GetSongBPM, MusicBrainz, AcousticBrainz), 30-day cache, ~70-90% coverage** |
| **`get_playlist_stats`** | **Get comprehensive playlist statistics** | **Duration, genre breakdown, avg release year** |
| **`merge_playlists`** | **Merge multiple playlists with deduplication** | **Auto-dedup, custom descriptions** |
| **`compare_playlists`** | **Find shared and unique tracks** | **Venn diagram analysis** |
| **`set_collaborative`** | **Toggle playlist collaborative status** | **Enable/disable collaboration** |
| **`get_artist_discography`** | **Get artist's complete discography** | **Albums, singles, compilations** |
| **`get_related_artists`** | **Find similar artists** | **Spotify similarity algorithm** |
| **`get_artist_top_tracks`** | **Get artist's most popular tracks** | **Country-specific results** |

**Total**: 18 tools available

## Reliability Features

### Automatic Rate Limit Handling
The server automatically handles Spotify API rate limits (HTTP 429):
- Reads the `Retry-After` header from Spotify
- Waits the specified time
- Retries the operation once
- Logs rate limit events to stderr

This makes bulk operations (adding/removing 100+ tracks) reliable and resilient.

### Batch Processing
Operations that modify playlists automatically batch requests:
- Max 100 tracks per API call (Spotify's limit)
- Handles playlists of any size
- Maintains operation atomicity within batches

### Input Validation
- `get_recommendations` validates that at least one seed is provided before making API calls
- Prevents unnecessary API requests with clear error messages

## Troubleshooting

### "Authentication failed" error
- Verify your Client ID and Client Secret are correct
- Make sure the Redirect URI in your Spotify app settings matches exactly: `http://127.0.0.1:8888/callback`
- Delete `.spotify_cache` and try authenticating again

### "No module named 'mcp'" error
- Run `pip install -e .` from the project directory
- Make sure you're using Python 3.10+

### "spawn python ENOENT" error in Claude Desktop
- Use the **full path** to your Python interpreter in the config
- Find it with: `which python` or `which python3`
- Example: `"command": "/opt/miniconda3/bin/python"` instead of `"command": "python"`

### Claude Desktop doesn't show Spotify tools
- Verify the JSON configuration syntax is correct
- Check that all paths are absolute (not relative)
- Use full Python path (see "spawn python ENOENT" above)
- Restart Claude Desktop after configuration changes
- Check Claude Desktop logs for errors

### Browser doesn't open for authentication
- The first run requires a browser. Run the server manually once:
  ```bash
  cd spotify-mcp/src
  python server.py
  ```
- After authentication succeeds, the token is cached for Claude Desktop/CLI

### "No audio features available" message
- Track may be too recent (post-2020 has ~20-40% coverage)
- Older/classic tracks have better coverage (~70-90%)
- GetSongBPM API key improves coverage significantly
- MusicBrainz/AcousticBrainz stopped collecting data in 2022
- Features are cached for 30 days after lookup

## Security Notes

- **Never commit** your `.env` file or `.spotify_cache` file to version control
- The `.spotify_cache` file contains your access and refresh tokens
- Client Secret should be kept private
- This server is designed for personal use on your local machine

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest
```

### Project Structure
```
spotify-mcp/
├── src/
│   ├── features/                  # Audio features module (Phase 2)
│   │   ├── __init__.py
│   │   ├── models.py             # Pydantic data models
│   │   ├── cache.py              # File-based caching (30-day TTL)
│   │   ├── service.py            # Multi-source orchestration
│   │   └── clients/              # API clients
│   │       ├── getsongbpm.py     # GetSongBPM API client
│   │       ├── musicbrainz.py    # MusicBrainz ISRC lookup
│   │       └── acousticbrainz.py # AcousticBrainz features
│   ├── clients/
│   │   └── spotify_client.py      # Spotify API wrapper
│   ├── logic/
│   │   ├── playlist_logic.py      # Playlist intelligence
│   │   └── artist_logic.py        # Artist deep dive
│   └── server.py                  # Main MCP server
├── pyproject.toml                 # Dependencies
├── .env.example                   # Example environment variables
└── README.md
```

## Credits
Access from https://getsongbpm.com/ via their free API provides song-analysis including beats-per-minute.  Thanks, GetSongBPM.com

## License

MIT License - feel free to modify and distribute. Make it better.  Make it cooler.

## Contributing

Issues and pull requests welcome! This implementation includes core features and can be extended with:
- More Spotify API endpoints
- Advanced playlist curation algorithms
- User library management
- Collaborative filtering
- Setlist generators (DJ sets, concert setlists)
- Additional audio analysis sources

## Credits

This project is built on top of excellent open-source tools and APIs:

### Core Dependencies
- **[MCP (Model Context Protocol)](https://modelcontextprotocol.io/)** - Anthropic's protocol for LLM integrations
- **[Spotipy](https://spotipy.readthedocs.io/)** - Python library for Spotify Web API
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation using Python type annotations

### Audio Features Data Sources
- **[GetSongBPM API](https://getsongbpm.com/api)** - Primary source for tempo, key, and audio features - mucho gracias
- **[MusicBrainz](https://musicbrainz.org/)** - Open music encyclopedia for ISRC lookups - killer
- **[AcousticBrainz](https://acousticbrainz.org/)** - Crowd-sourced acoustic analysis database (archived 2022) - very cool

### Development Tools
- **[httpx](https://www.python-httpx.org/)** - Modern async HTTP client
- **[tenacity](https://tenacity.readthedocs.io/)** - Retry logic with exponential backoff
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - Environment variable management

### Special Thanks
My mom and Dad.
Claude in all his different clothes

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotipy Library](https://spotipy.readthedocs.io/)
- [GetSongBPM API Docs](https://getsongbpm.com/api)
- [MusicBrainz API](https://musicbrainz.org/doc/MusicBrainz_API)
