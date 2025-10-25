"""Spotify API client wrapper using spotipy."""

import os
import sys
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, List, Dict, Any, Callable

# Conditional import for audio analysis (optional feature)
try:
    import sys
    import os
    # Add src directory to path if not already present
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    from analysis.audio_analyzer import AudioFeatureAnalyzer
    from analysis.exceptions import AudioAnalysisError
    AUDIO_ANALYSIS_ENABLED = True
except ImportError as e:
    AudioFeatureAnalyzer = None
    AudioAnalysisError = None
    AUDIO_ANALYSIS_ENABLED = False


class SpotifyClient:
    """Wrapper around spotipy for Spotify API interactions."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        cache_path: str = ".spotify_cache"
    ):
        """
        Initialize Spotify client with OAuth.
        
        Args:
            client_id: Spotify application client ID
            client_secret: Spotify application client secret
            redirect_uri: OAuth redirect URI (must match Spotify app settings)
            cache_path: Path to store OAuth tokens
        """
        self.scope = " ".join([
            "playlist-modify-public",
            "playlist-modify-private",
            "playlist-read-private",
            "playlist-read-collaborative",
            "user-library-read",
            "user-top-read",
        ])
        
        self.auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.scope,
            cache_path=cache_path,
            open_browser=True  # Will open browser for first-time auth
        )

        self.sp: Optional[spotipy.Spotify] = None

        # Initialize audio analyzer (optional feature)
        if AUDIO_ANALYSIS_ENABLED:
            self.audio_analyzer = AudioFeatureAnalyzer()
        else:
            self.audio_analyzer = None
    
    def authenticate(self) -> None:
        """Authenticate with Spotify. Opens browser on first run."""
        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
        # Test the connection
        user = self.sp.me()
        print(f"✅ Authenticated as: {user['display_name']} ({user['id']})")

    def _with_retry(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Execute Spotify API call with automatic retry on rate limit.

        Args:
            fn: The Spotify API function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result from the API call

        Raises:
            spotipy.SpotifyException: For non-rate-limit errors
        """
        try:
            return fn(*args, **kwargs)
        except spotipy.SpotifyException as e:
            if e.http_status == 429:  # Rate limited
                retry_after = int(e.headers.get("Retry-After", 1))
                print(
                    f"⚠️  Rate limited. Waiting {retry_after} seconds...",
                    file=sys.stderr
                )
                time.sleep(retry_after)
                return fn(*args, **kwargs)  # Single retry after waiting
            raise  # Re-raise non-rate-limit errors

    def create_playlist(
        self,
        name: str,
        description: str = "",
        public: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new playlist.
        
        Args:
            name: Playlist name
            description: Playlist description
            public: Whether playlist is public
            
        Returns:
            Dict with playlist_id, url, and name
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        user_id = self.sp.me()['id']
        playlist = self.sp.user_playlist_create(
            user=user_id,
            name=name,
            description=description,
            public=public
        )
        
        return {
            "playlist_id": playlist['id'],
            "url": playlist['external_urls']['spotify'],
            "name": playlist['name'],
            "description": playlist['description']
        }
    
    def add_tracks_to_playlist(
        self,
        playlist_id: str,
        track_uris: List[str]
    ) -> Dict[str, Any]:
        """
        Add tracks to a playlist with automatic rate limit handling.

        Args:
            playlist_id: Spotify playlist ID
            track_uris: List of Spotify track URIs (e.g., "spotify:track:...")

        Returns:
            Dict with success status and number of tracks added

        Note:
            Automatically retries if rate limited (HTTP 429)
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Spotify allows max 100 tracks per request
        batch_size = 100
        tracks_added = 0

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            self._with_retry(self.sp.playlist_add_items, playlist_id, batch)
            tracks_added += len(batch)

        return {
            "success": True,
            "tracks_added": tracks_added,
            "playlist_id": playlist_id
        }

    def remove_tracks_from_playlist(
        self,
        playlist_id: str,
        track_uris: List[str]
    ) -> Dict[str, Any]:
        """
        Remove tracks from a playlist with automatic rate limit handling.

        Args:
            playlist_id: Spotify playlist ID
            track_uris: List of Spotify track URIs to remove (e.g., "spotify:track:...")

        Returns:
            Dict with success status and number of tracks removed

        Note:
            Automatically retries if rate limited (HTTP 429)
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Spotify allows max 100 tracks per request for removal
            batch_size = 100
            tracks_removed = 0

            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                self._with_retry(
                    self.sp.playlist_remove_all_occurrences_of_items,
                    playlist_id,
                    batch
                )
                tracks_removed += len(batch)

            return {
                "success": True,
                "tracks_removed": tracks_removed,
                "playlist_id": playlist_id
            }

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Spotify API error: {e}")
    
    def search_tracks(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for tracks on Spotify.
        
        Args:
            query: Search query (artist, track name, etc.)
            limit: Maximum number of results (1-50)
            
        Returns:
            List of track dicts with id, name, artist, uri, and url
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        results = self.sp.search(q=query, type='track', limit=min(limit, 50))
        
        tracks = []
        for item in results['tracks']['items']:
            tracks.append({
                "id": item['id'],
                "name": item['name'],
                "artist": ", ".join([artist['name'] for artist in item['artists']]),
                "album": item['album']['name'],
                "uri": item['uri'],
                "url": item['external_urls']['spotify'],
                "duration_ms": item['duration_ms']
            })
        
        return tracks
    
    def get_user_playlists(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get current user's playlists.
        
        Args:
            limit: Maximum number of playlists to return
            
        Returns:
            List of playlist dicts with id, name, description, and url
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        results = self.sp.current_user_playlists(limit=limit)
        
        playlists = []
        for item in results['items']:
            playlists.append({
                "id": item['id'],
                "name": item['name'],
                "description": item['description'] or "",
                "url": item['external_urls']['spotify'],
                "tracks_total": item['tracks']['total'],
                "public": item['public']
            })
        
        return playlists
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Get all tracks from a playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List of track dicts
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        tracks = []
        results = self.sp.playlist_items(playlist_id)
        
        while results:
            for item in results['items']:
                if item['track']:  # Sometimes tracks can be null
                    track = item['track']
                    tracks.append({
                        "id": track['id'],
                        "name": track['name'],
                        "artist": ", ".join([artist['name'] for artist in track['artists']]),
                        "album": track['album']['name'],
                        "uri": track['uri'],
                        "url": track['external_urls']['spotify']
                    })
            
            # Check if there are more results
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        
        return tracks
    
    def get_recommendations(
        self,
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        seed_genres: Optional[List[str]] = None,
        limit: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get track recommendations based on seeds.

        Args:
            seed_tracks: List of track IDs
            seed_artists: List of artist IDs
            seed_genres: List of genre names
            limit: Number of recommendations (1-100)
            **kwargs: Additional tunable attributes (e.g., target_energy=0.8)

        Returns:
            List of recommended track dicts

        Raises:
            RuntimeError: If not authenticated
            ValueError: If no seeds are provided
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Validate at least one seed provided
        if not any([seed_tracks, seed_artists, seed_genres]):
            raise ValueError(
                "At least one of seed_tracks, seed_artists, or seed_genres "
                "must be provided for recommendations."
            )

        try:
            results = self.sp.recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres,
                limit=min(limit, 100),
                **kwargs
            )

            tracks = []
            for item in results['tracks']:
                tracks.append({
                    "id": item['id'],
                    "name": item['name'],
                    "artist": ", ".join([artist['name'] for artist in item['artists']]),
                    "album": item['album']['name'],
                    "uri": item['uri'],
                    "url": item['external_urls']['spotify']
                })

            return tracks

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Spotify API error: {e}")

    def find_duplicates(self, playlist_id: str) -> Dict[str, Any]:
        """
        Find duplicate tracks in a playlist based on track name and artist.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            Dict with duplicate_count, duplicates list, and total_tracks
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Get all tracks from the playlist
            tracks = self.get_playlist_tracks(playlist_id)

            if not tracks:
                return {
                    "duplicate_count": 0,
                    "duplicates": [],
                    "total_tracks": 0
                }

            # Track seen combinations of (name, artist)
            seen: Dict[tuple, List[Dict[str, Any]]] = {}

            for track in tracks:
                # Create a normalized key (lowercase for case-insensitive comparison)
                key = (track['name'].lower(), track['artist'].lower())

                if key not in seen:
                    seen[key] = []
                seen[key].append(track)

            # Find duplicates (entries where we've seen the same track more than once)
            duplicates = []
            duplicate_count = 0

            for key, track_list in seen.items():
                if len(track_list) > 1:
                    duplicate_count += len(track_list) - 1  # Don't count the first occurrence
                    duplicates.append({
                        "name": track_list[0]['name'],
                        "artist": track_list[0]['artist'],
                        "occurrences": len(track_list),
                        "uris": [t['uri'] for t in track_list],
                        "urls": [t['url'] for t in track_list]
                    })

            return {
                "duplicate_count": duplicate_count,
                "duplicates": duplicates,
                "total_tracks": len(tracks)
            }

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Spotify API error: {e}")

    def get_top_tracks(
        self,
        limit: int = 20,
        time_range: str = "medium_term"
    ) -> List[Dict[str, Any]]:
        """
        Get user's top tracks based on listening history.

        Args:
            limit: Number of tracks to return (1-50)
            time_range: Time period for top tracks
                - "short_term": ~4 weeks
                - "medium_term": ~6 months (default)
                - "long_term": all time

        Returns:
            List of track dicts with id, name, artist, album, uri, and url

        Raises:
            RuntimeError: If not authenticated
            ValueError: If invalid time_range provided
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        valid_ranges = ["short_term", "medium_term", "long_term"]
        if time_range not in valid_ranges:
            raise ValueError(
                f"Invalid time_range '{time_range}'. "
                f"Must be one of: {', '.join(valid_ranges)}"
            )

        try:
            results = self.sp.current_user_top_tracks(
                limit=min(limit, 50),
                time_range=time_range
            )

            tracks = []
            for item in results['items']:
                tracks.append({
                    "id": item['id'],
                    "name": item['name'],
                    "artist": ", ".join([artist['name'] for artist in item['artists']]),
                    "album": item['album']['name'],
                    "uri": item['uri'],
                    "url": item['external_urls']['spotify']
                })

            return tracks

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Spotify API error: {e}")

    def create_curated_playlist_from_top_tracks(
        self,
        playlist_name: str,
        num_top_tracks: int = 20,
        num_recommendations: int = 30,
        time_range: str = "medium_term",
        playlist_description: str = "",
        public: bool = False
    ) -> Dict[str, Any]:
        """
        Create a curated playlist based on user's top tracks plus recommendations.

        This high-level method:
        1. Gets user's top tracks
        2. Uses top 5 tracks as seeds for recommendations
        3. Creates a new playlist
        4. Adds top tracks + recommended tracks to the playlist

        Args:
            playlist_name: Name for the new playlist
            num_top_tracks: Number of top tracks to include (1-50)
            num_recommendations: Number of recommended tracks to add (1-100)
            time_range: Time period for top tracks (short_term, medium_term, long_term)
            playlist_description: Optional description for the playlist
            public: Whether the playlist should be public

        Returns:
            Dict with:
                - playlist_id: ID of created playlist
                - playlist_url: Spotify URL of playlist
                - tracks_added: Total number of tracks added
                - top_tracks_count: Number of top tracks included
                - recommendations_count: Number of recommended tracks added

        Raises:
            RuntimeError: If not authenticated or API error occurs
        """
        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Step 1: Get user's top tracks
            top_tracks = self.get_top_tracks(
                limit=num_top_tracks,
                time_range=time_range
            )

            if not top_tracks:
                raise RuntimeError("No top tracks found for user")

            # Step 2: Get recommendations using top 5 tracks as seeds
            seed_track_ids = [track['id'] for track in top_tracks[:5]]
            recommendations = self.get_recommendations(
                seed_tracks=seed_track_ids,
                limit=num_recommendations
            )

            # Step 3: Create the playlist
            if not playlist_description:
                time_labels = {
                    "short_term": "last month",
                    "medium_term": "last 6 months",
                    "long_term": "all time"
                }
                playlist_description = (
                    f"Curated mix based on your top {num_top_tracks} tracks from "
                    f"{time_labels.get(time_range, time_range)} plus "
                    f"{num_recommendations} similar recommendations"
                )

            playlist_info = self.create_playlist(
                name=playlist_name,
                description=playlist_description,
                public=public
            )

            # Step 4: Combine tracks and add to playlist
            all_track_uris = [track['uri'] for track in top_tracks]
            all_track_uris.extend([track['uri'] for track in recommendations])

            add_result = self.add_tracks_to_playlist(
                playlist_id=playlist_info['playlist_id'],
                track_uris=all_track_uris
            )

            return {
                "playlist_id": playlist_info['playlist_id'],
                "playlist_url": playlist_info['url'],
                "playlist_name": playlist_info['name'],
                "tracks_added": add_result['tracks_added'],
                "top_tracks_count": len(top_tracks),
                "recommendations_count": len(recommendations),
                "description": playlist_description
            }

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Spotify API error: {e}")

    async def get_track_audio_features(
        self,
        track_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get audio features for a track using local analysis.

        Args:
            track_id: Spotify track ID

        Returns:
            Dict with audio features or None if preview unavailable

        Raises:
            RuntimeError: If analysis fails or audio analysis not installed

        Note:
            Replaces deprecated sp.audio_features() API.
            Analyzes 30-second preview with librosa.
            ~60-70% of tracks have previews available.
            Requires optional [audio] dependencies.
        """
        if not self.audio_analyzer:
            raise RuntimeError(
                "Audio analysis not available. Install with: pip install .[audio]"
            )

        if not self.sp:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Get track details including preview_url
        try:
            track = self.sp.track(track_id)
            preview_url = track.get('preview_url')

            if not preview_url:
                return None

            # Analyze preview (async, runs in thread pool)
            features = await self.audio_analyzer.analyze_preview(
                preview_url,
                track_id
            )
            return features

        except AudioAnalysisError as e:
            # Convert specific internal exceptions to RuntimeError
            raise RuntimeError(
                f"Failed to analyze audio for track {track_id}: {e}"
            )

        except spotipy.SpotifyException as e:
            raise RuntimeError(f"Failed to get track {track_id}: {e}")