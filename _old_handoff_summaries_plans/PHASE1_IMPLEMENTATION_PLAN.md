# Phase 1 Implementation Plan - APPROVED

**Status:** ✅ Ready to Execute
**Date:** 2025-10-23
**Validated By:** Zen Chat (Gemini 2.5 Pro) + Claude Code Analysis

---

## Executive Summary

Phase 1 will add **7 new MCP tools** to the Spotify server, organized into two categories:
- **Playlist Intelligence** (4 tools): Stats, merge, compare, collaborative management
- **Artist Deep Dive** (3 tools): Discography, related artists, top tracks

**Critical Discovery:** Spotify deprecated the Audio Features API on November 27, 2024. This **does not affect Phase 1** but requires a strategic pivot for Phase 2.

**Estimated Implementation Time:** 8-12 hours
**Dependencies:** None (uses existing Spotify Web API only)

---

## Architecture Changes

### Directory Structure Refactor

```
spotify-mcp/
├── src/
│   ├── server.py                    # MCP handlers (thin routing layer)
│   ├── clients/
│   │   ├── __init__.py
│   │   └── spotify_client.py        # Auth, retries, raw Spotify API calls
│   ├── logic/
│   │   ├── __init__.py
│   │   ├── playlist_logic.py        # Playlist intelligence business logic
│   │   └── artist_logic.py          # Artist discovery business logic
│   └── __init__.py
├── tests/
│   ├── fixtures/                    # JSON fixtures from real API responses
│   │   ├── playlist_stats_fixture.json
│   │   ├── artist_discography_fixture.json
│   │   └── ...
│   ├── test_playlist_logic.py
│   ├── test_artist_logic.py
│   └── conftest.py                  # Shared fixtures and mocks
├── pyproject.toml
├── ENHANCEMENT_ROADMAP.md
└── PHASE1_IMPLEMENTATION_PLAN.md    # This document
```

### Key Architectural Principles

1. **Separation of Concerns**
   - `clients/spotify_client.py`: HOW to talk to Spotify (auth, retries, fetching)
   - `logic/*.py`: WHAT to do with the data (calculate, merge, analyze)
   - `server.py`: Routing and MCP protocol handling

2. **Dependency Injection**
   - Logic classes receive `spotify_client` instance in constructor
   - Enables easy mocking for tests
   - Clear dependency graph

3. **Batch Optimization**
   - Collect all IDs first, then batch fetch (50 items per API call)
   - Reduces API calls from N to ceil(N/50)
   - Example: Getting genres for 100 artists = 2 API calls instead of 100

---

## Implementation Order

### Step 1: Refactor Existing Structure (1-2 hours)
1. Create `src/clients/` directory
2. Move `src/spotify_client.py` to `src/clients/spotify_client.py`
3. Create `src/logic/` directory with `__init__.py`
4. Update imports in `src/server.py`
5. Test that existing 10 tools still work

### Step 2: Implement Playlist Logic (3-4 hours)
**File:** `src/logic/playlist_logic.py`

**Methods to implement:**
```python
class PlaylistLogic:
    def __init__(self, spotify_client: SpotifyClient):
        self.client = spotify_client

    def get_playlist_stats(self, playlist_id: str) -> Dict[str, Any]:
        """Calculate comprehensive playlist statistics."""
        # 1. Get playlist metadata + tracks
        # 2. Batch-fetch track details (50 per call)
        # 3. Calculate duration, avg year
        # 4. Collect unique artist IDs
        # 5. Batch-fetch artist details for genres (50 per call)
        # 6. Return structured stats

    def merge_playlists(
        self,
        playlist_ids: List[str],
        new_name: str,
        remove_duplicates: bool = True,
        description: str = "",
        public: bool = False
    ) -> Dict[str, Any]:
        """Merge multiple playlists into one."""
        # 1. Fetch all tracks from all playlists
        # 2. Deduplicate by URI if requested
        # 3. Create new playlist
        # 4. Add tracks in batches
        # 5. Return merge summary

    def compare_playlists(
        self,
        playlist_id_1: str,
        playlist_id_2: str
    ) -> Dict[str, Any]:
        """Compare two playlists."""
        # 1. Fetch both playlists' tracks
        # 2. Create URI sets
        # 3. Find intersection and differences
        # 4. Return comparison results

    def set_collaborative(
        self,
        playlist_id: str,
        collaborative: bool
    ) -> Dict[str, Any]:
        """Toggle collaborative status."""
        # Use sp.playlist_change_details()
```

