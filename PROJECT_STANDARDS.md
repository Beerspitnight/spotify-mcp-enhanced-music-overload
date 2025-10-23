--- START OF FILE PROJECT_STANDARDS.md ---
# Project: Spotify Curation MCP Server (Homer)

**Vision**: Allow Claude/Client to create and curate Spotify playlists via a dedicated Tool Server.
**Goal (MVP)**: Implement Spotify Auth + Expose Core Playlist Tools (Create, Search, Add, List).

## 1. Project Architecture & Stack

| Component | Standard | Location/Reference | Note |
|:---|:---|:---|:---|
| **Language** | Python 3.10+ | Synchronous Python | Server runs via `python src/server.py`. |
| **Architecture** | Tool Server Pattern | `src/server.py` | Handles all MCP tool definition and calling. |
| **Spotify API** | spotipy Library | `src/spotify_client.py` | Encapsulates all API logic and token caching. |
| **Auth/Cache** | Authorization Code Flow | `.spotify_cache` file | Auth persists using `spotipy`'s token caching file. **NO DATABASE**. |
| **Code Structure** | Modular | `src/` directory | `spotify_client.py` handles API, `server.py` handles MCP. |
| **Testing** | Unit Tests (MCP Logic) | - | **90% coverage minimum** for all logic outside of `spotipy` calls. |

## 2. Core Constitutional Rules

- **Workflow**: Context → Tool Definition → Tool Calling. Feature-branch Git workflow.
- **Tools**: List all available tools in the final output.
- **Logic**: All Spotify API/Playlist logic must be encapsulated within `src/spotify_client.py`.

### Violations (Halt/No Merge)

- **Critical (Halt)**: Hardcoded secrets, missing auth flow, logic outside of `src/`.
- **High (No Merge)**: Missing type hints, lack of error handling in tool functions, synchronous I/O blocking.

## 3. Tool Reference

**8 Tools Exposed (Phase 1 Complete):**
1.  `get_user_playlists` - List all user playlists
2.  `create_playlist` - Create a new playlist
3.  `search_tracks` - Search for tracks by query
4.  `add_tracks_to_playlist` - Add tracks to playlist (with rate limit handling)
5.  `remove_tracks_from_playlist` - Remove tracks from playlist (with rate limit handling)
6.  `get_playlist_tracks` - Get all tracks from a playlist
7.  `get_recommendations` - Get track recommendations (with seed validation)
8.  `find_duplicates` - Find duplicate tracks in a playlist

## 4. File Naming Conventions
All file names will follow the following convention: YYMMDD_HHMM_HANDOFF_SUMMARY_DESCRIPTION.md
-  MM is rounded to the closest quarter-hour.

## 5. Coding Patterns & Best Practices

### 5.1 Rate Limit Handling Pattern

For operations that may hit Spotify API rate limits, use the `_with_retry` helper:

```python
def _with_retry(self, fn: Callable, *args, **kwargs) -> Any:
    """Execute Spotify API call with automatic retry on rate limit."""
    try:
        return fn(*args, **kwargs)
    except spotipy.SpotifyException as e:
        if e.http_status == 429:  # Rate limited
            retry_after = int(e.headers.get("Retry-After", 1))
            print(f"⚠️  Rate limited. Waiting {retry_after} seconds...", file=sys.stderr)
            time.sleep(retry_after)
            return fn(*args, **kwargs)  # Single retry
        raise
```

**Usage**:
```python
# Instead of: self.sp.playlist_add_items(playlist_id, batch)
# Use:
self._with_retry(self.sp.playlist_add_items, playlist_id, batch)
```

**Apply to**: Bulk operations (add_tracks, remove_tracks) that may exceed rate limits.

### 5.2 Input Validation Pattern

Validate inputs before making API calls to provide better error messages:

```python
# Validate at least one seed provided
if not any([seed_tracks, seed_artists, seed_genres]):
    raise ValueError(
        "At least one of seed_tracks, seed_artists, or seed_genres "
        "must be provided for recommendations."
    )
```

**Benefits**:
- Prevents unnecessary API calls
- Clearer error messages for users
- Faster failure detection

### 5.3 Batch Processing Pattern

For operations with API limits (e.g., 100 tracks per request):

```python
batch_size = 100
for i in range(0, len(track_uris), batch_size):
    batch = track_uris[i:i + batch_size]
    self._with_retry(self.sp.playlist_add_items, playlist_id, batch)
```

**Standard**: Always batch operations that modify playlists.

### 5.4 Error Handling Pattern

Wrap Spotify API calls with try/except:

```python
try:
    results = self.sp.recommendations(...)
    # Process results
except spotipy.SpotifyException as e:
    raise RuntimeError(f"Spotify API error: {e}")
```

**Standard**: Convert `spotipy.SpotifyException` to `RuntimeError` with context.

### 5.5 Type Hints

All functions must have complete type hints:

```python
def get_recommendations(
    self,
    seed_tracks: Optional[List[str]] = None,
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    limit: int = 20,
    **kwargs
) -> List[Dict[str, Any]]:
```

**Required imports**: `from typing import Optional, List, Dict, Any, Callable`

### 5.6 Documentation

All methods require docstrings with:
- Summary
- Args section
- Returns section
- Raises section (if applicable)
- Note section for special behavior

```python
def add_tracks_to_playlist(
    self,
    playlist_id: str,
    track_uris: List[str]
) -> Dict[str, Any]:
    """
    Add tracks to a playlist with automatic rate limit handling.

    Args:
        playlist_id: Spotify playlist ID
        track_uris: List of Spotify track URIs

    Returns:
        Dict with success status and number of tracks added

    Note:
        Automatically retries if rate limited (HTTP 429)
    """
```

---
