--- START OF FILE SECURITY_STANDARDS.md ---
# Spotify Curation Security Standards (Actionable Reference)

**Authority**: PROJECT_STANDARDS.md | **Compliance**: Mandatory.

## 1. Secrets & Configuration

- **Rule**: NEVER commit secrets to Git.
- **Implementation**: Load credentials from `.env` (via `python-dotenv`). **`.env` and `.spotify_cache` MUST be in `.gitignore`**.
    - `SPOTIFY_CLIENT_ID`
    - `SPOTIFY_CLIENT_SECRET`
    - `SPOTIPY_REDIRECT_URI`

## 2. Authentication & Authorization

- **Flow**: Authorization Code Flow. Authentication is performed on the first run of `server.py` and token is persisted.
- **Token Storage**: `spotipy` handles token caching in the `.spotify_cache` file. This file must be treated as a **SECRET** (see above).
- **API Protection**: All tool functions must use the authenticated `SpotifyClient` instance (`src/spotify_client.py`).

## 3. Data Integrity & Validation

- **Input Validation**: All tool parameters must be validated to prevent bad API calls or unexpected input.
- **Error Handling**: Graceful failure: use comprehensive `try/except` blocks in `src/spotify_client.py` to catch `spotipy.SpotifyException` and return helpful error messages to the Claude caller.
- **Rate Limiting**: Implement a check for Spotify's rate limit headers (HTTP 429) to avoid being banned.

---