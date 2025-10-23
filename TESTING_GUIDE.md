# Testing Guide: Spotify MCP Server with Claude Desktop

**Last Updated**: 2025-10-22
**Server Version**: 0.1.0
**Status**: Production Ready ✅

---

## Prerequisites

Before testing, ensure you have:

- [x] Claude Desktop installed
- [x] Spotify MCP server installed (`pip install -e .`)
- [x] Spotify API credentials in `.env` file
- [x] Server authentication completed (`.spotify_cache` exists)
- [x] Server tested successfully in standalone mode

---

## Step 1: Add Spotify Server to Claude Desktop Config

### 1.1 Open Configuration File

**macOS**:
```bash
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows**:
```
notepad %APPDATA%\Claude\claude_desktop_config.json
```

### 1.2 Add Spotify MCP Server Entry

Add the following to your `mcpServers` section:

```json
{
  "mcpServers": {
    "spotify": {
      "command": "python",
      "args": [
        "/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/src/server.py"
      ],
      "env": {
        "SPOTIFY_CLIENT_ID": "4ffb56fb74d149189e1e0b17e31ef4f4",
        "SPOTIFY_CLIENT_SECRET": "b3a6e6b6d9684f529a21af1eeb2aeaa8",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIFY_CACHE_PATH": "/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/.spotify_cache"
      }
    }
  }
}
```

**Important Notes**:
- Use **absolute paths** (not relative paths like `~/` or `.`)
- Keep your existing MCP servers (zen, ghost-mcp, etc.)
- Add comma after previous server entry if needed

### 1.3 Complete Configuration Example

Here's how your full config should look with multiple servers:

```json
{
  "mcpServers": {
    "zen": {
      "command": "/Users/bmcmanus/Documents/zen-mcp-server/.zen_venv/bin/python",
      "args": [
        "/Users/bmcmanus/Documents/zen-mcp-server/server.py"
      ],
      "env": {
        "DISABLED_TOOLS": "consensus,planner,docgen,analyze,refactor,tracer,testgen,secaudit,precommit",
        "PORT": "3000"
      }
    },
    "ghost-mcp": {
      "command": "npx",
      "args": ["-y", "@fanyangmeng/ghost-mcp"],
      "env": {
        "GHOST_API_URL": "https://dispatches-from-the-llama.ghost.io",
        "GHOST_ADMIN_API_KEY": "68f849e99c30240001a6b2fa:b9193ee2fe411adf2a803dae115bbc1b861524741b89d56829a7d417f8d47d52",
        "GHOST_API_VERSION": "v5.0"
      }
    },
    "spotify": {
      "command": "python",
      "args": [
        "/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/src/server.py"
      ],
      "env": {
        "SPOTIFY_CLIENT_ID": "4ffb56fb74d149189e1e0b17e31ef4f4",
        "SPOTIFY_CLIENT_SECRET": "b3a6e6b6d9684f529a21af1eeb2aeaa8",
        "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:8888/callback",
        "SPOTIFY_CACHE_PATH": "/Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/.spotify_cache"
      }
    }
  }
}
```

### 1.4 Validate JSON Syntax

Before saving, verify your JSON is valid:

```bash
python -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

If valid, you'll see formatted JSON output. If invalid, you'll see an error message.

---

## Step 2: Restart Claude Desktop

**Important**: Claude Desktop only loads MCP servers on startup.

### 2.1 Quit Claude Desktop Completely

**macOS**:
- Press `Cmd + Q` (not just closing the window)
- Or: Right-click Claude in Dock → Quit

**Windows**:
- File → Exit
- Or: Right-click taskbar icon → Close

### 2.2 Verify Claude Desktop is Closed

```bash
# macOS - should return nothing
ps aux | grep -i "claude"
```

### 2.3 Relaunch Claude Desktop

Open Claude Desktop from Applications/Start Menu

---

## Step 3: Verify Server Connection

### 3.1 Check for Connection Indicators

When Claude Desktop starts:

1. **Look for MCP indicator** in the interface
2. **Check for Spotify tools** in available tools
3. **No error messages** should appear

### 3.2 Common Startup Issues

**Issue**: "Failed to connect to MCP server: spotify"

**Solutions**:
- Verify Python path is correct: `which python`
- Check server.py path is absolute
- Ensure .spotify_cache file exists
- Review Claude Desktop logs (see Troubleshooting section)

**Issue**: "Authentication failed"

**Solutions**:
- Verify credentials in config are correct
- Ensure .spotify_cache exists and is readable
- Try running server manually first: `python src/server.py`

---

## Step 4: Test Basic Functionality

### Test 1: List Your Playlists

