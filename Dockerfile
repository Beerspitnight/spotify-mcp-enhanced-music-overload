# Start from the same base
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Optimization Starts Here ---

# 1. Copy ONLY the files that define your dependencies
COPY pyproject.toml .
# If you had a requirements.txt, you'd copy it here too
# COPY requirements.txt .

# 2. Install the dependencies
# This step will now be cached and only re-run if
# pyproject.toml (or requirements.txt) changes.
RUN pip install --no-cache-dir -e .

# 3. NOW copy the rest of your project's source code
COPY . .
# (A more advanced version might just be "COPY src/ src/")

# --- End of Optimization ---

# The rest is the same
EXPOSE 8888
ENV SPOTIFY_CACHE_PATH=.spotify_cache
CMD ["python", "-m", "src.server"]
