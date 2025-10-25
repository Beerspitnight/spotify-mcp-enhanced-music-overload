# Phase 2: AudioFeatureAnalyzer Implementation Plan

**Date:** 2025-10-24
**Status:** Ready for Implementation
**Goal:** Implement local audio analysis to replace deprecated Spotify Audio Features API

---

## Executive Summary

This plan details the implementation of `AudioFeatureAnalyzer` for the Spotify MCP server, incorporating architectural best practices and addressing critical async/blocking concerns identified during brainstorming.

**Key Decisions:**
- ✅ New `src/analysis/` directory for domain-specific analysis modules
- ✅ Async wrapper with `asyncio.to_thread` to prevent event loop blocking
- ✅ Cache versioning for algorithm updates
- ✅ Custom exceptions for better error handling
- ✅ Optional dependency management via `[audio]` extra
- ✅ Multi-layered testing strategy with fixtures

---

## 1. Architecture & File Structure

### Directory Structure (NEW)
```
spotify-mcp/
├── src/
│   ├── analysis/               # NEW: Domain-specific analysis
│   │   ├── __init__.py
│   │   ├── audio_analyzer.py   # AudioFeatureAnalyzer class
│   │   └── exceptions.py       # Custom exceptions
│   ├── clients/
│   │   └── spotify_client.py   # MODIFIED: Add get_track_audio_features()
│   ├── logic/
│   │   ├── playlist_logic.py
│   │   └── artist_logic.py
│   └── server.py               # MODIFIED: Add get_audio_features tool
├── tests/
│   ├── fixtures/
│   │   └── audio/              # NEW: Test audio clips
│   ├── test_audio_analyzer.py  # NEW: Unit tests
│   └── test_spotify_client.py  # MODIFIED: Integration tests
├── .audio_cache/               # NEW: Git-ignored cache directory
└── pyproject.toml              # MODIFIED: Add optional [audio] deps
```

**Rationale:**
- `src/analysis/` - Clear separation: clients retrieve, analysis transforms, logic orchestrates
- Scalable for future analysis modules (lyrics, sentiment, etc.)
- Follows existing modular architecture pattern

---

## 2. Custom Exceptions

### File: `src/analysis/exceptions.py`

```python
"""Custom exceptions for audio analysis operations."""


class AudioAnalysisError(Exception):
    """Base exception for audio analysis failures."""
    pass


class PreviewDownloadError(AudioAnalysisError):
    """Failed to download the audio preview URL."""
    pass


class AudioProcessingError(AudioAnalysisError):
    """Failed to process the audio file with librosa."""
    pass
```

**Error Handling Strategy:**
- Return `None`: Only when `preview_url` is missing (expected scenario)
- Raise `PreviewDownloadError`: Network failures, 404s, timeouts
- Raise `AudioProcessingError`: Librosa failures, corrupt audio
- Convert to `RuntimeError` at boundary (SpotifyClient) per project standards

---

## 3. Core AudioFeatureAnalyzer Class

### File: `src/analysis/audio_analyzer.py`

