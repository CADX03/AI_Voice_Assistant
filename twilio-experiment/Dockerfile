### Development and prod file
FROM python:3.11-slim-bookworm
WORKDIR /app
COPY requirements-prod.txt .
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    torch==2.6.0+cpu torchaudio==2.6.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install setuptools before other requirements
RUN pip install --no-cache-dir setuptools
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY . .

ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# handle environment variables in custom script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "twilio_server:app"]