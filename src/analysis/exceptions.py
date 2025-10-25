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