### Step 3: Implement Artist Logic (2-3 hours)
**File:** `src/logic/artist_logic.py`

**Methods to implement:**
```python
class ArtistLogic:
    def __init__(self, spotify_client: SpotifyClient):
        self.client = spotify_client

    def get_artist_discography(
        self,
        artist_id: str,
        include_groups: List[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get complete artist discography."""
        # 1. Fetch artist details
        # 2. Iterate through album_type groups (album, single, compilation)
        # 3. Handle pagination
        # 4. Return grouped discography

    def get_related_artists(
        self,
        artist_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get related artists."""
        # Use sp.artist_related_artists()

    def get_artist_top_tracks(
        self,
        artist_id: str,
        country: str = 'US'
    ) -> List[Dict[str, Any]]:
        """Get artist's top tracks."""
        # Use sp.artist_top_tracks()
```

### Step 4: Update Server Handlers (2-3 hours)
**File:** `src/server.py`

**Changes:**
1. Import logic classes
2. Initialize in `main()`:
   ```python
   playlist_logic = PlaylistLogic(spotify_client)
   artist_logic = ArtistLogic(spotify_client)
   ```

3. Add 7 new tools to `list_tools()` with `outputSchema`

4. Add 7 new handlers in `call_tool()` with structured responses:
   ```python
   elif name == "get_playlist_stats":
       stats = playlist_logic.get_playlist_stats(arguments["playlist_id"])

       # Format text summary
       summary = f"📊 Stats for '{stats['playlist_name']}':\n..."

       return [
           types.StructuredContent(type="structured", structured=stats),
           types.TextContent(type="text", text=summary)
       ]
   ```

### Step 5: Testing (2-3 hours)
1. **Prototype first tool** (get_artist_discography)
   - Run against real Spotify API
   - Capture real response
   - Save as fixture

2. **Write fixture-based tests** for remaining tools
   - Mock `spotify_client` methods
   - Return fixture data
   - Assert business logic correctness

3. **Integration test**
   - Run full server
   - Test all 7 new tools via MCP
   - Verify structured + text responses

---

## MCP Tool Definitions

### 1. get_playlist_stats

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_id": {"type": "string", "description": "Spotify playlist ID"}
  },
  "required": ["playlist_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_name": {"type": "string"},
    "total_tracks": {"type": "integer"},
    "total_duration_minutes": {"type": "number"},
    "average_release_year": {"type": "integer"},
    "genre_breakdown": {
      "type": "object",
      "additionalProperties": {"type": "integer"}
    },
    "earliest_track": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "artist": {"type": "string"},
        "release_date": {"type": "string"}
      }
    },
    "newest_track": {"type": "object"}
  }
}
```

### 2. merge_playlists

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_ids": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of playlist IDs to merge"
    },
    "new_playlist_name": {"type": "string"},
    "remove_duplicates": {"type": "boolean", "default": true},
    "description": {"type": "string"},
    "public": {"type": "boolean", "default": false}
  },
  "required": ["playlist_ids", "new_playlist_name"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_id": {"type": "string"},
    "playlist_url": {"type": "string"},
    "tracks_added": {"type": "integer"},
    "duplicates_removed": {"type": "integer"},
    "source_playlists": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "track_count": {"type": "integer"}
        }
      }
    }
  }
}
```

### 3. compare_playlists

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_id_1": {"type": "string"},
    "playlist_id_2": {"type": "string"}
  },
  "required": ["playlist_id_1", "playlist_id_2"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_1_name": {"type": "string"},
    "playlist_2_name": {"type": "string"},
    "shared_count": {"type": "integer"},
    "unique_1_count": {"type": "integer"},
    "unique_2_count": {"type": "integer"},
    "shared_tracks": {"type": "array"},
    "unique_to_playlist_1": {"type": "array"},
    "unique_to_playlist_2": {"type": "array"}
  }
}
```

### 4. set_collaborative

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "playlist_id": {"type": "string"},
    "collaborative": {"type": "boolean"}
  },
  "required": ["playlist_id", "collaborative"]
}
```

