# app/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.database import Base, engine

def create_app():
    app = FastAPI(title="Threat Detection API")
    
    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Import routes here to ensure token is available
    from app.api.routes import get_router
    router = get_router(os.environ.get("HUGGINGFACE_TOKEN"))
    
    # Include routers
    app.include_router(router, prefix="/api")
    
    return app