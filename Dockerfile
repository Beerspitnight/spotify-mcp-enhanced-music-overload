# Dockerfile for Spotify MCP Server
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port 8888 for Spotify OAuth callback
EXPOSE 8888

# Set default environment variables
ENV SPOTIFY_CACHE_PATH=.spotify_cache

# Required environment variables (pass these when running the container):
# - SPOTIFY_CLIENT_ID: Your Spotify API client ID
# - SPOTIFY_CLIENT_SECRET: Your Spotify API client secret
# - SPOTIFY_REDIRECT_URI: OAuth redirect URI (default: http://127.0.0.1:8888/callback)
# Optional:
# - GETSONGBPM_API_KEY: For enhanced audio analysis coverage

# Run the server
CMD ["python", "-m", "src.server"]