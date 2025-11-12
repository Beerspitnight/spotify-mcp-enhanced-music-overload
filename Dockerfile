FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    GLAMA_VERSION="1.0.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git bash python3 python3-pip python3-venv \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone your repo (replace with your actual GitHub link)
RUN git clone https://github.com/Beerspitnight/spotify-mcp-enhanced-music-overload . 

# Install dependencies (adjust if you have requirements.txt or package.json)
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy in your server source (if needed)
COPY . .

# Default command to start the MCP server
CMD ["mcp-proxy", "python3", "src/server.py"]
