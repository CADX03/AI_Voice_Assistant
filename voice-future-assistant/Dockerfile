### Development and prod file
FROM python:3.10-slim-bookworm
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# torch dependencies
RUN pip install --no-cache-dir \
    torch==2.6.0+cpu torchaudio==2.6.0 \
    --extra-index-url https://download.pytorch.org/whl/cpu
    
# Piper dependencies
RUN mkdir -p /app/piper_voices
COPY piper_voices/pt_PT-tugão-medium.onnx piper_voices/
COPY piper_voices/pt_PT-tugão-medium.onnx.json piper_voices/
RUN pip install --no-cache-dir \
    piper-phonemize==1.1.0 \
    piper-tts==1.2.0

# Install requirements
COPY requirements-prod.txt .
RUN pip install --no-cache-dir setuptools
RUN pip install --no-cache-dir -r requirements-prod.txt
COPY . .

ENV PYTHONUNBUFFERED=1
# speed up hugging face large model downloads
ENV HF_HUB_ENABLE_HF_TRANSFER=1 

# Expose port
EXPOSE 8000

# handle environment variables in custom script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]