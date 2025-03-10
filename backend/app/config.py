# app/config.py
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = f"sqlite:///{BASE_DIR}/threats.db"

# NLTK data path
NLTK_DATA_PATH = os.path.join(BASE_DIR, "nltk_data")