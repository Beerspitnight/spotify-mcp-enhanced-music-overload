"""Data models for audio features."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AudioFeatures(BaseModel):
    """
    Canonical audio features model.

    Normalized schema for audio features from multiple sources.
    All fields are optional to support partial data from different APIs.
    """
    # Core Spotify-like features (0.0 - 1.0 range)
    acousticness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence that track is acoustic")
    danceability: Optional[float] = Field(None, ge=0.0, le=1.0, description="How suitable for dancing")
    energy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Perceptual measure of intensity")
    instrumentalness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Predicts if track has no vocals")
    liveness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of live performance")
    speechiness: Optional[float] = Field(None, ge=0.0, le=1.0, description="Presence of spoken words")
    valence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Musical positiveness/happiness")

    # Musical characteristics
    key: Optional[int] = Field(None, ge=0, le=11, description="Musical key (0=C, 1=C#, ..., 11=B)")
    mode: Optional[Literal[0, 1]] = Field(None, description="Modality: 0=minor, 1=major")
    tempo: Optional[float] = Field(None, gt=0, description="Tempo in BPM")
    time_signature: Optional[int] = Field(None, ge=3, le=7, description="Time signature (3-7)")

    # Audio properties
    loudness: Optional[float] = Field(None, description="Overall loudness in dB")

    # Metadata
    source: Optional[str] = Field(None, description="Data source (e.g., 'getsongbpm', 'acousticbrainz')")
    source_track_id: Optional[str] = Field(None, description="Track ID from source (e.g., MBID)")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="When features were retrieved")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SpotifyTrack(BaseModel):
    """Simplified Spotify track model for feature extraction."""
    id: str
    name: str
    artist: str
    duration_ms: int
    isrc: Optional[str] = None
