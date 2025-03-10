# app/database.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Threat(Base):
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, index=True)
    negative_score = Column(Float)
    threat_level = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Fields for harmful content detection
    toxic_score = Column(Float, nullable=True)
    primary_harm_type = Column(String, nullable=True)
    hate_speech_score = Column(Float, nullable=True)
    cyberbullying_score = Column(Float, nullable=True)
    threats_score = Column(Float, nullable=True)
    self_harm_score = Column(Float, nullable=True)
    sexual_content_score = Column(Float, nullable=True)
    misinformation_score = Column(Float, nullable=True)

class EmailAttempt(Base):
    __tablename__ = "email_attempts"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    recipient = Column(String)
    subject = Column(String)
    content = Column(String)
    full_content = Column(String)
    toxic_score = Column(Float)
    threat_level = Column(String)
    primary_harm_type = Column(String)
    was_blocked = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)