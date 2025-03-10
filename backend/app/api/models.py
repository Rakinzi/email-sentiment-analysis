# app/api/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class TextInput(BaseModel):
    content: str

class EmailInput(BaseModel):
    raw_email: str

class SentimentScores(BaseModel):
    neg: float
    neu: float
    pos: float
    compound: float

class HarmCategoryScores(BaseModel):
    hate_speech: float
    cyberbullying: float
    threats: float
    self_harm: float
    sexual_content: float
    misinformation: float

class ThreatResponse(BaseModel):
    content: str
    sentiment_scores: SentimentScores
    threat_level: str

class HarmfulContentResponse(BaseModel):
    content: str
    sentiment_scores: SentimentScores
    toxic_score: float
    threat_level: str
    primary_harm_type: str
    category_scores: HarmCategoryScores

class EmailThreatResponse(ThreatResponse):
    subject: str
    sender: str

class EmailHarmfulContentResponse(HarmfulContentResponse):
    subject: str
    sender: str

class ThreatDisplay(BaseModel):
    id: int
    content: str
    negative_score: float
    threat_level: str
    timestamp: datetime
    toxic_score: Optional[float] = None
    primary_harm_type: Optional[str] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode in Pydantic v2.0