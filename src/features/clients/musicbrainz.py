"""MusicBrainz API client for ISRC lookups."""

import logging
from typing import Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class MusicBrainzClient:
    """Client for MusicBrainz API."""

    BASE_URL = "https://musicbrainz.org/ws/2"
    USER_AGENT = "SpotifyMCP/1.0 (https://github.com/yourusername/spotify-mcp)"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def lookup_mbid_by_isrc(self, isrc: str) -> Optional[str]:
        """
        Lookup MusicBrainz Recording ID (MBID) using ISRC.

        Args:
            isrc: International Standard Recording Code

        Returns:
            MBID (MusicBrainz ID) if found, None otherwise
        """
        try:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json"
            }

            params = {
                "query": f"isrc:{isrc}",
                "fmt": "json"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug(f"Looking up MBID for ISRC: {isrc}")
                response = await client.get(
                    f"{self.BASE_URL}/recording/",
                    params=params,
                    headers=headers
                )

                if response.status_code == 404:
                    logger.debug(f"No recording found for ISRC: {isrc}")
                    return None

                response.raise_for_status()
                data = response.json()

                # Extract first recording MBID from results
                recordings = data.get("recordings", [])
                if recordings and len(recordings) > 0:
                    mbid = recordings[0].get("id")
                    logger.debug(f"Found MBID {mbid} for ISRC {isrc}")
                    return mbid

                logger.debug(f"No recordings in response for ISRC: {isrc}")
                return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error from MusicBrainz: {e.response.status_code}")
            raise
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching from MusicBrainz for ISRC: {isrc}")
            raise
        except Exception:
            logger.exception(f"Unexpected error in MusicBrainzClient for ISRC: {isrc}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fuzzy_search_mbid(
        self,
        track_name: str,
        artist_name: str,
        duration_ms: Optional[int] = None
    ) -> Optional[str]:
        """
        Fuzzy search for MBID using track and artist name.

        Args:
            track_name: Track name
            artist_name: Artist name
            duration_ms: Track duration in milliseconds (optional, for matching)

        Returns:
            MBID if found, None otherwise
        """
        try:
            headers = {
                "User-Agent": self.USER_AGENT,
                "Accept": "application/json"
            }

            # Build query
            query = f'recording:"{track_name}" AND artist:"{artist_name}"'

            params = {
                "query": query,
                "fmt": "json",
                "limit": 5  # Get top 5 matches for comparison
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.debug(f"Fuzzy searching MBID for: {track_name} by {artist_name}")
                response = await client.get(
                    f"{self.BASE_URL}/recording/",
                    params=params,
                    headers=headers
                )

                if response.status_code == 404:
                    logger.debug(f"No recording found for: {track_name}")
                    return None

                response.raise_for_status()
                data = response.json()

                recordings = data.get("recordings", [])
                if not recordings:
                    return None

                # If we have duration, try to find the best match
                if duration_ms:
                    best_match = self._find_best_duration_match(recordings, duration_ms)
                    if best_match:
                        return best_match.get("id")

                # Otherwise, return first result
                mbid = recordings[0].get("id")
                logger.debug(f"Found MBID {mbid} for {track_name}")
                return mbid

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"HTTP error from MusicBrainz: {e.response.status_code}")
            raise
        except httpx.TimeoutException:
            logger.warning(f"Timeout fuzzy searching MusicBrainz for: {track_name}")
            raise
        except Exception:
            logger.exception(f"Unexpected error in fuzzy search for: {track_name}")
            return None

    def _find_best_duration_match(
        self,
        recordings: list,
        target_duration_ms: int,
        tolerance_ms: int = 5000
    ) -> Optional[dict]:
        """
        Find recording with closest duration match.

        Args:
            recordings: List of recording objects from MusicBrainz
            target_duration_ms: Target duration in milliseconds
            tolerance_ms: Maximum acceptable difference in milliseconds

        Returns:
            Best matching recording or None
        """
        best_match = None
        min_diff = float('inf')

        for recording in recordings:
            # MusicBrainz duration is in milliseconds
            mb_duration = recording.get("length")
            if not mb_duration:
                continue

            diff = abs(mb_duration - target_duration_ms)
            if diff < min_diff and diff <= tolerance_ms:
                min_diff = diff
                best_match = recording

        return best_match
