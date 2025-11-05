#!/usr/bin/env python3
"""
API FastAPI pour la classification d'images
MLOps Project - Pissenlit vs Herbe
"""

import os
import sys
import logging
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import io

# FastAPI imports
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# ML imports
import torch
from fastai.vision.all import *
from PIL import Image
import numpy as np

# Monitoring imports
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import psutil

# Database imports
import mysql.connector
from mysql.connector import Error

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
class Config:
    MODEL_PATH = Path("../model.pkl")
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    IMAGE_SIZE = 224
    
    # Base de données
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "mlops_db")
    DB_USER = os.getenv("DB_USER", "mlops_app")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mlops_app_password")
    
    # API
    API_VERSION = "1.0.0"
    API_TITLE = "MLOps Image Classification API"
    API_DESCRIPTION = "API pour la classification d'images pissenlit vs herbe"

# Métriques Prometheus
try:
    PREDICTION_COUNTER = Counter('predictions_total', 'Total number of predictions', ['model_version', 'predicted_class'])
    PREDICTION_HISTOGRAM = Histogram('prediction_duration_seconds', 'Time spent on predictions')
    ERROR_COUNTER = Counter('prediction_errors_total', 'Total number of prediction errors', ['error_type'])
    MODEL_INFO = Gauge('model_info', 'Model information', ['model_version', 'model_name'])
except ValueError:
    # Métriques déjà créées, les récupérer
    from prometheus_client import REGISTRY
    PREDICTION_COUNTER = None
    PREDICTION_HISTOGRAM = None
    ERROR_COUNTER = None
    MODEL_INFO = None

# Variables globales
model_learner = None
model_version = None
model_loaded_at = None

# Initialisation de l'application FastAPI
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sécurité (optionnelle)
security = HTTPBearer(auto_error=False)

def get_db_connection():
    """Créer une connexion à la base de données"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        return connection
    except Error as e:
        logger.error(f"Erreur connexion DB: {e}")
        return None

def load_model():
    """Charger le modèle de classification"""
    global model_learner, model_version, model_loaded_at
    
    logger.info("🔄 Chargement du modèle...")
    
    if not Config.MODEL_PATH.exists():
        logger.error(f"❌ Modèle non trouvé: {Config.MODEL_PATH}")
        return False
    
    try:
        # Charger le modèle FastAI
        model_learner = load_learner(Config.MODEL_PATH)
        model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_loaded_at = datetime.now()
        
        # Mettre à jour les métriques
        MODEL_INFO.labels(model_version=model_version, model_name="dandelion-grass-classifier").set(1)
        
        logger.info(f"✅ Modèle chargé: {model_version}")
        logger.info(f"📊 Classes disponibles: {model_learner.dls.vocab}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur chargement modèle: {e}")
        return False

def validate_image(file: UploadFile) -> bool:
    """Valider le fichier image uploadé"""
    # Vérifier l'extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée. Extensions autorisées: {Config.ALLOWED_EXTENSIONS}"
        )
    
    # Vérifier la taille (sera vérifié lors de la lecture)
    return True

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """Préprocesser l'image pour la prédiction"""
    try:
        # Ouvrir l'image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convertir en RGB si nécessaire
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Vérifier les dimensions minimales
        if image.size[0] < 32 or image.size[1] < 32:
            raise HTTPException(status_code=400, detail="Image trop petite (minimum 32x32 pixels)")
        
        return image
        
    except Exception as e:
        logger.error(f"Erreur preprocessing: {e}")
        raise HTTPException(status_code=400, detail=f"Erreur traitement image: {str(e)}")

def log_prediction(request_id: str, prediction_data: Dict[str, Any]):
    """Logger la prédiction dans la base de données"""
    try:
        connection = get_db_connection()
        if connection is None:
            return
        
        cursor = connection.cursor()
        
        query = """
        INSERT INTO api_predictions 
        (request_id, model_name, model_version, predicted_class, confidence_score, 
         prediction_time_ms, response_status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            request_id,
            "dandelion-grass-classifier",
            model_version,
            prediction_data.get('predicted_class'),
            prediction_data.get('confidence'),
            prediction_data.get('prediction_time_ms'),
            200,
            datetime.now()
        )
        
        cursor.execute(query, values)
        connection.commit()
        
    except Error as e:
        logger.error(f"Erreur logging DB: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Routes de l'API

@app.on_event("startup")
async def startup_event():
    """Événement de démarrage de l'application"""
    logger.info("🚀 Démarrage de l'API MLOps...")
    
    # Charger le modèle
    if not load_model():
        logger.error("❌ Impossible de charger le modèle")
        sys.exit(1)
    
    logger.info("✅ API prête!")

