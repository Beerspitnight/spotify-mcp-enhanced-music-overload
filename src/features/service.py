"""Audio features service with multi-source waterfall logic."""

import logging
from typing import Optional

from .models import AudioFeatures, SpotifyTrack
from .cache import FeatureCache
from .clients import GetSongBPMClient, MusicBrainzClient, AcousticBrainzClient

logger = logging.getLogger(__name__)


class AudioFeaturesService:
    """
    Service for fetching audio features from multiple sources.

    Implements waterfall strategy:
    1. Check cache
    2. Try GetSongBPM (fastest, pre-computed)
    3. Try MusicBrainz + AcousticBrainz (slower, better coverage)
    4. Return None if no features found
    """

    def __init__(
        self,
        getsongbpm_client: Optional[GetSongBPMClient] = None,
        musicbrainz_client: Optional[MusicBrainzClient] = None,
        acousticbrainz_client: Optional[AcousticBrainzClient] = None,
        cache: Optional[FeatureCache] = None
    ):
        """
        Initialize audio features service.

        Args:
            getsongbpm_client: GetSongBPM client (optional)
            musicbrainz_client: MusicBrainz client (optional)
            acousticbrainz_client: AcousticBrainz client (optional)
            cache: Feature cache (optional)
        """
        self.getsongbpm = getsongbpm_client
        self.musicbrainz = musicbrainz_client or MusicBrainzClient()
        self.acousticbrainz = acousticbrainz_client or AcousticBrainzClient()
        self.cache = cache or FeatureCache()

        # Log which clients are available
        logger.info(f"AudioFeaturesService initialized with clients: "
                   f"GetSongBPM={'enabled' if self.getsongbpm else 'disabled'}, "
                   f"MusicBrainz=enabled, AcousticBrainz=enabled")

    async def get_features(self, track: SpotifyTrack) -> Optional[AudioFeatures]:
        """
        Get audio features for track using waterfall strategy.

        Args:
            track: Spotify track information

        Returns:
            AudioFeatures if found, None otherwise
        """
        logger.info(f"Fetching features for track: {track.id} - {track.name} by {track.artist}")

        # 1. Check cache
        cached = await self.cache.get(track.id)
        if cached is not None:
            logger.info(f"Returning cached features for track: {track.id}")
            return cached

        # 2. Try GetSongBPM (if available)
        if self.getsongbpm:
            try:
                features = await self.getsongbpm.fetch(track)
                if features:
                    logger.info(f"Found features from GetSongBPM for track: {track.id}")
                    await self.cache.set(track.id, features)
                    return features
            except Exception as e:
                logger.warning(f"GetSongBPM failed for track {track.id}: {e}")

        # 3. Try MusicBrainz + AcousticBrainz
        try:
            features = await self._fetch_from_acousticbrainz(track)
            if features:
                logger.info(f"Found features from AcousticBrainz for track: {track.id}")
                await self.cache.set(track.id, features)
                return features
        except Exception as e:
            logger.warning(f"AcousticBrainz path failed for track {track.id}: {e}")

        # 4. No features found - cache negative result
        logger.warning(f"No audio features found for track: {track.id}")
        await self.cache.set(track.id, None)
        return None

    async def _fetch_from_acousticbrainz(self, track: SpotifyTrack) -> Optional[AudioFeatures]:
        """
        Fetch features from AcousticBrainz via MusicBrainz lookup.

        Args:
            track: Spotify track information

        Returns:
            AudioFeatures if found, None otherwise
        """
        # First, get MBID from MusicBrainz
        mbid = None

        # Try ISRC lookup first (most reliable)
        if track.isrc:
            logger.debug(f"Looking up MBID by ISRC: {track.isrc}")
            mbid = await self.musicbrainz.lookup_mbid_by_isrc(track.isrc)

        # Fallback to fuzzy search if ISRC lookup failed
        if not mbid:
            logger.debug(f"Fuzzy searching MBID for: {track.name} by {track.artist}")
            mbid = await self.musicbrainz.fuzzy_search_mbid(
                track_name=track.name,
                artist_name=track.artist,
                duration_ms=track.duration_ms
            )

        # If we found an MBID, query AcousticBrainz
        if mbid:
            logger.debug(f"Found MBID {mbid}, querying AcousticBrainz")
            return await self.acousticbrainz.fetch(mbid)

        logger.debug(f"No MBID found for track: {track.id}")
        return None
