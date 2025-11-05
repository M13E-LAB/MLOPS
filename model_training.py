#!/usr/bin/env python3
"""
Script d'entraînement du modèle de classification
MLOps Project - Pissenlit vs Herbe
Utilise FastAI avec tracking MLflow
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Imports ML
import torch
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from PIL import Image
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# FastAI imports
from fastai.vision.all import *
from fastai.callback.tracker import SaveModelCallback
from fastai.callback.schedule import lr_find

# MLflow imports
import mlflow
import mlflow.pytorch
from mlflow.tracking import MlflowClient

# Configuration
class Config:
    # Chemins
    DATA_DIR = Path("data")
    MODELS_DIR = Path("models")
    LOGS_DIR = Path("logs")
    
    # MLflow
    MLFLOW_TRACKING_URI = "http://localhost:5001"
    MLFLOW_EXPERIMENT_NAME = "dandelion-grass-classification"
    
    # Modèle
    MODEL_ARCH = "resnet34"  # Architecture par défaut
    IMAGE_SIZE = 224
    BATCH_SIZE = 32
    EPOCHS = 10
    LEARNING_RATE = 1e-3
    
    # Validation
    VALID_PCT = 0.2
    SEED = 42

def setup_mlflow():
    """Configurer MLflow pour le tracking"""
    logger.info("🔧 Configuration de MLflow...")
    
    # Configuration de l'URI de tracking
    mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
    
    # Créer ou récupérer l'expérience
    try:
        experiment = mlflow.get_experiment_by_name(Config.MLFLOW_EXPERIMENT_NAME)
        if experiment is None:
            experiment_id = mlflow.create_experiment(Config.MLFLOW_EXPERIMENT_NAME)
            logger.info(f"✅ Expérience créée: {Config.MLFLOW_EXPERIMENT_NAME}")
        else:
            experiment_id = experiment.experiment_id
            logger.info(f"✅ Expérience existante: {Config.MLFLOW_EXPERIMENT_NAME}")
        
        mlflow.set_experiment(Config.MLFLOW_EXPERIMENT_NAME)
        return experiment_id
        
    except Exception as e:
        logger.error(f"❌ Erreur configuration MLflow: {e}")
        return None

def prepare_data():
    """Préparer les données pour l'entraînement"""
    logger.info("📊 Préparation des données...")
    
    # Vérifier que les données existent
    dandelion_dir = Config.DATA_DIR / "dandelion"
    grass_dir = Config.DATA_DIR / "grass"
    
    if not dandelion_dir.exists() or not grass_dir.exists():
        logger.error("❌ Dossiers de données non trouvés. Exécutez d'abord download_data.py")
        return None
    
    # Compter les images
    dandelion_count = len(list(dandelion_dir.glob("*.jpg")))
    grass_count = len(list(grass_dir.glob("*.jpg")))
    
    logger.info(f"📈 Dataset: {dandelion_count} pissenlits, {grass_count} herbe")
    
    # Créer le DataBlock FastAI
    dblock = DataBlock(
        blocks=(ImageBlock, CategoryBlock),
        get_items=get_image_files,
        splitter=RandomSplitter(valid_pct=Config.VALID_PCT, seed=Config.SEED),
        get_y=parent_label,
        item_tfms=Resize(Config.IMAGE_SIZE),
        batch_tfms=aug_transforms(
            size=Config.IMAGE_SIZE,
            min_scale=0.8,
            max_rotate=15,
            max_lighting=0.3,
            max_warp=0.2,
            p_affine=0.8,
            p_lighting=0.8
        )
    )
    
    # Créer les DataLoaders
    dls = dblock.dataloaders(Config.DATA_DIR, bs=Config.BATCH_SIZE)
    
    logger.info(f"✅ DataLoaders créés: {len(dls.train_ds)} train, {len(dls.valid_ds)} validation")
    
    return dls

def create_model(dls, arch_name="resnet34"):
    """Créer le modèle de classification"""
    logger.info(f"🏗️ Création du modèle {arch_name}...")
    
    # Architectures disponibles
    architectures = {
        "resnet18": resnet18,
        "resnet34": resnet34,
        "resnet50": resnet50,
        "efficientnet_b0": efficientnet_b0,
        "vgg16_bn": vgg16_bn,
    }
    
    if arch_name not in architectures:
        logger.warning(f"⚠️ Architecture {arch_name} non supportée, utilisation de resnet34")
        arch_name = "resnet34"
    
    arch = architectures[arch_name]
    
    # Créer le learner
    learn = vision_learner(
        dls, 
        arch, 
        metrics=[accuracy, error_rate],
        model_dir=Config.MODELS_DIR
    )
    
    logger.info(f"✅ Modèle {arch_name} créé avec {len(dls.vocab)} classes: {dls.vocab}")
    
    return learn