```python
"""Local audio feature extraction from Spotify preview URLs."""

from typing import Optional, Dict, Any
import asyncio
import json
import os
import tempfile
import requests
import librosa
import numpy as np

from .exceptions import PreviewDownloadError, AudioProcessingError


class AudioFeatureAnalyzer:
    """
    Local audio feature extraction from Spotify preview URLs.
    Replaces deprecated Spotify Audio Features API.

    Features Extracted:
        - tempo (BPM): float
        - key: int (0-11, C to B)
        - mode: int (0=minor, 1=major)
        - energy: float (0.0-1.0)
        - danceability: float (0.0-1.0) [estimated]
        - valence: float (0.0-1.0) [estimated from spectral features]
    """

    ANALYZER_VERSION = "1.0.0"  # Bump when algorithm changes

    def __init__(self, cache_dir: str = ".audio_cache"):
        """
        Initialize analyzer with optional caching directory.

        Args:
            cache_dir: Directory for caching analysis results
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    async def analyze_preview(
        self,
        preview_url: str,
        track_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze 30-second Spotify preview for audio features (async).

        Args:
            preview_url: Spotify MP3 preview URL
            track_id: Spotify track ID for caching

        Returns:
            Dict with audio features, or None if preview unavailable

        Raises:
            PreviewDownloadError: If download fails
            AudioProcessingError: If librosa analysis fails

        Note:
            Uses asyncio.to_thread to avoid blocking event loop.
            Analysis runs in separate thread pool.
        """
        if not preview_url:
            return None

        # Check cache (with version validation)
        cache_path = os.path.join(self.cache_dir, f"{track_id}.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                data = json.load(f)
                if data.get("analyzer_version") == self.ANALYZER_VERSION:
                    return data

        # Download preview (run in thread to avoid blocking)
        try:
            response = await asyncio.to_thread(
                requests.get,
                preview_url,
                timeout=10
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise PreviewDownloadError(
                f"Failed to download preview: {preview_url}"
            ) from e

        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        try:
            # Run CPU-bound analysis in thread pool
            features = await asyncio.to_thread(self._extract_features, tmp_path)

            # Add metadata
            features["analyzer_version"] = self.ANALYZER_VERSION
            features["track_id"] = track_id
            features["preview_url"] = preview_url

            # Cache results
            with open(cache_path, 'w') as f:
                json.dump(features, f, indent=2)

            return features

        except Exception as e:
            raise AudioProcessingError(
                f"Librosa failed to process audio for track {track_id}"
            ) from e

        finally:
            # Clean up temporary file
            os.unlink(tmp_path)

    def _extract_features(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract audio features using librosa (synchronous, CPU-bound).

        Args:
            audio_path: Path to MP3 file

        Returns:
            Dict with extracted features

        Note:
            This is a blocking function. Should only be called via
            asyncio.to_thread() to avoid blocking the event loop.
        """
        # Load audio (librosa defaults to mono, 22050 Hz)
        y, sr = librosa.load(audio_path, sr=22050)

        # 1. TEMPO (BPM)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

        # 2. KEY DETECTION (using chroma features)
        # Use Constant-Q Transform chroma for better resolution
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

        # Sum chroma across time and find dominant pitch class
        chroma_sum = np.sum(chroma, axis=1)
        key = int(np.argmax(chroma_sum))  # 0-11 (C, C#, D, ..., B)

        # 3. MODE (major/minor detection)
        # IMPROVED: Use chroma pattern analysis
        # Major chords have stronger 3rd (4 semitones up)
        # Minor chords have stronger minor 3rd (3 semitones up)
        major_third_idx = (key + 4) % 12
        minor_third_idx = (key + 3) % 12

        major_strength = chroma_sum[major_third_idx]
        minor_strength = chroma_sum[minor_third_idx]

        mode = 1 if major_strength > minor_strength else 0

        # 4. ENERGY (RMS energy normalized)
        rms = librosa.feature.rms(y=y)[0]
        energy = float(np.mean(rms))

        # Normalize to 0-1 range (use percentile to handle outliers)
        max_rms = np.percentile(rms, 95)
        if max_rms > 0:
            energy = min(energy / max_rms, 1.0)

        # 5. DANCEABILITY (estimated from beat strength and regularity)
        beat_strength = librosa.onset.onset_strength(y=y, sr=sr)

        # Regularity: std deviation of beat intervals
        if len(beats) > 1:
            beat_intervals = np.diff(beats)
            regularity = 1.0 - min(np.std(beat_intervals) / np.mean(beat_intervals), 1.0)
        else:
            regularity = 0.0

        # Strength: average onset strength at beat locations
        if len(beats) > 0:
            beat_strengths = beat_strength[beats]
            strength = np.mean(beat_strengths) / (np.max(beat_strength) + 1e-6)
        else:
            strength = 0.0

        danceability = float((regularity + strength) / 2.0)

        # 6. VALENCE (estimated from spectral features)
        # Brighter, higher-frequency music tends to sound happier
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

        # Normalize centroid to 0-1 (using typical range)
        # Typical range: 500-4000 Hz
        mean_centroid = np.mean(spectral_centroid)
        valence = float((mean_centroid - 500) / 3500)
        valence = max(0.0, min(1.0, valence))  # Clamp to [0, 1]

        return {
            "tempo": float(tempo),
            "key": key,
            "mode": mode,
            "energy": energy,
            "danceability": danceability,
            "valence": valence,
            "analysis_method": "librosa",
            "preview_based": True
        }
```

---

## 4. SpotifyClient Integration

### File: `src/clients/spotify_client.py` (MODIFICATIONS)

```python
# At top of file, add conditional import
try:
    from analysis.audio_analyzer import AudioFeatureAnalyzer
    from analysis.exceptions import AudioAnalysisError
    AUDIO_ANALYSIS_ENABLED = True
except ImportError:
    AudioFeatureAnalyzer = None
    AUDIO_ANALYSIS_ENABLED = False


class SpotifyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8888/callback",
        cache_path: str = ".spotify_cache"
    ):
        # ... existing init code ...

        # Initialize audio analyzer (optional feature)
        if AUDIO_ANALYSIS_ENABLED:
            self.audio_analyzer = AudioFeatureAnalyzer()
        else:
            self.audio_analyzer = None

    async def get_track_audio_features(
        self,
        track_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get audio features for a track using local analysis.

        Args:
            track_id: Spotify track ID

        Returns:
            Dict with audio features or None if preview unavailable

        Raises:
            RuntimeError: If analysis fails or audio analysis not installed

        Note:
            Replaces deprecated sp.audio_features() API.
            Analyzes 30-second preview with librosa.
            ~60-70% of tracks have previews available.
            Requires optional [audio] dependencies.
        """
        if not self.audio_analyzer:
            raise RuntimeError(
                "Audio analysis not available. Install with: pip install .[audio]"
            )

        # Get track details including preview_url
        try:
            track = self.sp.track(track_id)
            preview_url = track.get('preview_url')

            if not preview_url:
                return None

            # Analyze preview (async, runs in thread pool)
            features = await self.audio_analyzer.analyze_preview(
                preview_url,
                track_id
            )
            return features

        except AudioAnalysisError as e:
            # Convert specific internal exceptions to RuntimeError
            raise RuntimeError(
                f"Failed to analyze audio for track {track_id}: {e}"
            )

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Failed to get track {track_id}: {e}")
```

