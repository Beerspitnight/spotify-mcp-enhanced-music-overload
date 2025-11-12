# Glama.ai compatible Dockerfile
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies matching glama.ai setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g mcp-proxy@5.5.4 pnpm@10.14.0 \
    && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="/usr/local/bin" sh \
    && uv python install 3.10 --default --preview \
    && ln -s $(uv python find) /usr/local/bin/python \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy all project files
COPY . .

# Install dependencies with uv into .venv
RUN uv sync

# Expose port 8888 for Spotify OAuth callback
EXPOSE 8888

# Set default environment variables
ENV SPOTIFY_CACHE_PATH=/app/.spotify_cache

# Required environment variables (pass these when running the container):
# - SPOTIFY_CLIENT_ID: Your Spotify API client ID
# - SPOTIFY_CLIENT_SECRET: Your Spotify API client secret
# - SPOTIFY_REDIRECT_URI: OAuth redirect URI (default: http://127.0.0.1:8888/callback)
# Optional:
# - GETSONGBPM_API_KEY: For enhanced audio analysis coverage

# Use venv's Python with mcp-proxy
CMD ["mcp-proxy", "/app/.venv/bin/python", "-m", "src.server"]