def train_model(learn, epochs=None):
    """Entraîner le modèle"""
    if epochs is None:
        epochs = Config.EPOCHS
        
    logger.info(f"🚀 Début de l'entraînement ({epochs} époques)...")
    
    # Recherche du taux d'apprentissage optimal
    logger.info("🔍 Recherche du taux d'apprentissage optimal...")
    lr_result = learn.lr_find()
    suggested_lr = lr_result.valley if hasattr(lr_result, 'valley') else 1e-3
    
    logger.info(f"📊 LR suggéré: {suggested_lr:.2e}")
    
    # Entraînement avec fine-tuning
    logger.info("🎯 Phase 1: Entraînement de la tête du modèle...")
    learn.fit_one_cycle(epochs//2, lr_max=suggested_lr)
    
    logger.info("🎯 Phase 2: Fine-tuning de tout le modèle...")
    learn.unfreeze()
    learn.fit_one_cycle(epochs//2, lr_max=suggested_lr/10)
    
    logger.info("✅ Entraînement terminé!")
    
    return learn

def evaluate_model(learn):
    """Évaluer les performances du modèle"""
    logger.info("📊 Évaluation du modèle...")
    
    # Prédictions sur le set de validation
    preds, targets = learn.get_preds()
    preds_class = preds.argmax(dim=1)
    
    # Métriques
    accuracy = accuracy_score(targets, preds_class)
    precision, recall, f1, _ = precision_recall_fscore_support(targets, preds_class, average='weighted')
    
    # Matrice de confusion
    cm = confusion_matrix(targets, preds_class)
    
    # Métriques par classe
    class_names = learn.dls.vocab
    precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
        targets, preds_class, average=None, labels=range(len(class_names))
    )
    
    metrics = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'confusion_matrix': cm.tolist(),
        'class_metrics': {
            class_names[i]: {
                'precision': float(precision_per_class[i]),
                'recall': float(recall_per_class[i]),
                'f1_score': float(f1_per_class[i])
            }
            for i in range(len(class_names))
        }
    }
    
    logger.info(f"📈 Résultats:")
    logger.info(f"   Accuracy: {accuracy:.4f}")
    logger.info(f"   Precision: {precision:.4f}")
    logger.info(f"   Recall: {recall:.4f}")
    logger.info(f"   F1-Score: {f1:.4f}")
    
    return metrics