---

## 5. MCP Server Tool Exposure

### File: `src/server.py` (MODIFICATIONS)

**Add to `list_tools()`:**
```python
Tool(
    name="get_audio_features",
    description="Get audio features (BPM, key, energy, etc.) for a track using local analysis of its 30-second preview. Requires track to have preview available.",
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
),
```

**Add to `call_tool()` (async handler):**
```python
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
```

**IMPORTANT:** Change `call_tool()` function signature to async:
```python
@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls from Claude (async)."""
```

---

## 6. Dependency Management

### File: `pyproject.toml` (MODIFICATIONS)

```toml
[project]
name = "spotify-mcp"
version = "0.2.0"
dependencies = [
    "spotipy>=2.23.0",
    "python-dotenv>=1.0.0",
    "mcp>=0.1.0"
]

[project.optional-dependencies]
audio = [
    "librosa>=0.10.0",
    "soundfile>=0.12.0",
    "numpy>=1.24.0",
    "requests>=2.31.0"
]

dev = [
    "pytest>=7.0.0",
    "requests-mock>=1.10.0"
]
```

**Installation Instructions (update README):**
```bash
# Base installation (playlist management only)
pip install .

# With audio analysis features
pip install .[audio]

# Development (includes testing tools)
pip install .[audio,dev]
```

---

## 7. Git Ignore Updates

### File: `.gitignore` (ADDITIONS)

```gitignore
# Audio analysis cache
.audio_cache/

# Test fixtures (optional, if we commit fixtures keep this out)
tests/fixtures/audio/*.mp3
```

---

## 8. Testing Strategy

### 8.1 Test Fixtures

Create `tests/fixtures/audio/` with known test clips:
- `120bpm_c_major.mp3` - Simple electronic track (known BPM/key)
- `rock_g_major.mp3` - Rock track with drums
- `jazz_variable.mp3` - Variable tempo jazz (edge case)

**Fixture Creation:**
Use a tool like Audacity to create 5-10 second clips from known tracks, verify BPM/key manually.

### 8.2 Unit Tests

**File: `tests/test_audio_analyzer.py`**

```python
import pytest
import os
from src.analysis.audio_analyzer import AudioFeatureAnalyzer
from src.analysis.exceptions import AudioProcessingError


@pytest.fixture
def analyzer():
    return AudioFeatureAnalyzer(cache_dir=".test_cache")


def test_extract_features_120bpm(analyzer):
    """Test feature extraction on known 120 BPM track."""
    fixture_path = "tests/fixtures/audio/120bpm_c_major.mp3"

    features = analyzer._extract_features(fixture_path)

    assert 118 <= features["tempo"] <= 122  # ±2 BPM tolerance
    assert features["key"] == 0  # C
    assert features["mode"] == 1  # Major
    assert 0.0 <= features["energy"] <= 1.0
    assert "analyzer_version" not in features  # Added by analyze_preview


@pytest.mark.asyncio
async def test_analyze_preview_caching(analyzer, requests_mock):
    """Test that analysis results are cached."""
    # Mock HTTP GET
    with open("tests/fixtures/audio/120bpm_c_major.mp3", "rb") as f:
        audio_bytes = f.read()

    requests_mock.get(
        "https://p.scdn.co/mp3-preview/test",
        content=audio_bytes
    )

    # First call: should analyze
    features1 = await analyzer.analyze_preview(
        "https://p.scdn.co/mp3-preview/test",
        "test_track_id"
    )

    # Second call: should load from cache
    features2 = await analyzer.analyze_preview(
        "https://p.scdn.co/mp3-preview/test",
        "test_track_id"
    )

    assert features1 == features2
    assert requests_mock.call_count == 1  # Only called once


@pytest.mark.asyncio
async def test_analyze_preview_no_url(analyzer):
    """Test that None is returned when preview_url is None."""
    result = await analyzer.analyze_preview(None, "test_id")
    assert result is None
```

### 8.3 Integration Tests