@app.get("/")
async def root():
    """Route racine avec informations sur l'API"""
    return {
        "message": "MLOps Image Classification API",
        "version": Config.API_VERSION,
        "model_version": model_version,
        "model_loaded_at": model_loaded_at.isoformat() if model_loaded_at else None,
        "available_classes": list(model_learner.dls.vocab) if model_learner else [],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de santé de l'API"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": Config.API_VERSION,
        "model_loaded": model_learner is not None,
        "model_version": model_version
    }
    
    # Vérifier la connexion à la base de données
    db_connection = get_db_connection()
    health_status["database_connected"] = db_connection is not None
    if db_connection:
        db_connection.close()
    
    # Vérifier l'utilisation des ressources
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    return health_status

@app.get("/metrics")
async def get_metrics():
    """Endpoint pour les métriques Prometheus"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/predict")
async def predict_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Prédire la classe d'une image uploadée
    
    - **file**: Image à classifier (formats supportés: JPG, PNG, BMP, TIFF)
    - Retourne la classe prédite avec le score de confiance
    """
    
    if model_learner is None:
        ERROR_COUNTER.labels(error_type="model_not_loaded").inc()
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    
    # Générer un ID unique pour la requête
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Valider le fichier
        validate_image(file)
        
        # Lire le contenu du fichier
        image_bytes = await file.read()
        
        # Vérifier la taille
        if len(image_bytes) > Config.MAX_FILE_SIZE:
            ERROR_COUNTER.labels(error_type="file_too_large").inc()
            raise HTTPException(
                status_code=413, 
                detail=f"Fichier trop volumineux (max: {Config.MAX_FILE_SIZE // (1024*1024)}MB)"
            )
        
        # Préprocesser l'image
        image = preprocess_image(image_bytes)
        
        # Faire la prédiction
        with PREDICTION_HISTOGRAM.time():
            pred_class, pred_idx, pred_probs = model_learner.predict(image)
        
        # Calculer le temps de prédiction
        prediction_time_ms = int((time.time() - start_time) * 1000)
        
        # Préparer la réponse
        confidence = float(pred_probs[pred_idx])
        predicted_class = str(pred_class)
        
        response_data = {
            "request_id": request_id,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "all_probabilities": {
                str(class_name): float(prob) 
                for class_name, prob in zip(model_learner.dls.vocab, pred_probs)
            },
            "model_version": model_version,
            "prediction_time_ms": prediction_time_ms,
            "timestamp": datetime.now().isoformat()
        }
        
        # Mettre à jour les métriques
        PREDICTION_COUNTER.labels(
            model_version=model_version, 
            predicted_class=predicted_class
        ).inc()
        
        # Logger la prédiction en arrière-plan
        background_tasks.add_task(log_prediction, request_id, response_data)
        
        logger.info(f"✅ Prédiction {request_id}: {predicted_class} ({confidence:.3f})")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        ERROR_COUNTER.labels(error_type="prediction_error").inc()
        logger.error(f"❌ Erreur prédiction {request_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.post("/predict/batch")
async def predict_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Prédire la classe de plusieurs images en lot
    
    - **files**: Liste d'images à classifier
    - Retourne les prédictions pour chaque image
    """
    
    if model_learner is None:
        ERROR_COUNTER.labels(error_type="model_not_loaded").inc()
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    
    if len(files) > 10:  # Limiter le nombre d'images par batch
        raise HTTPException(status_code=400, detail="Maximum 10 images par batch")
    
    batch_id = str(uuid.uuid4())
    results = []
    
    for i, file in enumerate(files):
        try:
            # Réutiliser la logique de prédiction simple
            validate_image(file)
            image_bytes = await file.read()
            
            if len(image_bytes) > Config.MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "error": "Fichier trop volumineux"
                })
                continue
            
            image = preprocess_image(image_bytes)
            pred_class, pred_idx, pred_probs = model_learner.predict(image)
            
            results.append({
                "filename": file.filename,
                "predicted_class": str(pred_class),
                "confidence": float(pred_probs[pred_idx]),
                "all_probabilities": {
                    str(class_name): float(prob) 
                    for class_name, prob in zip(model_learner.dls.vocab, pred_probs)
                }
            })
            
            PREDICTION_COUNTER.labels(
                model_version=model_version, 
                predicted_class=str(pred_class)
            ).inc()
            
        except Exception as e:
            ERROR_COUNTER.labels(error_type="batch_prediction_error").inc()
            results.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "batch_id": batch_id,
        "model_version": model_version,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }

@app.get("/model/info")
async def get_model_info():
    """Obtenir des informations sur le modèle actuel"""
    if model_learner is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    
    return {
        "model_version": model_version,
        "model_loaded_at": model_loaded_at.isoformat(),
        "classes": list(model_learner.dls.vocab),
        "num_classes": len(model_learner.dls.vocab),
        "model_path": str(Config.MODEL_PATH),
        "image_size": Config.IMAGE_SIZE
    }

@app.post("/model/reload")
async def reload_model(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Recharger le modèle (utile après un nouveau déploiement)"""
    logger.info("🔄 Rechargement du modèle demandé...")
    
    if load_model():
        return {
            "message": "Modèle rechargé avec succès",
            "model_version": model_version,
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=500, detail="Erreur lors du rechargement du modèle")

if __name__ == "__main__":
    # Configuration pour le développement
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