def create_visualizations(learn, metrics):
    """Créer des visualisations des résultats"""
    logger.info("🎨 Création des visualisations...")
    
    # Créer le dossier de visualisations
    viz_dir = Path("visualizations")
    viz_dir.mkdir(exist_ok=True)
    
    # 1. Matrice de confusion
    plt.figure(figsize=(8, 6))
    cm = np.array(metrics['confusion_matrix'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=learn.dls.vocab, yticklabels=learn.dls.vocab)
    plt.title('Matrice de Confusion')
    plt.ylabel('Vraie classe')
    plt.xlabel('Classe prédite')
    plt.tight_layout()
    plt.savefig(viz_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Courbes d'entraînement
    try:
        learn.recorder.plot_loss()
        plt.savefig(viz_dir / 'training_loss.png', dpi=300, bbox_inches='tight')
        plt.close()
    except:
        logger.warning("⚠️ Impossible de créer le graphique des pertes")
    
    # 3. Exemples de prédictions
    try:
        learn.show_results(max_n=9, figsize=(12, 8))
        plt.savefig(viz_dir / 'predictions_examples.png', dpi=300, bbox_inches='tight')
        plt.close()
    except:
        logger.warning("⚠️ Impossible de créer les exemples de prédictions")
    
    # 4. Métriques par classe
    plt.figure(figsize=(10, 6))
    classes = list(metrics['class_metrics'].keys())
    precision_scores = [metrics['class_metrics'][c]['precision'] for c in classes]
    recall_scores = [metrics['class_metrics'][c]['recall'] for c in classes]
    f1_scores = [metrics['class_metrics'][c]['f1_score'] for c in classes]
    
    x = np.arange(len(classes))
    width = 0.25
    
    plt.bar(x - width, precision_scores, width, label='Precision', alpha=0.8)
    plt.bar(x, recall_scores, width, label='Recall', alpha=0.8)
    plt.bar(x + width, f1_scores, width, label='F1-Score', alpha=0.8)
    
    plt.xlabel('Classes')
    plt.ylabel('Score')
    plt.title('Métriques par Classe')
    plt.xticks(x, classes)
    plt.legend()
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(viz_dir / 'class_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Visualisations sauvegardées dans {viz_dir}")
    return viz_dir

def log_to_mlflow(learn, metrics, viz_dir, hyperparams):
    """Logger les résultats dans MLflow"""
    logger.info("📝 Logging des résultats dans MLflow...")
    
    with mlflow.start_run() as run:
        # Log des hyperparamètres
        mlflow.log_params(hyperparams)
        
        # Log des métriques
        mlflow.log_metrics({
            'accuracy': metrics['accuracy'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score']
        })
        
        # Log des métriques par classe
        for class_name, class_metrics in metrics['class_metrics'].items():
            mlflow.log_metrics({
                f'{class_name}_precision': class_metrics['precision'],
                f'{class_name}_recall': class_metrics['recall'],
                f'{class_name}_f1_score': class_metrics['f1_score']
            })
        
        # Log du modèle
        model_path = "model"
        learn.export(f"{model_path}.pkl")
        mlflow.log_artifact(f"{model_path}.pkl")
        
        # Log des visualisations
        for viz_file in viz_dir.glob("*.png"):
            mlflow.log_artifact(str(viz_file))
        
        # Log des métadonnées
        mlflow.log_dict(metrics, "metrics.json")
        
        # Enregistrer le modèle dans le Model Registry
        model_name = "dandelion-grass-classifier"
        
        # Sauvegarder le modèle FastAI localement puis l'enregistrer
        learn.export(f"{model_path}/model.pkl")
        mlflow.log_artifact(f"{model_path}/model.pkl", "model")
        
        # Enregistrer aussi le modèle PyTorch sous-jacent
        mlflow.pytorch.log_model(
            learn.model, 
            "pytorch_model",
            registered_model_name=model_name
        )
        
        run_id = run.info.run_id
        logger.info(f"✅ Run MLflow: {run_id}")
        
        return run_id

def main():
    """Fonction principale"""
    logger.info("🚀 Début du pipeline d'entraînement MLOps")
    
    # Créer les dossiers nécessaires
    Config.MODELS_DIR.mkdir(exist_ok=True)
    Config.LOGS_DIR.mkdir(exist_ok=True)
    
    # Configuration MLflow
    experiment_id = setup_mlflow()
    if experiment_id is None:
        logger.error("❌ Impossible de configurer MLflow")
        return
    
    # Préparation des données
    dls = prepare_data()
    if dls is None:
        return
    
    # Hyperparamètres
    hyperparams = {
        'architecture': Config.MODEL_ARCH,
        'image_size': Config.IMAGE_SIZE,
        'batch_size': Config.BATCH_SIZE,
        'epochs': Config.EPOCHS,
        'learning_rate': Config.LEARNING_RATE,
        'valid_pct': Config.VALID_PCT,
        'seed': Config.SEED,
        'train_size': len(dls.train_ds),
        'valid_size': len(dls.valid_ds),
        'num_classes': len(dls.vocab),
        'classes': str(dls.vocab)
    }
    
    logger.info(f"🔧 Hyperparamètres: {hyperparams}")
    
    # Création et entraînement du modèle
    learn = create_model(dls, Config.MODEL_ARCH)
    learn = train_model(learn, Config.EPOCHS)
    
    # Évaluation
    metrics = evaluate_model(learn)
    
    # Visualisations
    viz_dir = create_visualizations(learn, metrics)
    
    # Logging MLflow
    run_id = log_to_mlflow(learn, metrics, viz_dir, hyperparams)
    
    # Sauvegarder le modèle localement
    model_filename = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
    learn.export(Config.MODELS_DIR / model_filename)
    logger.info(f"💾 Modèle sauvegardé: {model_filename}")
    
    logger.info("🎉 Pipeline d'entraînement terminé avec succès!")
    logger.info(f"📊 Accuracy finale: {metrics['accuracy']:.4f}")
    logger.info(f"🔗 MLflow Run: {run_id}")

if __name__ == "__main__":
    # Installation des dépendances si nécessaire
    try:
        import fastai
        import mlflow
    except ImportError:
        logger.info("📦 Installation des dépendances ML...")
        os.system("pip install fastai mlflow torch torchvision scikit-learn matplotlib seaborn")
        import fastai
        import mlflow
    
    main()
