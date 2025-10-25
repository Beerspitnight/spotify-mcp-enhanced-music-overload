#!/usr/bin/env python3
"""Quick test of AudioFeatureAnalyzer module (Phase 2A verification)."""

import asyncio
import sys
from src.analysis import AudioFeatureAnalyzer, AUDIO_ANALYSIS_AVAILABLE


async def test_analyzer():
    """Test that AudioFeatureAnalyzer can be instantiated and basic methods work."""

    print("=" * 60)
    print("Phase 2A: AudioFeatureAnalyzer Module Test")
    print("=" * 60)

    # Check availability
    print(f"\n✓ Audio analysis available: {AUDIO_ANALYSIS_AVAILABLE}")

    if not AUDIO_ANALYSIS_AVAILABLE:
        print("✗ Audio analysis dependencies not installed")
        return False

    # Create analyzer
    try:
        analyzer = AudioFeatureAnalyzer(cache_dir=".test_audio_cache")
        print("✓ AudioFeatureAnalyzer instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate AudioFeatureAnalyzer: {e}")
        return False

    # Test with None preview URL (should return None gracefully)
    result = await analyzer.analyze_preview(None, "test_track_id")
    if result is None:
        print("✓ Correctly handles None preview_url")
    else:
        print(f"✗ Expected None for missing preview_url, got: {result}")
        return False

    # Test analyzer version
    print(f"✓ Analyzer version: {analyzer.ANALYZER_VERSION}")

    print("\n" + "=" * 60)
    print("Phase 2A: All basic tests passed! ✅")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Phase 2B: Integrate with SpotifyClient")
    print("  - Test with real Spotify preview URLs")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_analyzer())
    sys.exit(0 if success else 1)
