# Spotify MCP Server - Enhancement Roadmap

## Overview
This document outlines the planned enhancements to the Spotify MCP server, organized by priority and complexity.

---

## 🎯 Phase 1: Foundation & Quick Wins (Week 1-2)

### 1.1 Playlist Intelligence Tools ⚡ QUICK WIN
**Status:** Ready to implement
**Dependencies:** None (uses existing Spotify API)
**Complexity:** Low

**Features:**
- `get_playlist_stats` - Duration, track count, avg release year, genre breakdown
- `merge_playlists` - Combine multiple playlists with deduplication
- `compare_playlists` - Find unique/shared tracks between playlists
- `get_collaborative_status` - Check who can edit playlists

**MCP Tools to Add:**
```python
- get_playlist_stats(playlist_id)
- merge_playlists(playlist_ids[], name, remove_duplicates=True)
- compare_playlists(playlist_id_1, playlist_id_2)
- set_collaborative(playlist_id, collaborative=True)
```

**Estimated Time:** 4-6 hours

---

### 1.2 Artist Deep Dive Tools ⚡ QUICK WIN
**Status:** Ready to implement
**Dependencies:** None (uses existing Spotify API)
**Complexity:** Low-Medium

**Features:**
- Get artist's full discography with album groupings
- Find related artists
- Track artist evolution over time
- Get artist genres and popularity

**MCP Tools to Add:**
```python
- get_artist_discography(artist_id, include_groups=['album','single','compilation'])
- get_related_artists(artist_id, limit=20)
- get_artist_details(artist_id)
- get_artist_top_tracks(artist_id, country='US')
```

**Estimated Time:** 4-6 hours

---

## 🎸 Phase 2: Advanced Curation (Week 2-3)

### 2.1 Smart Recommendations System
**Status:** Design phase
**Dependencies:** Spotify API, possibly audio features if available
**Complexity:** Medium

**Features:**
- **Genre-boundary explorer** - Find tracks that blend genres
- **Decade traversal** - Similar sound across different eras
- **Deep cut digger** - Obscure tracks from popular artists

**Implementation Strategy:**
```python
# Genre Boundary Explorer
- Use get_recommendations() with multiple genre seeds
- Filter by artist popularity < 60 (less mainstream)
- Cross-reference with related artists from different genres

# Decade Traversal
- Get recommendations seeded by classic tracks
- Filter by release date ranges
- Use audio features for similarity matching

# Deep Cut Digger
- Get artist's full discography
- Filter out tracks with popularity < 40
- Exclude singles/greatest hits compilations
- Focus on album tracks 5+ minutes long
```

**MCP Tools to Add:**
```python
- find_genre_blends(genre_1, genre_2, limit=20)
- find_decade_similar(track_id, target_decade, limit=20)
- get_artist_deep_cuts(artist_id, popularity_threshold=40)
```

**Estimated Time:** 8-12 hours

---

### 2.2 Setlist Generator 🎭
**Status:** Design phase
**Dependencies:** Spotify API, audio features (if available)
**Complexity:** Medium-High

**Features:**
- DJ sets with smooth transitions (tempo/key matching)
- Concert-style setlists (opener → climax → closer arc)
- Festival lineup simulators

**Implementation Strategy:**
```python
# DJ Set Builder
- Analyze tempo, key, energy of tracks
- Use harmonic mixing rules (Camelot wheel)
- Build transition chains with minimal BPM jumps
- Ensure energy flow (gradual increases/decreases)

# Concert Setlist
- Opener: mid-high energy, crowd-pleasers
- Build: escalating energy, deep cuts mixed in
- Peak: highest energy, biggest hits
- Encore: emotional closer or final energy burst

# Festival Simulator
- Mix multiple artists
- Time-slot aware (early acts vs headliners)
- Genre progression throughout day
```

**MCP Tools to Add:**
```python
- create_dj_set(seed_tracks[], duration_minutes, transition_style='smooth')
- create_concert_setlist(artist_id, duration_minutes, include_deep_cuts=True)
- create_festival_lineup(artist_ids[], duration_hours, style='progressive')
```

**Audio Features Needed:**
- tempo (BPM)
- key (musical key)
- energy (0-1)
- danceability (0-1)
- valence (mood, 0-1)

**Challenge:** Audio features API may be deprecated. Need to test availability.

**Estimated Time:** 12-16 hours

---

## 🔌 Phase 3: External Integrations (Week 3-4)

### 3.1 MusicBrainz Integration 🎵
**Status:** Research required
**Dependencies:** MusicBrainz API
**Complexity:** Medium

**API Info:**
- Free, open-source music database
- No API key required
- Rate limit: ~1 req/sec
- Python library: `musicbrainzngs`

**Features:**
- Enhanced metadata (recording dates, labels, producers)
- Find rare releases and B-sides
- Track remaster vs original versions
- Get recording history and versions

**Implementation:**
```python
# Install: pip install musicbrainzngs

# Features
- search_musicbrainz(artist, track) -> recording_id, release_info
- get_track_versions(track_uri) -> list of remasters, editions
- get_recording_metadata(track_uri) -> detailed info
- find_rare_releases(artist_id) -> B-sides, limited editions
```

