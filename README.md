# Spotify MCP Server

A Model Context Protocol (MCP) server that enables Claude to interact with Spotify for playlist curation and management.

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

### Reliability Features
- ✅ Automatic retry on Spotify API rate limits (HTTP 429)
- ✅ Batch processing for large operations (100+ tracks)

## Prerequisites

- Python 3.10 or higher
- Spotify account
- Spotify Developer App (for API credentials)

## Setup

### 1. Get Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create app"
3. Fill in:
   - **App name**: "My Spotify MCP Server" (or your preferred name)
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

Or with uv:
```bash
uv pip install -e .
```

### 3. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Spotify credentials
# SPOTIFY_CLIENT_ID=your_actual_client_id
# SPOTIFY_CLIENT_SECRET=your_actual_client_secret
```

### 4. First Run Authentication

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
You: Based on my current "Chill Vibes" playlist, recommend 10 similar songs

Claude: [Uses get_playlist_tracks and get_recommendations tools]
Here are 10 recommendations based on your playlist...
```

### List Your Playlists
```
You: Show me all my playlists

Claude: [Uses get_user_playlists tool]
Found 15 playlists:
1. Morning Energy (Public) - 25 tracks
2. Chill Vibes (Private) - 40 tracks
...
```

### Remove Tracks
```
You: Remove all tracks by "The Killers" from my workout playlist

Claude: [Uses get_playlist_tracks and remove_tracks_from_playlist tools]
Found 3 tracks by The Killers. Removing...
✅ Removed 3 tracks from playlist
```

### Find Duplicates
```
You: Find duplicate songs in my "Favorites" playlist

Claude: [Uses find_duplicates tool]
Found 5 duplicate tracks:
1. "Mr. Brightside" by The Killers - 2 occurrences
2. "Take On Me" by A-ha - 2 occurrences
...
```

### Get Your Top Tracks
```
You: Show me my top 20 most-played tracks from the last 6 months

Claude: [Uses get_top_tracks tool]
Your top 20 tracks (last 6 months):
1. Saboteurs by Dave Hause
2. Web in Front by Archers Of Loaf
3. Sweetness by Jimmy Eat World
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

**Total**: 10 tools available

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
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   └── spotify_client.py  # Spotify API wrapper
├── pyproject.toml         # Dependencies
├── .env.example           # Example environment variables
└── README.md
```

## License

MIT License - feel free to modify and distribute.

## Contributing

Issues and pull requests welcome! This is a minimal implementation that can be extended with:
- More Spotify API endpoints
- Advanced playlist curation algorithms
- Audio feature analysis
- User library management
- Collaborative filtering

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotipy Library](https://spotipy.readthedocs.io/)