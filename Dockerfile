# Start from the debian base image specified
FROM debian:bookworm-slim

# Install system dependencies, including python3, pip, and git
# (git is still useful if your requirements.txt needs it)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# --- THIS IS THE MAIN FIX for Error 1 ---
# Copy all your local files (from the directory you run 'docker build' in)
# into the /app directory inside the container.
# This replaces the 'RUN git clone ...' line.
COPY . .

# Create a Python virtual environment
RUN python3 -m venv venv

# Activate the venv and install the Python dependencies from your requirements.txt
# Using --no-cache-dir saves space in the final image
RUN . venv/bin/activate && pip3 install --no-cache-dir -r requirements.txt

# Expose port 8888, which is what your redirect URI uses
EXPOSE 8888

# Set the default cache path (as seen in your screenshot)
ENV SPOTIFY_CACHE_PATH=.spotify_cache

# --- THIS IS THE MAIN FIX for Error 2 ---
# The command to run when the container starts.
# It activates the virtual environment and then runs app.py using 'python3'
CMD ["sh", "-c", ". venv/bin/activate && python3 app.py"]