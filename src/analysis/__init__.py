"""Audio analysis module for extracting features from Spotify preview URLs."""

from .exceptions import (
    AudioAnalysisError,
    PreviewDownloadError,
    AudioProcessingError
)

try:
    from .audio_analyzer import AudioFeatureAnalyzer
    AUDIO_ANALYSIS_AVAILABLE = True
except ImportError:
    AudioFeatureAnalyzer = None
    AUDIO_ANALYSIS_AVAILABLE = False

__all__ = [
    'AudioFeatureAnalyzer',
    'AudioAnalysisError',
    'PreviewDownloadError',
    'AudioProcessingError',
    'AUDIO_ANALYSIS_AVAILABLE'
]
