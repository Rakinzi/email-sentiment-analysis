# app/services/harmful_content_detector.py
from transformers import pipeline
import openai
import os
import json

class HarmfulContentDetector:
    def __init__(self, openai_api_key=None):
        # Initialize the toxicity classification pipeline
        self.toxic_classifier = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            return_all_scores=True
        )
        
        # Set up OpenAI client
        self.use_openai = False
        if openai_api_key or os.environ.get("OPENAI_API_KEY"):
            openai.api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
            self.use_openai = True
            print("OpenAI API is configured and will be used for detection.")
    
    def detect_with_openai(self, text):
        """Use OpenAI to detect harmful content categories"""
        print("OpenAI is being used for enhanced detection.")
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Use the appropriate model
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are a harmful content detection assistant. Analyze the text and provide scores between 0 and 1 for the following categories: "
                            "hate_speech, cyberbullying, threats, self_harm, sexual_content, and misinformation. "
                            "Respond ONLY with a JSON object that contains these keys."
                        )
                    },
                    {"role": "user", "content": f"Analyze this text for harmful content: \"{text}\""}
                ],
               temperature=0.1,  # Reduced temperature for more consistent scoring
               max_tokens=150
            )
            
            # Extract and parse the JSON response from OpenAI
            result = response.choices[0].message.content
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                    print(f"OpenAI response: {result}")
                except json.JSONDecodeError:
                    print(f"Could not parse OpenAI response as JSON: {result}")
                    return {}
            
            # If the JSON object is nested under a key, adjust accordingly:
            return result.get("category_scores", result)
        except Exception as e:
            print(f"Error using OpenAI: {e}")
            return {}
    
    def detect_harmful_content(self, text, force_openai=False):
        """
        Analyze text for harmful content using both toxic-bert and OpenAI
        
        Args:
            text (str): Text content to analyze
            force_openai (bool): Whether to use OpenAI regardless of toxicity score
            
        Returns:
            dict: Analysis results with different harm categories
        """
        # Get results from toxic-bert
        toxic_results = self.toxic_classifier(text)
        
        toxic_categories = {}
        total_toxic_score = 0
        
        for result in toxic_results[0]:
            label = result['label'].lower()
            score = result['score']
            toxic_categories[label] = score
            
            if label in ["toxic", "severe_toxic"]:
                total_toxic_score += score
        
        toxic_score = min(1.0, total_toxic_score)
        
        # Map toxic-bert results to desired categories
        category_scores = {
            "hate_speech": toxic_categories.get("identity_hate", 0),
            "cyberbullying": max(toxic_categories.get("insult", 0), toxic_categories.get("threat", 0)),
            "threats": toxic_categories.get("threat", 0),
            "self_harm": 0,          # Not directly detected by toxic-bert
            "sexual_content": toxic_categories.get("obscene", 0),
            "misinformation": 0        # Not directly detected by toxic-bert
        }
        
        # Use OpenAI to enhance detection
        if self.use_openai and (force_openai or toxic_score > 0.2 or toxic_categories.get("toxic", 0) > 0.1):
            # Lower thresholds to make OpenAI more likely to be used
            openai_scores = self.detect_with_openai(text)
            if openai_scores:
                # For categories not detected by toxic-bert, use OpenAI scores directly
                category_scores["self_harm"] = openai_scores.get("self_harm", 0)
                category_scores["misinformation"] = openai_scores.get("misinformation", 0)
                
                # For categories detected by both models, use weighted average
                if "hate_speech" in openai_scores:
                    category_scores["hate_speech"] = (
                        category_scores["hate_speech"] * 0.5 + 
                        openai_scores.get("hate_speech", 0) * 0.5
                    )
                
                if "cyberbullying" in openai_scores:
                    category_scores["cyberbullying"] = (
                        category_scores["cyberbullying"] * 0.5 + 
                        openai_scores.get("cyberbullying", 0) * 0.5
                    )
                
                if "threats" in openai_scores:
                    category_scores["threats"] = (
                        category_scores["threats"] * 0.5 + 
                        openai_scores.get("threats", 0) * 0.5
                    )
                
                if "sexual_content" in openai_scores:
                    category_scores["sexual_content"] = (
                        category_scores["sexual_content"] * 0.5 + 
                        openai_scores.get("sexual_content", 0) * 0.5
                    )
        
        # Recalculate toxic score based on the combined scores from both models
        recalculated_toxic_score = max(
            toxic_score,  # Original toxic-bert score
            max(category_scores.values())  # Highest category score after combining models
        )
        
        # Determine primary harm type
        primary_harm_type = "None"
        max_harm_score = 0
        
        for category, score in category_scores.items():
            if score > max_harm_score and score >= 0.3:  # Minimum threshold
                max_harm_score = score
                primary_harm_type = category
        
        # Set overall threat level based on recalculated toxicity
        if recalculated_toxic_score > 0.7:
            threat_level = "High"
        elif recalculated_toxic_score > 0.4:
            threat_level = "Medium"
        else:
            threat_level = "Low"
            
        return {
            "toxic_score": recalculated_toxic_score,
            "threat_level": threat_level,
            "primary_harm_type": primary_harm_type,
            "category_scores": category_scores
        }