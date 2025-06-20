import sys
from server import app as server_app
from uvicorn import run
import os
from dotenv import load_dotenv

load_dotenv()
ENV = os.getenv("ENV", "development")
UVICORN_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")  # Bind to all interfaces
UVICORN_PORT = int(os.getenv("UVICORN_PORT", os.getenv("PORT", "8000")))

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"  # Default to "local"
    
    if mode == "local":
        if ENV == "production":
            print("Local mode is disabled in production.")
        else:
            print("Starting local pipeline...")
            from local import start_local
            start_local()

    elif mode == "web":
        print(f"Starting WebSocket server on {UVICORN_HOST}:{UVICORN_PORT}...")
        run(server_app, host=UVICORN_HOST, port=UVICORN_PORT)  # Run FastAPI server
    else:
        print("Invalid mode. Use 'local' or 'web'.")