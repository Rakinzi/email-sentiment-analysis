# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import os
import json
from datetime import datetime



from app.database import get_db, Threat, EmailAttempt
from app.api.models import (
    TextInput, 
    ThreatResponse, 
    ThreatDisplay, 
    EmailInput, 
    EmailThreatResponse,
    HarmfulContentResponse,
    EmailHarmfulContentResponse,
    
)
from app.services.sentiment import analyze_sentiment
from app.services.email_processor import parse_email_content
from app.services.harmful_content_detector import HarmfulContentDetector
from app.services.send_gmail import send_email_via_gmail
from app.services.kaggle_content_detector import KaggleContentDetector

def get_router(hf_token=None):
    router = APIRouter()
    
    # Initialize with OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY") or "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"
    harmful_detector = HarmfulContentDetector(openai_api_key=openai_api_key)
    
    kaggle_detector = KaggleContentDetector()
    
    @router.post("/analyze", response_model=HarmfulContentResponse)
    def analyze_text(text_input: TextInput, db: Session = Depends(get_db)):
        content = text_input.content
        
        # Get sentiment scores from the original approach
        sentiment_scores, _ = analyze_sentiment(content)
        
        # Get harmful content analysis, forcing OpenAI usage
        harm_analysis = harmful_detector.detect_harmful_content(content, force_openai=True)
        
        # Create new threat record
        db_threat = Threat(
            content=content,
            negative_score=sentiment_scores["neg"],
            toxic_score=harm_analysis["toxic_score"],
            threat_level=harm_analysis["threat_level"],
            primary_harm_type=harm_analysis["primary_harm_type"],
            hate_speech_score=harm_analysis["category_scores"]["hate_speech"],
            cyberbullying_score=harm_analysis["category_scores"]["cyberbullying"],
            threats_score=harm_analysis["category_scores"]["threats"],
            self_harm_score=harm_analysis["category_scores"]["self_harm"],
            sexual_content_score=harm_analysis["category_scores"]["sexual_content"],
            misinformation_score=harm_analysis["category_scores"]["misinformation"]
        )
        
        # Save to database
        db.add(db_threat)
        db.commit()
        db.refresh(db_threat)
        
        return {
            "content": content,
            "sentiment_scores": sentiment_scores,
            "toxic_score": harm_analysis["toxic_score"],
            "threat_level": harm_analysis["threat_level"],
            "primary_harm_type": harm_analysis["primary_harm_type"],
            "category_scores": harm_analysis["category_scores"]
        }

    @router.get("/threats", response_model=List[ThreatDisplay])
    def get_threats(db: Session = Depends(get_db)):
        threats = db.query(Threat).order_by(Threat.timestamp.desc()).limit(20).all()
        return threats

    @router.post("/analyze-email", response_model=EmailHarmfulContentResponse)
    def analyze_email(email_input: EmailInput, db: Session = Depends(get_db)):
        # Parse the email
        email_data = parse_email_content(email_input.raw_email)
        
        # Extract content to analyze (subject + body)
        content_to_analyze = email_data["full_content"]
        
        # Get sentiment scores from the original approach
        sentiment_scores, _ = analyze_sentiment(content_to_analyze)
        
        # Get harmful content analysis, forcing OpenAI usage
        harm_analysis = harmful_detector.detect_harmful_content(content_to_analyze, force_openai=True)
        
        # Create new threat record
        db_threat = Threat(
            content=content_to_analyze,
            negative_score=sentiment_scores["neg"],
            toxic_score=harm_analysis["toxic_score"],
            threat_level=harm_analysis["threat_level"],
            primary_harm_type=harm_analysis["primary_harm_type"],
            hate_speech_score=harm_analysis["category_scores"]["hate_speech"],
            cyberbullying_score=harm_analysis["category_scores"]["cyberbullying"],
            threats_score=harm_analysis["category_scores"]["threats"],
            self_harm_score=harm_analysis["category_scores"]["self_harm"],
            sexual_content_score=harm_analysis["category_scores"]["sexual_content"],
            misinformation_score=harm_analysis["category_scores"]["misinformation"]
        )
        
        # Save to database
        db.add(db_threat)
        db.commit()
        db.refresh(db_threat)
        
        return {
            "content": content_to_analyze,
            "sentiment_scores": sentiment_scores,
            "toxic_score": harm_analysis["toxic_score"],
            "threat_level": harm_analysis["threat_level"],
            "primary_harm_type": harm_analysis["primary_harm_type"],
            "category_scores": harm_analysis["category_scores"],
            "subject": email_data["subject"],
            "sender": email_data["from"]
        }

    @router.post("/quick-analyze")
    def quick_analyze(text_input: TextInput):
        content = text_input.content
        
        # Make sure quick analysis also uses OpenAI
        harm_analysis = harmful_detector.detect_harmful_content(content, force_openai=True)
        
        return {
            "content": content,
            "toxic_score": harm_analysis["toxic_score"],
            "threat_level": harm_analysis["threat_level"],
            "primary_harm_type": harm_analysis["primary_harm_type"],
            "category_scores": harm_analysis["category_scores"],
            "should_block": harm_analysis["threat_level"] in ["Medium", "High"]  # Updated to block Medium too
        }
    @router.post("/analyze-openai")
    def analyze_with_openai(text_input: TextInput):
        content = text_input.content
        
        # Use just OpenAI directly
        openai_scores = harmful_detector.detect_with_openai(content)
        
        if not openai_scores:
            return {
                "content": content,
                "error": "OpenAI analysis failed or returned no results",
                "fallback": "Using only toxic-bert results instead"
            }
        
        # Calculate threat level based on OpenAI scores
        max_score = max(openai_scores.values())
        if max_score > 0.7:
            threat_level = "High"
        elif max_score > 0.4:
            threat_level = "Medium"
        else:
            threat_level = "Low"
            
        return {
            "content": content,
            "openai_analysis": openai_scores,
            "threat_level": threat_level,
            "primary_harm_type": max(openai_scores, key=openai_scores.get) if max_score > 0.3 else "None"
        }

    @router.get("/threat-stats")
    def get_threat_stats(db: Session = Depends(get_db)):
        # Get total count
        total_count = db.query(Threat).count()
        
        # Get count by threat level
        high_count = db.query(Threat).filter(Threat.threat_level == "High").count()
        medium_count = db.query(Threat).filter(Threat.threat_level == "Medium").count()
        low_count = db.query(Threat).filter(Threat.threat_level == "Low").count()
        
        # Get count by primary harm type
        harm_types = ["hate_speech", "cyberbullying", "threats", "self_harm", "sexual_content", "misinformation", "None"]
        harm_type_counts = {}
        
        for harm_type in harm_types:
            count = db.query(Threat).filter(Threat.primary_harm_type == harm_type).count()
            harm_type_counts[harm_type] = count
        
        return {
            "total_analyzed": total_count,
            "by_threat_level": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "by_harm_type": harm_type_counts
        }
        
    @router.post("/send-email")
    def send_email(
        recipient: str = Form(...),
        subject: str = Form(...),
        body: str = Form(...),
        sender: str = Form(None),  # Make sender optional
        db: Session = Depends(get_db)
    ):
        """
        Send an email with content analysis
        """
        # Use configured Gmail address if sender not provided
        sender_email = sender or os.environ.get("GMAIL_EMAIL")
        
        if not sender_email:
            return {
                "status": "error",
                "message": "Sender email not configured"
            }
        
        # Compose full email content for analysis
        content_to_analyze = f"From: {sender_email}\nTo: {recipient}\nSubject: {subject}\n\n{body}"
        
        # Analyze for harmful content
        harm_analysis = harmful_detector.detect_harmful_content(content_to_analyze, force_openai=True)
        
        # Record the attempt in the database (whether blocked or not)
        email_attempt = EmailAttempt(
            sender=sender_email,
            recipient=recipient,
            subject=subject,
            content=body,
            full_content=content_to_analyze,
            toxic_score=harm_analysis["toxic_score"],
            threat_level=harm_analysis["threat_level"],
            primary_harm_type=harm_analysis["primary_harm_type"],
            was_blocked=harm_analysis["threat_level"] in ["Medium", "High"],  # Block both Medium and High
            timestamp=datetime.now()
        )
        db.add(email_attempt)
        db.commit()
        db.refresh(email_attempt)
        
        # Determine if it should be blocked - now includes Medium threat level
        should_block = harm_analysis["threat_level"] in ["Medium", "High"]
        
        if should_block:
            return {
                "status": "blocked",
                "reason": f"Email blocked due to {harm_analysis['primary_harm_type']} content (Threat Level: {harm_analysis['threat_level']})",
                "analysis": harm_analysis,
                "message_id": email_attempt.id
            }
        
        # If content is clean (Low threat), actually send the email
        # Get Gmail app password from environment variable
        gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
        
        if not gmail_app_password:
            return {
                "status": "error",
                "message": "SMTP credentials not configured. Email would have been sent.",
                "analysis": harm_analysis,
                "message_id": email_attempt.id
            }
        
        # Send the email
        email_result = send_email_via_gmail(
            sender_email=sender_email,
            recipient_email=recipient,
            subject=subject,
            message_body=body,
            app_password=gmail_app_password
        )
        
        if email_result is True:
            return {
                "status": "sent",
                "message": "Email passed content checks and was sent successfully",
                "analysis": harm_analysis,
                "message_id": email_attempt.id
            }
        else:
            return {
                "status": "error",
                "message": f"Email passed content checks but failed to send: {email_result if isinstance(email_result, str) else 'Unknown error'}",
                "analysis": harm_analysis,
                "message_id": email_attempt.id
            }
            
    @router.post("/analyze-kaggle")
    def analyze_with_kaggle(text_input: TextInput):
        content = text_input.content
        
        # Get analysis from Kaggle models
        kaggle_analysis = kaggle_detector.detect_harmful_content(content)
        
        return {
            "content": content,
            "kaggle_analysis": kaggle_analysis,
            "should_block": kaggle_analysis["threat_level"] in ["Medium", "High"]
        }
        
    @router.post("/log-email-attempt")
    def log_email_attempt(data: dict, db: Session = Depends(get_db)):
        """
        Log an email attempt to the database
        """
        email_attempt = EmailAttempt(
            sender=data.get("sender", ""),
            recipient=data.get("recipient", ""),
            subject=data.get("subject", ""),
            content=data.get("content", ""),
            full_content=f"From: {data.get('sender', '')}\nTo: {data.get('recipient', '')}\nSubject: {data.get('subject', '')}\n\n{data.get('content', '')}",
            toxic_score=0.5,  # This is just a placeholder, ideally you'd get this from the analysis
            threat_level=data.get("threat_level", "Unknown"),
            primary_harm_type=data.get("primary_harm_type", "Unknown"),
            was_blocked=data.get("was_blocked", False),
            timestamp=datetime.now()
        )
        
        db.add(email_attempt)
        db.commit()
        db.refresh(email_attempt)
        
        return {"status": "success", "message": "Email attempt logged", "id": email_attempt.id}
            
    return router