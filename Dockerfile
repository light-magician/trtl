# ──────────────────────────────────────────────────────────────
# trtl-daemon Dockerfile (single stage)
# ──────────────────────────────────────────────────────────────

FROM python:3.11-slim

# 1. Install system deps & CA certs for HTTPS calls
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      curl \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip, install Poetry & pipx
RUN pip install --upgrade pip \
 && pip install poetry pipx

# 3. Make sure pipx binaries are on PATH
ENV PATH="/root/.local/bin:${PATH}"

# 4. Copy the entire project into the container
WORKDIR /app
COPY . /app

# 5. Let Poetry create a venv and install all deps (including your CLI entry point)
RUN poetry install --no-interaction --no-ansi

# 6. Use pipx to install your project CLI in “editable” mode
#    (this lives outside Poetry’s venv so `trtl` is on /root/.local/bin)
RUN pipx install . --editable

# 7. Unbuffered output for real-time logs
ENV PYTHONUNBUFFERED=1
