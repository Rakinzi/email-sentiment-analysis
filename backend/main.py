# main.py
import os
import uvicorn
import multiprocessing
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file
load_dotenv()

# Create the FastAPI app
app = create_app()

if __name__ == "__main__":
    # This is needed for Windows to handle multiprocessing correctly
    multiprocessing.freeze_support()
    
    # Run the uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)