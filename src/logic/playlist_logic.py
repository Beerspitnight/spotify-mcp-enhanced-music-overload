"""Playlist intelligence business logic."""

from typing import Dict, Any, List
import sys


class PlaylistLogic:
    """Business logic for playlist operations."""

    def __init__(self, spotify_client):
        """
        Initialize with Spotify client.

        Args:
            spotify_client: Instance of SpotifyClient
        """
        self.client = spotify_client

    def get_playlist_stats(self, playlist_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a playlist.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            Dict with playlist statistics including:
                - playlist_name: Name of the playlist
                - playlist_description: Description
                - total_tracks: Number of tracks
                - total_duration_ms: Total duration in milliseconds
                - total_duration_formatted: Human-readable duration
                - avg_release_year: Average release year
                - genre_breakdown: Top genres and their counts
                - earliest_track: Oldest track info
                - newest_track: Newest track info
                - owner: Playlist owner
                - public: Whether playlist is public
                - collaborative: Whether playlist is collaborative
        """
        # Get playlist details and tracks
        playlist = self.client.sp.playlist(playlist_id)
        tracks = self.client.get_playlist_tracks(playlist_id)

        if not tracks:
            return {
                "playlist_name": playlist['name'],
                "total_tracks": 0,
                "total_duration_ms": 0,
                "total_duration_formatted": "0:00",
                "message": "Playlist is empty"
            }

        # Collect track IDs for batch fetching
        track_ids = [track['uri'].split(':')[-1] for track in tracks]

        # Batch fetch track details (50 per call)
        all_track_details = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            track_details = self.client.sp.tracks(batch)['tracks']
            all_track_details.extend(track_details)

        # Calculate stats
        total_duration_ms = 0
        release_years = []
        earliest_track = None
        newest_track = None
        earliest_date = None
        newest_date = None

        for track_detail in all_track_details:
            if track_detail:
                total_duration_ms += track_detail['duration_ms']

                # Track release years
                release_date = track_detail['album']['release_date']
                try:
                    year = int(release_date.split('-')[0])
                    release_years.append(year)

                    # Track earliest and newest
                    if earliest_date is None or release_date < earliest_date:
                        earliest_date = release_date
                        earliest_track = {
                            'name': track_detail['name'],
                            'artist': ', '.join([a['name'] for a in track_detail['artists']]),
                            'release_date': release_date
                        }

                    if newest_date is None or release_date > newest_date:
                        newest_date = release_date
                        newest_track = {
                            'name': track_detail['name'],
                            'artist': ', '.join([a['name'] for a in track_detail['artists']]),
                            'release_date': release_date
                        }
                except (ValueError, IndexError):
                    pass

        # Format duration
        hours = total_duration_ms // (1000 * 60 * 60)
        minutes = (total_duration_ms // (1000 * 60)) % 60
        seconds = (total_duration_ms // 1000) % 60

        if hours > 0:
            duration_formatted = f"{hours}h {minutes}m {seconds}s"
        else:
            duration_formatted = f"{minutes}m {seconds}s"

        # Calculate average year
        avg_year = sum(release_years) / len(release_years) if release_years else 0

        # Collect unique artist IDs for genre analysis
        artist_ids = set()
        for track_detail in all_track_details:
            if track_detail:
                for artist in track_detail['artists']:
                    artist_ids.add(artist['id'])

        # Batch fetch artist genres (50 per call)
        genre_counts: Dict[str, int] = {}
        artist_ids_list = list(artist_ids)

        for i in range(0, len(artist_ids_list), 50):
            batch = artist_ids_list[i:i+50]
            artists = self.client.sp.artists(batch)['artists']

            for artist in artists:
                if artist and artist['genres']:
                    for genre in artist['genres']:
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1

        # Sort genres by count and get top 10
        top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "playlist_name": playlist['name'],
            "playlist_description": playlist['description'] or "",
            "total_tracks": len(tracks),
            "total_duration_ms": total_duration_ms,
            "total_duration_formatted": duration_formatted,
            "avg_release_year": round(avg_year, 1) if avg_year else None,
            "genre_breakdown": dict(top_genres),
            "earliest_track": earliest_track,
            "newest_track": newest_track,
            "owner": playlist['owner']['display_name'],
            "public": playlist['public'],
            "collaborative": playlist['collaborative']
        }

    def merge_playlists(
        self,
        playlist_ids: List[str],
        new_playlist_name: str,
        remove_duplicates: bool = True,
        description: str = "",
        public: bool = False
    ) -> Dict[str, Any]:
        """
        Merge multiple playlists into a new playlist.

        Args:
            playlist_ids: List of Spotify playlist IDs to merge
            new_playlist_name: Name for the new merged playlist
            remove_duplicates: Whether to remove duplicate tracks (default: True)
            description: Description for the new playlist
            public: Whether the new playlist should be public

        Returns:
            Dict with:
                - playlist_id: ID of created playlist
                - playlist_url: URL of created playlist
                - playlist_name: Name of the playlist
                - tracks_added: Number of tracks added
                - duplicates_removed: Number of duplicates removed (if applicable)
                - source_playlists: Info about source playlists
        """
        # Get all tracks from all playlists
        all_tracks = []
        source_playlist_info = []

        for playlist_id in playlist_ids:
            playlist = self.client.sp.playlist(playlist_id)
            tracks = self.client.get_playlist_tracks(playlist_id)

            source_playlist_info.append({
                "name": playlist['name'],
                "track_count": len(tracks)
            })

            all_tracks.extend(tracks)

        if not all_tracks:
            raise RuntimeError("No tracks found in source playlists")

        # Remove duplicates if requested
        duplicates_removed = 0
        if remove_duplicates:
            seen_uris = set()
            unique_tracks = []

            for track in all_tracks:
                if track['uri'] not in seen_uris:
                    seen_uris.add(track['uri'])
                    unique_tracks.append(track)
                else:
                    duplicates_removed += 1

            all_tracks = unique_tracks

        # Create new playlist
        if not description:
            playlist_names = ", ".join([p['name'] for p in source_playlist_info])
            description = f"Merged from: {playlist_names}"

        new_playlist = self.client.create_playlist(
            name=new_playlist_name,
            description=description,
            public=public
        )

        # Add tracks to new playlist
        track_uris = [track['uri'] for track in all_tracks]
        add_result = self.client.add_tracks_to_playlist(
            playlist_id=new_playlist['playlist_id'],
            track_uris=track_uris
        )

        return {
            "playlist_id": new_playlist['playlist_id'],
            "playlist_url": new_playlist['url'],
            "playlist_name": new_playlist['name'],
            "tracks_added": add_result['tracks_added'],
            "duplicates_removed": duplicates_removed,
            "source_playlists": source_playlist_info
        }

    def compare_playlists(
        self,
        playlist_id_1: str,
        playlist_id_2: str
    ) -> Dict[str, Any]:
        """
        Compare two playlists and find unique/shared tracks.

        Args:
            playlist_id_1: First playlist ID
            playlist_id_2: Second playlist ID

        Returns:
            Dict with:
                - playlist_1_name: Name of first playlist
                - playlist_2_name: Name of second playlist
                - shared_tracks: Tracks in both playlists
                - unique_to_playlist_1: Tracks only in playlist 1
                - unique_to_playlist_2: Tracks only in playlist 2
                - shared_count: Number of shared tracks
                - unique_1_count: Number unique to playlist 1
                - unique_2_count: Number unique to playlist 2
        """
        # Get both playlists
        playlist_1 = self.client.sp.playlist(playlist_id_1)
        playlist_2 = self.client.sp.playlist(playlist_id_2)

        tracks_1 = self.client.get_playlist_tracks(playlist_id_1)
        tracks_2 = self.client.get_playlist_tracks(playlist_id_2)

        # Create sets of URIs
        uris_1 = {track['uri']: track for track in tracks_1}
        uris_2 = {track['uri']: track for track in tracks_2}

        # Find shared and unique tracks
        shared_uris = set(uris_1.keys()) & set(uris_2.keys())
        unique_1_uris = set(uris_1.keys()) - set(uris_2.keys())
        unique_2_uris = set(uris_2.keys()) - set(uris_1.keys())

        return {
            "playlist_1_name": playlist_1['name'],
            "playlist_2_name": playlist_2['name'],
            "shared_tracks": [uris_1[uri] for uri in shared_uris],
            "unique_to_playlist_1": [uris_1[uri] for uri in unique_1_uris],
            "unique_to_playlist_2": [uris_2[uri] for uri in unique_2_uris],
            "shared_count": len(shared_uris),
            "unique_1_count": len(unique_1_uris),
            "unique_2_count": len(unique_2_uris)
        }

    def set_collaborative(
        self,
        playlist_id: str,
        collaborative: bool
    ) -> Dict[str, Any]:
        """
        Toggle collaborative status of a playlist.

        Args:
            playlist_id: Spotify playlist ID
            collaborative: Whether to make playlist collaborative

        Returns:
            Dict with:
                - playlist_id: ID of the playlist
                - playlist_name: Name of the playlist
                - collaborative: New collaborative status
                - success: Whether operation succeeded
        """
        # Get current playlist info
        playlist = self.client.sp.playlist(playlist_id)

        # Update collaborative status
        self.client.sp.playlist_change_details(
            playlist_id=playlist_id,
            collaborative=collaborative
        )

        # Verify the change
        updated_playlist = self.client.sp.playlist(playlist_id)

        return {
            "playlist_id": playlist_id,
            "playlist_name": playlist['name'],
            "collaborative": updated_playlist['collaborative'],
            "success": updated_playlist['collaborative'] == collaborative
        }
