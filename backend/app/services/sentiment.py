# app/services/sentiment.py
import nltk
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from app.config import NLTK_DATA_PATH

# Set NLTK data path
nltk.data.path.append(NLTK_DATA_PATH)

# Download VADER lexicon if not already present
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', download_dir=NLTK_DATA_PATH)

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """
    Analyze text sentiment and determine threat level
    
    Args:
        text (str): Text content to analyze
        
    Returns:
        tuple: (sentiment_scores, threat_level)
    """
    # Perform sentiment analysis
    scores = sia.polarity_scores(text)
    
    # Determine threat level
    negative_score = scores['neg']
    if negative_score > 0.7:
        threat_level = "High"
    elif negative_score > 0.4:
        threat_level = "Medium"
    else:
        threat_level = "Low"
    
    return scores, threat_level