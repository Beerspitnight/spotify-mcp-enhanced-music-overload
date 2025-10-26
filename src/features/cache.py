"""Caching layer for audio features."""

import json
import logging
import os
from typing import Optional
from datetime import datetime, timedelta

from .models import AudioFeatures

logger = logging.getLogger(__name__)


class FeatureCache:
    """
    Simple file-based cache for audio features.

    Uses JSON files in a cache directory. Supports TTL for cache invalidation.
    """

    def __init__(self, cache_dir: str = ".feature_cache", ttl_days: int = 30):
        """
        Initialize cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_days: Cache time-to-live in days
        """
        self.cache_dir = cache_dir
        self.ttl = timedelta(days=ttl_days)
        os.makedirs(cache_dir, exist_ok=True)
        logger.debug(f"Feature cache initialized at: {cache_dir}")

    def _get_cache_path(self, track_id: str) -> str:
        """Get cache file path for track ID."""
        return os.path.join(self.cache_dir, f"{track_id}.json")

    async def get(self, track_id: str) -> Optional[AudioFeatures]:
        """
        Get cached features for track.

        Args:
            track_id: Spotify track ID

        Returns:
            AudioFeatures if cached and valid, None otherwise
        """
        cache_path = self._get_cache_path(track_id)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)

            # Check if cache is still valid
            retrieved_at = datetime.fromisoformat(data["retrieved_at"])
            age = datetime.utcnow() - retrieved_at

            if age > self.ttl:
                logger.debug(f"Cache expired for track: {track_id}")
                os.unlink(cache_path)
                return None

            # Check for negative cache (no features found)
            if data.get("_not_found"):
                logger.debug(f"Negative cache hit for track: {track_id}")
                return None

            logger.debug(f"Cache hit for track: {track_id}")
            return AudioFeatures(**data)

        except (json.JSONDecodeError, KeyError, ValueError, OSError) as e:
            logger.warning(f"Failed to read cache for track {track_id}: {e}")
            # Clean up corrupted cache file
            try:
                os.unlink(cache_path)
            except OSError:
                pass
            return None

    async def set(self, track_id: str, features: Optional[AudioFeatures]) -> None:
        """
        Cache features for track.

        Args:
            track_id: Spotify track ID
            features: AudioFeatures object or None for negative cache
        """
        cache_path = self._get_cache_path(track_id)

        try:
            if features is None:
                # Negative cache: store marker that features not found
                data = {
                    "_not_found": True,
                    "retrieved_at": datetime.utcnow().isoformat()
                }
            else:
                # Convert pydantic model to dict with datetime serialization
                data = features.dict()
                # Convert datetime to ISO format string
                if "retrieved_at" in data and isinstance(data["retrieved_at"], datetime):
                    data["retrieved_at"] = data["retrieved_at"].isoformat()

            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Cached features for track: {track_id}")

        except (OSError, TypeError) as e:
            logger.warning(f"Failed to write cache for track {track_id}: {e}")

    async def clear(self, track_id: Optional[str] = None) -> None:
        """
        Clear cache for specific track or entire cache.

        Args:
            track_id: Track ID to clear, or None to clear all
        """
        if track_id:
            cache_path = self._get_cache_path(track_id)
            try:
                os.unlink(cache_path)
                logger.debug(f"Cleared cache for track: {track_id}")
            except OSError:
                pass
        else:
            # Clear all cache files
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.unlink(os.path.join(self.cache_dir, filename))
                logger.info("Cleared entire feature cache")
            except OSError as e:
                logger.warning(f"Failed to clear cache: {e}")
