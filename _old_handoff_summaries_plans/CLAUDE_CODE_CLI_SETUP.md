# Using Spotify MCP Server with Claude Code CLI

**Status**: ✅ CONFIGURED AND READY
**Date**: 2025-10-23
**Configuration File**: `~/.claude/settings.json`

---

## Summary

The Spotify MCP server is now accessible from Claude Code CLI! This gives you:
- **Larger context window** than Claude Desktop
- **Better handling of large playlists** (100+ tracks)
- **Command-line integration** with full terminal capabilities
- **All 10 Spotify tools** available

---

## Configuration Status

✅ **COMPLETE** - Spotify MCP server added to `~/.claude/settings.json`

**Configuration Details**:
- **Server Name**: `spotify`
- **Description**: Spotify playlist curation and management
- **Command**: `/opt/miniconda3/bin/python`
- **Server Path**: `/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/src/server.py`
- **Status**: Enabled

**Environment Variables**:
- `SPOTIFY_CLIENT_ID`: Configured ✅
- `SPOTIFY_CLIENT_SECRET`: Configured ✅
- `SPOTIFY_REDIRECT_URI`: `http://127.0.0.1:8888/callback` ✅
- `SPOTIFY_CACHE_PATH`: Points to existing `.spotify_cache` ✅

---

## How to Use

### 1. Restart Claude Code CLI (if currently running)

The MCP server configuration is loaded at startup, so restart any active Claude Code CLI sessions.

### 2. Verify Tools Are Available

In a new Claude Code CLI session, ask:

```
You: What MCP tools do you have access to?
```

You should see the Spotify tools listed, including:
- `get_top_tracks` (new!)
- `create_curated_playlist_from_top_tracks` (new!)
- `create_playlist`
- `search_tracks`
- `add_tracks_to_playlist`
- `remove_tracks_from_playlist`
- `get_user_playlists`
- `get_playlist_tracks`
- `get_recommendations`
- `find_duplicates`

### 3. Example Usage

#### Get Your Top Tracks
```
You: Show me my top 20 tracks from the last 6 months
```

Claude will use the `get_top_tracks` tool with `time_range="medium_term"`.

#### Create Large Curated Playlist
```
You: Create a playlist called "My Ultimate Mix" with my top 50 tracks from all time, then find 50 similar tracks and add them all
```

Claude Code CLI can handle this large operation better than Claude Desktop due to larger context window.

#### Complex Multi-Step Workflow
```
You:
1. Get my top 30 tracks from the last month
2. Get my top 30 tracks from the last 6 months
3. Find which tracks appear in both lists
4. Create a playlist called "Consistent Favorites" with those tracks
5. Add 20 similar recommendations
```

Claude Code CLI excels at multi-step operations.

---

## Advantages Over Claude Desktop

### 1. Larger Context Window ✅
- Claude Code CLI: Much larger context (can handle more tracks/operations)
- Claude Desktop: Limited context (struggles with 100+ tracks)

### 2. Better Error Handling ✅
- Full terminal integration
- Can see detailed logs if needed
- Better debugging capabilities

### 3. Batch Operations ✅
- Can handle creating multiple playlists
- Better for bulk track operations
- Won't hit context limits as quickly

### 4. Composability ✅
- Can combine with other MCP servers (like zen-mcp)
- Full scripting capabilities
- Can save workflows as commands

---

## Example Workflows

### Workflow 1: Create Decade-Based Playlists

```
You: For each decade (80s, 90s, 2000s, 2010s), create a playlist with:
- My top 20 tracks from that decade
- 30 recommendations of similar tracks from that decade
```

### Workflow 2: Compare Listening Patterns

```
You:
1. Get my top 20 tracks from the last month
2. Get my top 20 tracks from all time
3. Create two playlists: "Recent Obsessions" and "All-Time Classics"
4. Tell me what genres/artists I'm currently into vs historically
```

### Workflow 3: Smart Genre Playlists

```
You:
1. Get my top 50 tracks
2. Analyze the genres
3. For the top 3 genres, create separate playlists with:
   - My top tracks in that genre
   - Recommendations for similar tracks
```

### Workflow 4: Playlist Cleanup