**MCP Tools to Add:**
```python
- get_track_metadata_musicbrainz(track_uri)
- find_track_versions(track_uri)
- get_rare_releases(artist_name)
```

**Estimated Time:** 8-10 hours

---

### 3.2 Genius Lyrics Integration 📝
**Status:** Research required
**Dependencies:** Genius API (requires free API key)
**Complexity:** Medium

**API Info:**
- Free tier available with rate limits
- Requires API key (sign up at genius.com/api-clients)
- Python library: `lyricsgenius`

**Features:**
- Fetch lyrics for tracks
- Analyze lyrical themes
- Create playlists based on lyrical content
- Search by lyrics

**Implementation:**
```python
# Install: pip install lyricsgenius

# Features
- Get lyrics for Spotify track
- Analyze lyrics for themes (love, politics, etc.)
- Search by lyric snippets
- Generate playlists by lyrical mood/theme
```

**MCP Tools to Add:**
```python
- get_track_lyrics(track_uri)
- analyze_lyrics_theme(track_uri) -> tags, sentiment
- search_by_lyrics(lyric_snippet)
- create_playlist_by_theme(theme, limit=50)
```

**Estimated Time:** 6-8 hours

---

## 📊 Implementation Priority Matrix

| Feature | Impact | Complexity | Priority | Phase |
|---------|--------|------------|----------|-------|
| Playlist Stats | High | Low | 🔥 HIGH | 1 |
| Artist Discography | High | Low | 🔥 HIGH | 1 |
| Collaborative Manager | Medium | Low | 🟡 MEDIUM | 1 |
| Smart Recommendations | High | Medium | 🔥 HIGH | 2 |
| Deep Cut Digger | High | Medium | 🔥 HIGH | 2 |
| Setlist Generator | High | High | 🟡 MEDIUM | 2 |
| MusicBrainz Integration | Medium | Medium | 🟢 LOW | 3 |
| Genius Integration | Medium | Medium | 🟢 LOW | 3 |

---

## 🏗️ Architecture Changes

### New Dependencies to Add
```toml
[project.dependencies]
# Existing
spotipy = ">=2.23.0"
python-dotenv = ">=1.0.0"
mcp = ">=0.1.0"

# New
musicbrainzngs = ">=0.7.1"  # MusicBrainz
lyricsgenius = ">=3.0.1"    # Genius
```

### New Environment Variables
```bash
# .env additions
MUSICBRAINZ_APP_NAME="Spotify-MCP-Server"
MUSICBRAINZ_APP_VERSION="1.0"
MUSICBRAINZ_CONTACT="your.email@example.com"

GENIUS_API_KEY="your_genius_api_key"
```

### File Structure
```
spotify-mcp/
├── src/
│   ├── server.py                    # Main MCP server
│   ├── spotify_client.py            # Spotify API wrapper
│   ├── musicbrainz_client.py        # NEW: MusicBrainz wrapper
│   ├── genius_client.py             # NEW: Genius wrapper
│   ├── setlist_generator.py         # NEW: Setlist algorithms
│   └── recommendation_engine.py     # NEW: Smart recommendations
├── tests/
│   ├── test_musicbrainz.py         # NEW
│   ├── test_genius.py              # NEW
│   └── test_setlist.py             # NEW
└── docs/
    └── ENHANCEMENT_ROADMAP.md       # This file
```

---

## 🚀 Next Steps

### Immediate Actions (This Week)
1. ✅ Create this roadmap document
2. ⏳ Implement Phase 1.1 - Playlist Intelligence Tools
3. ⏳ Implement Phase 1.2 - Artist Deep Dive Tools
4. ⏳ Test audio features API availability

### Week 2
1. Implement Smart Recommendations
2. Begin Setlist Generator prototype
3. Set up MusicBrainz/Genius API accounts

### Week 3-4
1. Complete Setlist Generator
2. Integrate MusicBrainz
3. Integrate Genius
4. Comprehensive testing

---

## 📝 Notes & Considerations

### Audio Features API Deprecation
- Need to verify if audio features are still available
- If deprecated, setlist generator may need alternative approach
- Consider third-party audio analysis libraries (librosa, essentia)

### Rate Limiting Strategy
- Spotify: Built-in retry logic ✅
- MusicBrainz: 1 req/sec - add rate limiter
- Genius: Check free tier limits

### Testing Strategy
- Unit tests for each new client
- Integration tests for MCP tools
- Manual testing with real playlists

### Documentation
- Update README with new features
- Create examples for each new tool
- Document external API setup requirements

---

## 🎯 Success Metrics

After implementation, we should be able to:
- ✅ Generate intelligent DJ sets with smooth transitions
- ✅ Discover obscure tracks from favorite artists
- ✅ Find genre-blending tracks
- ✅ Access enhanced track metadata from MusicBrainz
- ✅ Analyze lyrics and create themed playlists
- ✅ Get comprehensive artist discographies
- ✅ Manage collaborative playlists
- ✅ Generate detailed playlist statistics

---

**Last Updated:** 2025-10-23
**Version:** 1.0
**Author:** Claude Code + Brian McManus