**Prompt in Claude Desktop**:
```
Can you list my Spotify playlists?
```

**Expected Response**:
- Claude uses `list_user_playlists` tool
- Shows your playlists with track counts
- Returns playlist names and IDs

**Example Output**:
```
Found 5 playlists:

1. Mush '25 (Private)
   Description:
   Tracks: 26
   ID: 5E5mN3fCTmTaV40dVaOG83
   URL: https://open.spotify.com/playlist/5E5mN3fCTmTaV40dVaOG83

2. Workout (Private)
   ...
```

---

### Test 2: Search for Tracks

**Prompt**:
```
Search Spotify for "Bohemian Rhapsody" by Queen
```

**Expected Response**:
- Uses `search_tracks` tool
- Returns multiple results
- Shows track name, artist, album, URI

---

### Test 3: Create a Playlist

**Prompt**:
```
Create a new Spotify playlist called "Claude's Mix" with description "Created by Claude AI"
```

**Expected Response**:
- Uses `create_playlist` tool
- Returns playlist ID and URL
- Playlist appears in your Spotify account

**Verification**: Check your Spotify app to see the new playlist!

---

### Test 4: Add Tracks to Playlist

**Prompt**:
```
Add the song "Mr. Brightside" by The Killers to my "Claude's Mix" playlist
```

**Expected Response**:
- Uses `search_tracks` to find the song
- Uses `add_tracks_to_playlist` to add it
- Confirms track was added

**Verification**: Open the playlist in Spotify to see the track!

---

### Test 5: Find Duplicates

**Prompt**:
```
Check my "Mush '25" playlist for duplicate tracks
```

**Expected Response**:
- Uses `find_duplicates` tool
- Scans all tracks
- Reports any duplicates found (or confirms none)

---

### Test 6: Remove Tracks

**Prompt**:
```
Remove "Mr. Brightside" from my "Claude's Mix" playlist
```

**Expected Response**:
- Uses `remove_tracks_from_playlist` tool
- Confirms track was removed
- Track disappears from playlist

---

### Test 7: Get Playlist Tracks

**Prompt**:
```
Show me all the tracks in my "Workout" playlist
```

**Expected Response**:
- Uses `get_playlist_tracks` tool
- Lists all tracks with artist and album info

---

## Step 5: Advanced Testing

### Batch Operations Test

**Prompt**:
```
Create a playlist called "Rock Classics Test" and add 20 rock songs to it
```

**Expected Behavior**:
- Creates playlist
- Searches for rock songs
- Adds multiple tracks in one operation

### Multi-Step Workflow Test

**Prompt**:
```
I want to:
1. Create a new playlist called "Morning Vibes"
2. Find 10 upbeat pop songs
3. Add them to the playlist
4. Show me the final playlist
```

**Expected Behavior**:
- Claude executes each step in order
- Uses multiple tools in sequence
- Provides status updates

### Duplicate Detection Test

**Prompt**:
```
Find a playlist with duplicate tracks, then remove all duplicates
```

**Expected Behavior**:
- Scans playlists for duplicates
- Identifies duplicates
- Removes duplicate occurrences
- Confirms cleanup

---

## Step 6: Verify All 8 Tools Work

Test each tool systematically:

| # | Tool | Test Command | Expected Tool Used |
|---|------|--------------|-------------------|
| 1 | list_user_playlists | "List my playlists" | `list_user_playlists` |
| 2 | create_playlist | "Create playlist 'Test'" | `create_playlist` |
| 3 | search_tracks | "Search for Queen songs" | `search_tracks` |
| 4 | add_tracks_to_playlist | "Add a song to Test playlist" | `add_tracks_to_playlist` |
| 5 | get_playlist_tracks | "Show tracks in Test playlist" | `get_playlist_tracks` |
| 6 | get_recommendations | "Recommend songs like..." | `get_recommendations` ⚠️ |
| 7 | find_duplicates | "Find duplicates in Test" | `find_duplicates` |
| 8 | remove_tracks_from_playlist | "Remove a track from Test" | `remove_tracks_from_playlist` |

**Note**: `get_recommendations` may not work due to API limitations (see Known Issues)

---

## Troubleshooting

### View Claude Desktop Logs

**macOS**:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows**:
```
notepad %APPDATA%\Claude\Logs\mcp-server-spotify.log
```

### Common Issues and Solutions

#### Issue: Server Not Appearing in Claude Desktop

**Symptoms**: No Spotify tools visible

**Solutions**:
1. Check config file syntax (must be valid JSON)
2. Verify paths are absolute (not relative)
3. Restart Claude Desktop completely
4. Check logs for error messages