### 5-7. Artist Tools
(Similar schema structure for `get_artist_discography`, `get_related_artists`, `get_artist_top_tracks`)

---

## Response Pattern: Structured + Text

All tools return **both** structured data and human-readable text:

```python
return [
    types.StructuredContent(
        type="structured",
        structured={
            # Validated against outputSchema
            "playlist_name": "My Playlist",
            "total_tracks": 42,
            # ...
        }
    ),
    types.TextContent(
        type="text",
        text="📊 Stats for 'My Playlist':\n  - 42 tracks\n  - 2h 15m duration\n..."
    )
]
```

**Benefits:**
- AI agents can parse structured data
- Humans get readable summaries
- Backwards compatible

---

## Error Handling Pattern

Return structured errors instead of raising exceptions:

```python
try:
    result = playlist_logic.get_playlist_stats(playlist_id)
    # ... format response
except Exception as e:
    return [
        types.StructuredContent(
            type="structured",
            structured={
                "error_type": type(e).__name__,
                "message": str(e)
            }
        ),
        types.TextContent(
            type="text",
            text=f"❌ Error ({type(e).__name__}): {str(e)}"
        )
    ]
```

---

## Critical Discovery: Audio Features API Deprecated

### What Happened
- **Date:** November 27, 2024
- **Affected:** `audio_features`, `audio_analysis`, recommendations endpoints
- **Impact:** Returns 403 errors for new applications
- **No replacement** announced by Spotify

### What's Blocked
- ❌ **Phase 2 Setlist Generator** - Requires tempo, key, energy for DJ-style transitions
- ⚠️ **Phase 2 Smart Recommendations** - Partially blocked (audio feature filtering won't work)

### Strategic Pivot for Phase 2

**Recommended Approach: Hybrid Strategy**

1. **Accelerate Phase 3 Features** (Lyrics + Metadata)
   - Move Genius integration forward
   - Move MusicBrainz integration forward
   - These add unique value and don't depend on deprecated APIs

2. **Re-scope Setlist Generator** to `create_themed_playlist`
   - Use metadata-driven heuristics:
     - **Popularity arc:** Start popular → deep cuts → biggest hits
     - **Album chronology:** Follow release timeline
     - **Energy proxy:** Use genre tags (punk = high, ambient = low)
     - **Decade flow:** Traverse through musical eras
   - Still valuable without audio features
   - Honest about limitations

3. **Update Roadmap**
   - Mark Audio Features-dependent features as "Blocked"
   - Reprioritize remaining Phase 2/3 features
   - Document workarounds

---

## Testing Strategy

### 1. Prototype Phase (First Tool)
```python
# Run against real API
python test_artist_discography_live.py

# Capture response
import json
response = artist_logic.get_artist_discography("artist_id")
with open("tests/fixtures/artist_discography.json", "w") as f:
    json.dump(response, f, indent=2)
```

### 2. Fixture-Based Testing (Remaining Tools)
```python
# tests/test_playlist_logic.py
import pytest
from unittest.mock import Mock
import json

@pytest.fixture
def mock_spotify_client():
    client = Mock()
    # Load fixture
    with open("tests/fixtures/playlist_tracks.json") as f:
        client.get_playlist_tracks.return_value = json.load(f)
    return client

def test_get_playlist_stats(mock_spotify_client):
    logic = PlaylistLogic(mock_spotify_client)
    stats = logic.get_playlist_stats("test_id")

    assert stats["total_tracks"] == 42
    assert stats["playlist_name"] == "Test Playlist"
    # ...
```

---

## Success Metrics

After Phase 1 implementation:
- ✅ 7 new MCP tools available
- ✅ Modular architecture ready for Phase 2/3
- ✅ Comprehensive test coverage
- ✅ Structured + text responses for all tools
- ✅ Documentation updated

---

## Next Steps

1. **Get approval to proceed**
2. **Execute implementation** (Steps 1-5)
3. **Update ENHANCEMENT_ROADMAP.md** with Audio Features pivot
4. **Demonstrate new features** with example use cases

---

**Ready to begin implementation? Y/N**
