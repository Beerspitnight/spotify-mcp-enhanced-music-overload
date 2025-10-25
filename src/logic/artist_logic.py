"""Artist discovery and analysis business logic."""

from typing import Dict, Any, List, Optional


class ArtistLogic:
    """Business logic for artist operations."""

    def __init__(self, spotify_client):
        """
        Initialize with Spotify client.

        Args:
            spotify_client: Instance of SpotifyClient
        """
        self.client = spotify_client

    def get_artist_discography(
        self,
        artist_id: str,
        include_groups: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get an artist's complete discography grouped by album type.

        Args:
            artist_id: Spotify artist ID
            include_groups: Album types to include (album, single, compilation, appears_on)
                          Default: ['album', 'single', 'compilation']
            limit: Maximum albums per group (default: 50)

        Returns:
            Dict with:
                - artist_name: Artist name
                - artist_id: Artist ID
                - genres: Artist genres
                - popularity: Artist popularity score
                - albums: List of albums
                - singles: List of singles
                - compilations: List of compilations
                - appears_ons: List of appearances (if requested)
                - total_releases: Total number of releases
        """
        if include_groups is None:
            include_groups = ['album', 'single', 'compilation']

        artist = self.client.sp.artist(artist_id)

        results = {
            "artist_name": artist['name'],
            "artist_id": artist_id,
            "genres": artist['genres'],
            "popularity": artist['popularity'],
            "followers": artist['followers']['total']
        }

        # Get albums by group
        for group in include_groups:
            albums = []
            result = self.client.sp.artist_albums(
                artist_id,
                album_type=group,
                limit=min(limit, 50)
            )

            while result:
                for album in result['items']:
                    albums.append({
                        "name": album['name'],
                        "release_date": album['release_date'],
                        "total_tracks": album['total_tracks'],
                        "album_type": album['album_type'],
                        "id": album['id'],
                        "uri": album['uri'],
                        "url": album['external_urls']['spotify']
                    })

                # Pagination
                if result['next'] and len(albums) < limit:
                    result = self.client.sp.next(result)
                else:
                    break

            results[f"{group}s"] = albums

        results['total_releases'] = sum(
            len(results.get(f"{group}s", []))
            for group in include_groups
        )

        return results

    def get_related_artists(
        self,
        artist_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get artists related to a given artist.

        Args:
            artist_id: Spotify artist ID
            limit: Maximum number of related artists (max: 20)

        Returns:
            Dict with:
                - original_artist: Original artist info
                - related_artists: List of related artist details
                - count: Number of related artists returned
        """
        artist = self.client.sp.artist(artist_id)
        related = self.client.sp.artist_related_artists(artist_id)

        related_artists = []
        for related_artist in related['artists'][:limit]:
            related_artists.append({
                "name": related_artist['name'],
                "id": related_artist['id'],
                "genres": related_artist['genres'],
                "popularity": related_artist['popularity'],
                "followers": related_artist['followers']['total'],
                "url": related_artist['external_urls']['spotify']
            })

        return {
            "original_artist": {
                "name": artist['name'],
                "id": artist['id'],
                "genres": artist['genres'],
                "popularity": artist['popularity']
            },
            "related_artists": related_artists,
            "count": len(related_artists)
        }

    def get_artist_top_tracks(
        self,
        artist_id: str,
        country: str = 'US'
    ) -> Dict[str, Any]:
        """
        Get an artist's top tracks.

        Args:
            artist_id: Spotify artist ID
            country: ISO 3166-1 alpha-2 country code (default: 'US')

        Returns:
            Dict with:
                - artist_name: Artist name
                - artist_id: Artist ID
                - country: Country code used
                - tracks: List of top track dicts
                - count: Number of tracks returned
        """
        artist = self.client.sp.artist(artist_id)
        result = self.client.sp.artist_top_tracks(artist_id, country=country)

        tracks = []
        for track in result['tracks']:
            tracks.append({
                "name": track['name'],
                "id": track['id'],
                "album": track['album']['name'],
                "popularity": track['popularity'],
                "duration_ms": track['duration_ms'],
                "uri": track['uri'],
                "url": track['external_urls']['spotify']
            })

        return {
            "artist_name": artist['name'],
            "artist_id": artist_id,
            "country": country,
            "tracks": tracks,
            "count": len(tracks)
        }
