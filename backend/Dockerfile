# Official Playwright Python image — ships with browsers + system libraries pre-installed.
# Pin base image and requirements.txt to the same Playwright version.
FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Browsers are already present in the base image; this is a safety net that also pins
# the exact browser build matching the installed playwright pip package.
RUN playwright install chromium

# Application code (mounted as volume in dev, copied in prod)
COPY . .

# Ensure runtime directories exist
RUN mkdir -p /app/data /app/logs

EXPOSE 8000

# Hot-reload in dev; override CMD in compose for prod (drop --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
