"""Local audio feature extraction from Spotify preview URLs."""

from typing import Optional, Dict, Any
import asyncio
import json
import os
import sys
import tempfile

try:
    import requests
    import librosa
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

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

    Note:
        Requires optional dependencies: librosa, numpy, soundfile, requests
        Install with: pip install .[audio]
    """

    ANALYZER_VERSION = "1.0.0"  # Bump when algorithm changes

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize analyzer with optional caching directory.

        Args:
            cache_dir: Directory for caching analysis results.
                      If None, uses system temp directory (recommended for MCP servers).

        Raises:
            ImportError: If required audio analysis dependencies are not installed
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "Audio analysis dependencies not installed. "
                "Install with: pip install .[audio]"
            )

        # Use system temp directory by default to avoid permission issues with MCP servers
        if cache_dir is None:
            cache_dir = os.path.join(tempfile.gettempdir(), "spotify-mcp-audio-cache")
        elif not os.path.isabs(cache_dir):
            # If relative path provided, make it absolute using temp dir
            cache_dir = os.path.join(tempfile.gettempdir(), cache_dir)

        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        print(f"🗂️  Audio cache directory: {cache_dir}", file=sys.stderr)

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
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    if data.get("analyzer_version") == self.ANALYZER_VERSION:
                        print(f"✅ Loaded cached analysis for {track_id}", file=sys.stderr)
                        return data
                    else:
                        print(f"⚠️  Cache version mismatch for {track_id}, re-analyzing", file=sys.stderr)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Cache read error for {track_id}: {e}", file=sys.stderr)

        # Download preview (run in thread to avoid blocking)
        print(f"⬇️  Downloading preview for {track_id}...", file=sys.stderr)
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
            print(f"🔬 Analyzing audio for {track_id}...", file=sys.stderr)
            features = await asyncio.to_thread(self._extract_features, tmp_path)

            # Add metadata
            features["analyzer_version"] = self.ANALYZER_VERSION
            features["track_id"] = track_id
            features["preview_url"] = preview_url

            # Cache results
            try:
                with open(cache_path, 'w') as f:
                    json.dump(features, f, indent=2)
                print(f"💾 Cached analysis for {track_id}", file=sys.stderr)
            except IOError as e:
                print(f"⚠️  Failed to cache analysis: {e}", file=sys.stderr)

            return features

        except Exception as e:
            raise AudioProcessingError(
                f"Librosa failed to process audio for track {track_id}"
            ) from e

        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

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
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)

        # Regularity: std deviation of beat intervals
        if len(beats) > 1:
            beat_intervals = np.diff(beats)
            regularity = 1.0 - min(np.std(beat_intervals) / np.mean(beat_intervals), 1.0)
        else:
            regularity = 0.0

        # Strength: average onset strength at beat locations
        if len(beats) > 0:
            beat_strengths = onset_env[beats]
            strength = np.mean(beat_strengths) / (np.max(onset_env) + 1e-6)
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
