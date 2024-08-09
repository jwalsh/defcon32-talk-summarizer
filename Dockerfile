FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    wget \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Set up a non-root user
RUN useradd -m appuser
WORKDIR /home/appuser/app
USER appuser

# Set up mirror directory
ENV MIRROR_DIR="/home/appuser/defcon32_mirror"
RUN mkdir -p $MIRROR_DIR

# Copy necessary files
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser tests ./tests
COPY --chown=appuser:appuser prompt_defcon_talk_summary_pqrst.tmpl .
COPY --chown=appuser:appuser mirror_defcon.sh .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run tests
CMD ["python", "-m", "unittest", "discover", "-v", "-s", "tests"]


