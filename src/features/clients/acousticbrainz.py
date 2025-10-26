"""AcousticBrainz API client."""

import logging
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models import AudioFeatures

logger = logging.getLogger(__name__)


class AcousticBrainzClient:
    """Client for AcousticBrainz API."""

    BASE_URL = "https://acousticbrainz.org/api/v1"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fetch(self, mbid: str) -> Optional[AudioFeatures]:
        """
        Fetch audio features from AcousticBrainz using MBID.

        Args:
            mbid: MusicBrainz Recording ID

        Returns:
            AudioFeatures if found, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                logger.debug(f"Fetching from AcousticBrainz: {mbid}")
                response = await client.get(f"{self.BASE_URL}/{mbid}/low-level")

                if response.status_code == 404:
                    logger.debug(f"No features found in AcousticBrainz for MBID: {mbid}")
                    return None

                response.raise_for_status()
                data = response.json()

                return self._map_to_audio_features(data, mbid)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error from AcousticBrainz: {e.response.status_code}")
            raise
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching from AcousticBrainz for MBID: {mbid}")
            raise
        except Exception:
            logger.exception(f"Unexpected error in AcousticBrainzClient for MBID: {mbid}")
            return None

    def _map_to_audio_features(self, data: dict, mbid: str) -> Optional[AudioFeatures]:
        """
        Map AcousticBrainz response to AudioFeatures model.

        Args:
            data: API response data
            mbid: MusicBrainz ID

        Returns:
            AudioFeatures object or None
        """
        try:
            # AcousticBrainz structure:
            # {
            #   "rhythm": { "bpm": 120.5, ... },
            #   "tonal": { "key_key": 9, "key_scale": "major", ... },
            #   "lowlevel": { "spectral_centroid": {...}, ... },
            #   "metadata": { ... }
            # }

            rhythm = data.get("rhythm", {})
            tonal = data.get("tonal", {})
            lowlevel = data.get("lowlevel", {})

            # Extract BPM
            tempo = None
            if "bpm" in rhythm:
                tempo = float(rhythm["bpm"])

            # Extract key and mode
            key = None
            mode = None
            if "key_key" in tonal:
                key_value = tonal["key_key"]
                # Handle both string and integer key values
                if isinstance(key_value, str):
                    # Map note names to pitch class
                    key_map = {
                        "C": 0, "C#": 1, "Db": 1,
                        "D": 2, "D#": 3, "Eb": 3,
                        "E": 4,
                        "F": 5, "F#": 6, "Gb": 6,
                        "G": 7, "G#": 8, "Ab": 8,
                        "A": 9, "A#": 10, "Bb": 10,
                        "B": 11
                    }
                    key = key_map.get(key_value)
                else:
                    key = int(key_value)
            if "key_scale" in tonal:
                mode = 1 if tonal["key_scale"] == "major" else 0

            # Extract energy (estimate from RMS energy)
            energy = None
            if "average_loudness" in lowlevel:
                # Normalize from dB scale (typically -60 to 0)
                loudness_db = lowlevel["average_loudness"]
                # Simple normalization: map [-60, 0] to [0, 1]
                energy = max(0.0, min(1.0, (loudness_db + 60) / 60))

            # Extract loudness
            loudness = None
            if "average_loudness" in lowlevel:
                loudness = float(lowlevel["average_loudness"])

            # Note: AcousticBrainz doesn't provide direct equivalents for
            # danceability, valence, acousticness, speechiness, etc.
            # These would require more complex analysis of the low-level features

            return AudioFeatures(
                tempo=tempo,
                key=key,
                mode=mode,
                energy=energy,
                loudness=loudness,
                source="acousticbrainz",
                source_track_id=mbid
            )

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse AcousticBrainz response for MBID {mbid}: {e}")
            return None
