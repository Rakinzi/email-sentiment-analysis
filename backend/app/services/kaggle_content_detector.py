# app/services/kaggle_content_detector.py
import os
import numpy as np
import pandas as pd
import pickle
import re
import requests
import zipfile
import io
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import Dict, Any, Optional

class KaggleContentDetector:
    """
    Content detector using specific Kaggle models for toxic content detection.
    """
    
    def __init__(self, models_dir: str = "app/models"):
        """
        Initialize the Kaggle content detector
        
        Args:
            models_dir (str): Directory where the models will be stored
        """
        self.models_dir = models_dir
        self.models = {}
        self.vectorizers = {}
        
        # Ensure model directory exists
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Download and load models if needed
        self._setup_models()
        
        # Define categories for unified reporting
        self.categories = [
            "hate_speech", "cyberbullying", "threats",
            "self_harm", "sexual_content", "misinformation"
        ]
    
    def _setup_models(self):
        """Download and set up the necessary models"""
        # Check if models are already downloaded
        jigsaw_model_path = os.path.join(self.models_dir, "jigsaw_model.pkl")
        jigsaw_vectorizer_path = os.path.join(self.models_dir, "jigsaw_vectorizer.pkl")
        
        # Download if not available
        if not (os.path.exists(jigsaw_model_path) and os.path.exists(jigsaw_vectorizer_path)):
            print("Downloading Jigsaw Toxic Comment model...")
            self._download_jigsaw_model()
        
        # Load models
        try:
            # Load Jigsaw model
            with open(jigsaw_model_path, 'rb') as f:
                self.models["jigsaw"] = pickle.load(f)
            with open(jigsaw_vectorizer_path, 'rb') as f:
                self.vectorizers["jigsaw"] = pickle.load(f)
            print("Jigsaw model loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def _download_jigsaw_model(self):
        """Download the Jigsaw model from Kaggle or a public repository"""
        try:
            # Direct link to a pre-trained Jigsaw model (this is an example URL)
            model_url = "https://github.com/your-username/jigsaw-toxic-model/releases/download/v1.0/jigsaw_model.zip"
            
            response = requests.get(model_url)
            if response.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(response.content))
                z.extractall(self.models_dir)
                print("Jigsaw model downloaded successfully")
            else:
                print(f"Failed to download model: HTTP {response.status_code}")
                
                # Fallback: Create a simple model using built-in lists
                self._create_fallback_model()
                
        except Exception as e:
            print(f"Error downloading model: {e}")
            # Fallback to a simple keyword-based approach
            self._create_fallback_model()
    
    def _create_fallback_model(self):
        """Create a simple fallback model based on keyword matching"""
        # Create a simple keyword-based "model"
        toxic_keywords = {
            "hate_speech": ["hate", "racial", "racist", "ethnicity", "minority"],
            "cyberbullying": ["stupid", "idiot", "loser", "ugly", "fat", "dumb"],
            "threats": ["kill", "hurt", "attack", "threaten", "violence", "revenge"],
            "self_harm": ["suicide", "kill myself", "end my life", "self harm", "cutting"],
            "sexual_content": ["sex", "porn", "naked", "nude", "explicit"],
            "misinformation": ["hoax", "conspiracy", "fake news", "government lies"]
        }
        
        # Save as a pickle file
        with open(os.path.join(self.models_dir, "jigsaw_model.pkl"), 'wb') as f:
            pickle.dump(toxic_keywords, f)
        
        # Create a simple vectorizer (just for API compatibility)
        vectorizer = TfidfVectorizer()
        vectorizer.fit(["placeholder text"])
        with open(os.path.join(self.models_dir, "jigsaw_vectorizer.pkl"), 'wb') as f:
            pickle.dump(vectorizer, f)
        
        # Load the models
        self.models["jigsaw"] = toxic_keywords
        self.vectorizers["jigsaw"] = vectorizer
        print("Created fallback keyword-based model")
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _analyze_with_keywords(self, text: str) -> Dict[str, float]:
        """Analyze text using keyword matching"""
        preprocessed_text = self._preprocess_text(text)
        scores = {category: 0.0 for category in self.categories}
        
        if "jigsaw" in self.models:
            toxic_keywords = self.models["jigsaw"]
            
            # Check each category's keywords
            for category, keywords in toxic_keywords.items():
                category_score = 0.0
                
                for keyword in keywords:
                    if keyword in preprocessed_text:
                        # Add weight based on how many times the keyword appears
                        occurrences = preprocessed_text.count(keyword)
                        category_score += 0.2 * occurrences
                
                # Cap at 1.0
                scores[category] = min(1.0, category_score)
        
        return scores
    
    def detect_harmful_content(self, text: str) -> Dict[str, Any]:
        """
        Detect harmful content using Kaggle-based models or fallback mechanism
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Analysis results with harm categories
        """
        # Get category scores using keyword analysis (can be replaced with ML model prediction)
        category_scores = self._analyze_with_keywords(text)
        
        # Calculate overall toxic score
        toxic_score = max(category_scores.values())
        
        # Determine primary harm type
        primary_harm_type = "None"
        max_score = 0.0
        
        for category, score in category_scores.items():
            if score > max_score and score >= 0.3:
                max_score = score
                primary_harm_type = category
        
        # Determine threat level
        if toxic_score > 0.7:
            threat_level = "High"
        elif toxic_score > 0.4:
            threat_level = "Medium"
        else:
            threat_level = "Low"
        
        # Return results in the same format as other detectors
        return {
            "toxic_score": toxic_score,
            "threat_level": threat_level,
            "primary_harm_type": primary_harm_type,
            "category_scores": category_scores
        }