# Base Image: Python 3.12 (Golden Standard for 2026)
FROM python:3.12-slim

# Set Env to prevent Python from writing pyc files and buffering stdout
# DEBIAN_FRONTEND=noninteractive stops apt-get from whining about missing terminal
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    UV_SYSTEM_PYTHON=1 \
    DEBIAN_FRONTEND=noninteractive

# Install System Dependencies
# curl: to install uv
# git: if pip needs to fetch from git
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Fast Python Package Installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# CORRECT PATH for uv (It installs to /root/.local/bin by default)
ENV PATH="/root/.local/bin:$PATH"

# Set Work Directory
WORKDIR /app

# Copy dependency files first to leverage Docker Cache
COPY pyproject.toml .
# COPY uv.lock .  <-- Uncomment this if you have a lock file committed

# Install Dependencies directly into system python
# We use --system because we are already inside an isolated container
RUN uv pip install --system -r pyproject.toml || uv pip install --system .

# Copy the rest of the application code
COPY . .

# Expose ports
# 8501: Streamlit UI
# 8000: FastAPI Worker
EXPOSE 8501 8000

# Default Command (Overridden by docker-compose)
CMD ["python", "manage.py", "--help"]
