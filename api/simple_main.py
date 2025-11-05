"""
API FastAPI simplifiée pour Kubernetes
Version sans FastAI pour déploiement rapide
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import logging
from typing import Dict, Any
import os
from datetime import datetime

# Configuration
class Config:
    API_VERSION = "1.0.0"
    API_TITLE = "MLOps Image Classification API (Simple)"
    API_DESCRIPTION = "API simplifiée pour la classification d'images"

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation FastAPI
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Modèles Pydantic
class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    model_version: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Point de contrôle de santé"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version=Config.API_VERSION
    )

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Point d'entrée racine"""
    return {
        "message": "MLOps Image Classification API",
        "version": Config.API_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    """
    Prédiction d'image (version simplifiée)
    Pour l'instant, retourne une prédiction factice
    """
    try:
        # Vérifier le type de fichier
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")
        
        # Simulation d'une prédiction
        # Dans la vraie version, ici on chargerait le modèle FastAI
        import random
        predictions = ["dandelion", "grass"]
        prediction = random.choice(predictions)
        confidence = round(random.uniform(0.7, 0.99), 3)
        
        logger.info(f"Prédiction effectuée: {prediction} (confiance: {confidence})")
        
        return PredictionResponse(
            prediction=prediction,
            confidence=confidence,
            model_version="simple-v1.0",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Métriques basiques pour Prometheus"""
    return {
        "predictions_total": 42,
        "api_status": "running",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