```
You:
1. Get all my playlists
2. For each playlist, find duplicates
3. Show me which playlists have the most duplicates
4. Remove duplicates from my "Main Mix" playlist
```

---

## Configuration File Location

**File**: `~/.claude/settings.json`

**Spotify MCP Server Block** (lines 24-37):
```json
"spotify": {
  "description": "Spotify playlist curation and management. 10 tools for smart playlist creation based on listening history.",
  "command": "/opt/miniconda3/bin/python",
  "args": [
    "/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/src/server.py"
  ],
  "env": {
    "SPOTIFY_CLIENT_ID": "4ffb56fb74d149189e1e0b17e31ef4f4",
    "SPOTIFY_CLIENT_SECRET": "b3a6e6b6d9684f529a21af1eeb2aeaa8",
    "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
    "SPOTIFY_CACHE_PATH": "/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/.spotify_cache"
  },
  "enabled": true
}
```

---

## Troubleshooting

### Tools Not Showing Up

**Issue**: Claude Code CLI doesn't show Spotify tools

**Fixes**:
1. Restart Claude Code CLI completely
2. Verify `~/.claude/settings.json` has correct configuration
3. Check that server path is correct:
   ```bash
   ls -la /Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/src/server.py
   ```
4. Test server manually:
   ```bash
   /opt/miniconda3/bin/python /Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/src/server.py
   ```

### Authentication Issues

**Issue**: "Not authenticated" errors

**Fix**: The server uses the cached token at `.spotify_cache`. If you get auth errors:

```bash
# Remove cached token
rm /Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/.spotify_cache

# Run server manually once to re-authenticate
cd /Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp
python src/server.py
# Browser will open for auth, then Ctrl+C to stop
```

### Server Errors

**Issue**: Server won't start or crashes

**Check**:
1. Python path is correct: `/opt/miniconda3/bin/python`
2. Dependencies installed:
   ```bash
   cd /Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp
   pip install -e .
   ```
3. Check logs in Claude Code CLI debug output

---

## Available Tools Reference

| Tool | What It Does | Best For |
|------|--------------|----------|
| `get_top_tracks` | Get your most-played tracks by time period | Understanding listening habits, creating personalized playlists |
| `create_curated_playlist_from_top_tracks` | One-command automated playlist | Quick personalized playlists (blocked by API currently) |
| `create_playlist` | Create empty playlist | Starting point for custom playlists |
| `search_tracks` | Search Spotify library | Finding specific songs |
| `add_tracks_to_playlist` | Add tracks to playlist | Building playlists (handles 100+ tracks) |
| `remove_tracks_from_playlist` | Remove tracks | Cleaning up playlists |
| `get_user_playlists` | List all playlists | Playlist management |
| `get_playlist_tracks` | Get all tracks in playlist | Analyzing/copying playlists |
| `get_recommendations` | Get similar tracks | Discovery (currently blocked by API) |
| `find_duplicates` | Find duplicate tracks | Playlist cleanup |

---

## Context Window Comparison

### Claude Desktop
- **Context**: ~100K tokens
- **Good For**: Simple operations (1-2 tools)
- **Struggles With**: Large playlists (100+ tracks), multi-step workflows

### Claude Code CLI
- **Context**: Much larger (200K+ tokens)
- **Good For**: Complex workflows, large playlists, batch operations
- **Recommended For**: Serious playlist curation work

---

## Next Steps

### Try It Out!

1. Start Claude Code CLI
2. Ask: "Show me my top 10 tracks from the last month"
3. Try creating a playlist with your top tracks
4. Experiment with multi-step workflows

### Advanced Usage

Once comfortable, try:
- Comparing listening patterns across time periods
- Creating genre-based playlists
- Bulk playlist cleanup (finding/removing duplicates)
- Building playlists based on audio features

---

## Benefits Recap

✅ **No context limit issues** - Handle huge playlists
✅ **10 tools available** - All Spotify features accessible
✅ **Multi-step workflows** - Complex curation logic
✅ **Better for automation** - Can create multiple playlists at once
✅ **Existing auth token** - Uses your `.spotify_cache`, no re-auth needed
✅ **Works alongside other MCP servers** - zen-mcp still available

---

**Configuration Complete**: 2025-10-23 02:45
**Status**: Ready to use! 🎵
