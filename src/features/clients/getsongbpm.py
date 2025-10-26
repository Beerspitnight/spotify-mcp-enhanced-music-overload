"""GetSongBPM API client."""

import logging
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..models import AudioFeatures, SpotifyTrack

logger = logging.getLogger(__name__)


class GetSongBPMClient:
    """Client for GetSongBPM API."""

    BASE_URL = "https://api.getsong.co"

    def __init__(self, api_key: str):
        """
        Initialize GetSongBPM client.

        Args:
            api_key: GetSongBPM API key
        """
        self.api_key = api_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fetch(self, track: SpotifyTrack) -> Optional[AudioFeatures]:
        """
        Fetch audio features from GetSongBPM API.

        Args:
            track: Spotify track information

        Returns:
            AudioFeatures if found, None otherwise
        """
        try:
            # Use the search endpoint with correct parameters
            params = {
                "api_key": self.api_key,
                "type": "both",
                "lookup": f"song:{track.name} artist:{track.artist}"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug(f"Searching GetSongBPM: {track.name} by {track.artist}")
                response = await client.get(f"{self.BASE_URL}/search/", params=params)

                # 404 means not found in their database
                if response.status_code == 404:
                    logger.debug(f"Track not found in GetSongBPM: {track.id}")
                    return None

                response.raise_for_status()
                data = response.json()

                # Check if we have search results
                search_results = data.get("search", [])
                if not search_results or not isinstance(search_results, list) or len(search_results) == 0:
                    logger.debug(f"No search results from GetSongBPM for: {track.id}")
                    return None

                # Use the first result (best match)
                first_result = search_results[0]
                logger.debug(f"Found match: {first_result.get('title')} (ID: {first_result.get('id')})")

                # Parse and map to our model
                return self._map_to_audio_features({"song": first_result}, track.id)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error from GetSongBPM: {e.response.status_code}")
            raise
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching from GetSongBPM for track: {track.id}")
            raise
        except Exception:
            logger.exception(f"Unexpected error in GetSongBPMClient for track: {track.id}")
            return None

    def _map_to_audio_features(self, data: dict, track_id: str) -> Optional[AudioFeatures]:
        """
        Map GetSongBPM response to AudioFeatures model.

        Args:
            data: API response data
            track_id: Spotify track ID

        Returns:
            AudioFeatures object
        """
        try:
            song_data = data.get("song", {})

            # Map key notation to pitch class integer (0-11)
            key_str = song_data.get("key_of", "")
            key_int = self._parse_key(key_str)

            # Map time signature string to integer
            time_sig = song_data.get("time_sig", "")
            time_sig_int = self._parse_time_signature(time_sig)

            return AudioFeatures(
                tempo=float(song_data["tempo"]) if song_data.get("tempo") else None,
                key=key_int,
                mode=0 if "m" in key_str else 1,  # Minor (0) if 'm' in key notation, Major (1) otherwise
                danceability=float(song_data["danceability"]) / 100.0 if song_data.get("danceability") else None,
                acousticness=float(song_data["acousticness"]) / 100.0 if song_data.get("acousticness") else None,
                time_signature=time_sig_int,
                source="getsongbpm",
                source_track_id=song_data.get("id")
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse GetSongBPM response for track {track_id}: {e}")
            return None

    def _parse_key(self, key_str: str) -> Optional[int]:
        """
        Parse key notation to pitch class integer.

        Args:
            key_str: Key notation (e.g., "C", "F#m", "Bbm")

        Returns:
            Pitch class integer (0-11) or None
        """
        if not key_str:
            return None

        # Remove 'm' for minor
        key_str = key_str.replace("m", "").strip()

        key_map = {
            "C": 0, "C#": 1, "Db": 1,
            "D": 2, "D#": 3, "Eb": 3,
            "E": 4,
            "F": 5, "F#": 6, "Gb": 6,
            "G": 7, "G#": 8, "Ab": 8,
            "A": 9, "A#": 10, "Bb": 10,
            "B": 11
        }

        return key_map.get(key_str)

    def _parse_time_signature(self, time_sig_str: str) -> Optional[int]:
        """
        Parse time signature string to integer.

        Args:
            time_sig_str: Time signature (e.g., "4/4", "3/4")

        Returns:
            Numerator of time signature or None
        """
        if not time_sig_str:
            return None

        try:
            numerator = time_sig_str.split("/")[0]
            return int(numerator)
        except (IndexError, ValueError):
            return None