#### Issue: Authentication Errors

**Symptoms**: "Not authenticated" errors

**Solutions**:
1. Verify .spotify_cache exists:
   ```bash
   ls -la /Users/bmcmanus/Documents/my_docs/portfolio/spotify-mcp/.spotify_cache
   ```
2. Check credentials in config are correct
3. Try manual auth: `python src/server.py`
4. Regenerate cache if corrupted

#### Issue: Tools Work But Operations Fail

**Symptoms**: Tools execute but return errors

**Solutions**:
1. Check Spotify API quota/limits
2. Verify playlist IDs are correct
3. Ensure you have permission to modify playlists
4. Check track URIs are valid

#### Issue: Slow Response Times

**Symptoms**: Tools take >10 seconds to respond

**Possible Causes**:
- Large playlists (>500 tracks)
- Network latency
- Spotify API slowdown

**Solutions**:
- Use limit parameters to reduce data size
- Check internet connection
- Retry after a few minutes

---

## Performance Expectations

### Response Times (Typical)

| Operation | Tracks | Expected Time |
|-----------|--------|---------------|
| List playlists | N/A | <1 second |
| Search tracks | 20 | <1 second |
| Create playlist | N/A | <1 second |
| Add tracks | 1-10 | 1-2 seconds |
| Add tracks | 100+ | 2-5 seconds |
| Get playlist tracks | 50 | 1-2 seconds |
| Get playlist tracks | 500+ | 3-5 seconds |
| Find duplicates | 100 | 2-3 seconds |
| Remove tracks | 1-10 | 1-2 seconds |
| Remove tracks | 100+ | 2-5 seconds |

---

## Known Limitations

### 1. get_recommendations Tool

**Status**: ⚠️ May not work due to Spotify API access requirements

**Error**: HTTP 404 when calling recommendations endpoint

**Workaround**: Use search and manual curation instead

**Future Fix**: May require Spotify Developer Extended Quota

### 2. Rate Limiting

**Spotify Limits**: Not publicly documented, but exist

**Symptoms**: HTTP 429 errors

**Solution**: Wait a few minutes and retry

### 3. Playlist Size

**Maximum**: 10,000 tracks per playlist (Spotify limit)

**Batch Size**: 100 tracks per API request

**Impact**: Very large operations may take time

---

## Success Criteria

Your testing is successful if:

- ✅ All 7 working tools execute without errors
- ✅ Playlists created appear in your Spotify account
- ✅ Tracks added/removed correctly
- ✅ Search returns relevant results
- ✅ Duplicate detection works
- ✅ Batch operations (>100 tracks) complete successfully
- ✅ No authentication errors
- ✅ Response times are acceptable

---

## Next Steps After Testing

### If Everything Works ✅

1. Start using Spotify MCP server for real tasks!
2. Create custom playlists via Claude
3. Automate playlist maintenance
4. Explore advanced curation workflows

### If Issues Found ⚠️

1. Review troubleshooting section
2. Check Claude Desktop logs
3. Verify configuration
4. Test server manually: `python src/server.py`
5. Report issues with logs

---

## Example Conversation Flow

Here's a complete workflow example:

**You**: "I want to create a workout playlist with energetic songs"

**Claude**:
- Creates playlist "Workout Mix"
- Searches for high-energy tracks
- Adds 20 songs
- Shows you the final playlist

**You**: "Remove any slow songs and add 5 more upbeat tracks"

**Claude**:
- Analyzes current tracks
- Removes slower tracks
- Searches for more energetic songs
- Updates playlist

**You**: "Check for duplicates"

**Claude**:
- Scans playlist
- Reports any duplicates
- Offers to remove them

---

## Tips for Best Experience

1. **Be Specific**: Provide playlist IDs or exact names
2. **Start Small**: Test with small playlists first
3. **Use URIs**: When available, provide track URIs directly
4. **Be Patient**: Large operations take time
5. **Verify Changes**: Check Spotify app to confirm changes
6. **Keep .env Secure**: Never share your credentials

---

## Support

### Documentation
- Main README: `README.md`
- Security Standards: `SECURITY_STANDARDS.md`
- Project Standards: `PROJECT_STANDARDS.md`

### Test Results
- Test Results: `251022_1800_TEST_RESULTS_PHASE1.md`
- Batching Audit: `251022_1830_TASK22_BATCHING_AUDIT.md`

### Getting Help
- Check troubleshooting section
- Review Claude Desktop logs
- Verify configuration
- Test server standalone first

---

**Happy Testing!** 🎵

Your Spotify MCP Server is production-ready and waiting to manage your playlists!