**File: `tests/test_spotify_client.py` (ADDITIONS)**

```python
@pytest.mark.asyncio
async def test_get_track_audio_features_success(mocker):
    """Test successful audio feature extraction."""
    client = SpotifyClient(...)

    # Mock analyzer
    mock_analyzer = mocker.MagicMock()
    mock_analyzer.analyze_preview.return_value = {
        "tempo": 120.0,
        "key": 0,
        "mode": 1
    }
    client.audio_analyzer = mock_analyzer

    # Mock spotipy track call
    mocker.patch.object(
        client.sp,
        'track',
        return_value={
            'id': 'test_id',
            'preview_url': 'https://p.scdn.co/test.mp3'
        }
    )

    features = await client.get_track_audio_features("test_id")

    assert features["tempo"] == 120.0
    mock_analyzer.analyze_preview.assert_called_once()


@pytest.mark.asyncio
async def test_get_track_audio_features_no_preview():
    """Test graceful handling when track has no preview."""
    # ... similar test with preview_url = None ...
```

---

## 9. Implementation Checklist

### Phase 2A: Core Audio Analysis (Week 1, Days 1-3)

- [ ] Create `src/analysis/` directory structure
- [ ] Implement `src/analysis/exceptions.py`
- [ ] Implement `src/analysis/audio_analyzer.py`
  - [ ] `__init__` with cache directory setup
  - [ ] `analyze_preview()` async wrapper
  - [ ] `_extract_features()` with librosa
  - [ ] Cache versioning logic
- [ ] Update `.gitignore` for `.audio_cache/`
- [ ] Update `pyproject.toml` with optional `[audio]` deps
- [ ] Install dependencies: `pip install .[audio,dev]`

### Phase 2B: Integration (Week 1, Days 4-5)

- [ ] Modify `src/clients/spotify_client.py`
  - [ ] Add conditional import with `AUDIO_ANALYSIS_ENABLED`
  - [ ] Add `audio_analyzer` to `__init__`
  - [ ] Implement `get_track_audio_features()` async method
- [ ] Modify `src/server.py`
  - [ ] Change `call_tool()` to async
  - [ ] Add `get_audio_features` tool to `list_tools()`
  - [ ] Implement `get_audio_features` handler in `call_tool()`
- [ ] Manual testing with real Spotify tracks

### Phase 2C: Testing (Week 1, Days 6-7)

- [ ] Create test fixtures in `tests/fixtures/audio/`
- [ ] Implement `tests/test_audio_analyzer.py`
  - [ ] Unit tests for `_extract_features()`
  - [ ] Integration tests for `analyze_preview()`
  - [ ] Caching tests
- [ ] Implement `tests/test_spotify_client.py` additions
  - [ ] Mock-based integration tests
- [ ] Run full test suite: `pytest tests/`
- [ ] Document accuracy results in test report

### Phase 2D: Documentation (Week 2, Day 1)

- [ ] Update `README.md` with audio analysis features
- [ ] Add installation instructions for `[audio]` extra
- [ ] Document known limitations (60-70% preview coverage)
- [ ] Add examples of using `get_audio_features` tool
- [ ] Update `CURRENT_SPRINT.md` to mark Phase 2 complete

---

## 10. Known Limitations & Future Improvements

### Current Limitations
1. **Preview Coverage**: Only ~60-70% of tracks have preview URLs
2. **Accuracy**: Key/mode detection ~70-80% accurate (vs. Spotify's 95%+)
3. **Analysis Scope**: 30 seconds vs. full track
4. **No ML Features**: Cannot replicate speechiness, acousticness, instrumentalness

### Future Improvements (Phase 2D)
1. **Better Key Detection**: Research Krumhansl-Schmuckler algorithm
2. **Batch Processing**: Parallel analysis for multiple tracks
3. **Essentia Migration**: If performance becomes bottleneck
4. **Fallback Strategies**: Alternative data sources for tracks without previews

---

## 11. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Event loop blocking | **MITIGATED** | High | Use `asyncio.to_thread()` |
| Preview URL deprecated | Medium | High | Monitor Spotify API changelog |
| Low accuracy on complex music | High | Medium | Document limitations, allow user override |
| Heavy dependencies scare users | Low | Medium | Make `[audio]` optional |

---

## 12. Success Criteria

Phase 2 is complete when:
- ✅ `get_audio_features` tool works for tracks with previews
- ✅ BPM accuracy >85% on electronic/rock test tracks
- ✅ Key detection accuracy >75% on test tracks
- ✅ No event loop blocking (server remains responsive)
- ✅ Graceful degradation when audio deps not installed
- ✅ >80% test coverage for new code
- ✅ Documentation updated with examples

---

**Last Updated:** 2025-10-24
**Author:** Claude Code + Brian McManus
**Status:** ✅ APPROVED - Ready for Implementation
