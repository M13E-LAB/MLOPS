#!/usr/bin/env python3
"""
Application Web Streamlit pour la classification d'images
MLOps Project - Pissenlit vs Herbe
"""

import streamlit as st
import requests
import json
from PIL import Image
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import mysql.connector
from mysql.connector import Error
import os
import base64

# Configuration de la page
st.set_page_config(
    page_title="🌼 MLOps Image Classifier",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
class Config:
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "mlops_db")
    DB_USER = os.getenv("DB_USER", "mlops_readonly")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "mlops_readonly_password")

# Fonctions utilitaires
@st.cache_data(ttl=300)  # Cache pendant 5 minutes
def get_api_health():
    """Vérifier l'état de l'API"""
    try:
        response = requests.get(f"{Config.API_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@st.cache_data(ttl=300)
def get_model_info():
    """Obtenir les informations du modèle"""
    try:
        response = requests.get(f"{Config.API_URL}/model/info", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

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
        st.error(f"Erreur connexion DB: {e}")
        return None

@st.cache_data(ttl=60)  # Cache pendant 1 minute
def get_prediction_stats():
    """Récupérer les statistiques des prédictions"""
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Statistiques générales
        query = """
        SELECT 
            COUNT(*) as total_predictions,
            COUNT(DISTINCT DATE(created_at)) as active_days,
            AVG(prediction_time_ms) as avg_prediction_time,
            AVG(confidence_score) as avg_confidence
        FROM api_predictions 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """
        cursor.execute(query)
        general_stats = cursor.fetchone()
        
        # Prédictions par classe
        query = """
        SELECT 
            predicted_class,
            COUNT(*) as count,
            AVG(confidence_score) as avg_confidence
        FROM api_predictions 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY predicted_class
        """
        cursor.execute(query)
        class_stats = cursor.fetchall()
        
        # Prédictions par jour
        query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as predictions,
            AVG(confidence_score) as avg_confidence
        FROM api_predictions 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        cursor.execute(query)
        daily_stats = cursor.fetchall()
        
        return {
            'general': general_stats,
            'by_class': class_stats,
            'daily': daily_stats
        }
        
    except Error as e:
        st.error(f"Erreur requête DB: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def predict_image(image_file):
    """Envoyer une image à l'API pour prédiction"""
    try:
        files = {"file": ("image.jpg", image_file, "image/jpeg")}
        response = requests.post(f"{Config.API_URL}/predict", files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Erreur lors de la prédiction: {e}")
        return None

def create_confidence_chart(probabilities):
    """Créer un graphique de confiance"""
    classes = list(probabilities.keys())
    confidences = list(probabilities.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=classes,
            y=confidences,
            marker_color=['#FF6B6B' if conf == max(confidences) else '#4ECDC4' for conf in confidences],
            text=[f'{conf:.3f}' for conf in confidences],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Scores de Confiance par Classe",
        xaxis_title="Classes",
        yaxis_title="Score de Confiance",
        yaxis=dict(range=[0, 1]),
        height=400
    )
    
    return fig

# Interface utilisateur
def main():
    # Titre principal
    st.title("🌼 MLOps Image Classifier")
    st.markdown("**Classification automatique: Pissenlit vs Herbe**")
    
    # Sidebar avec informations système
    with st.sidebar:
        st.header("📊 État du Système")
        
        # Vérifier l'état de l'API
        api_health = get_api_health()
        if api_health:
            st.success("✅ API en ligne")
            st.json(api_health)
        else:
            st.error("❌ API hors ligne")
        
        # Informations du modèle
        model_info = get_model_info()
        if model_info:
            st.header("🤖 Informations du Modèle")
            st.write(f"**Version:** {model_info.get('model_version', 'N/A')}")
            st.write(f"**Classes:** {', '.join(model_info.get('classes', []))}")
            st.write(f"**Chargé le:** {model_info.get('model_loaded_at', 'N/A')}")
    
    # Onglets principaux
    tab1, tab2, tab3 = st.tabs(["🔍 Classification", "📈 Statistiques", "ℹ️ À propos"])
    
    with tab1:
        st.header("Classification d'Images")
        
        # Upload d'image
        uploaded_file = st.file_uploader(
            "Choisissez une image à classifier",
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
            help="Formats supportés: JPG, PNG, BMP, TIFF (max 10MB)"
        )
        
        if uploaded_file is not None:
            # Afficher l'image
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Image à classifier")
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Fichier: {uploaded_file.name}", use_column_width=True)
                
                # Informations sur l'image
                st.write(f"**Dimensions:** {image.size[0]} x {image.size[1]} pixels")
                st.write(f"**Mode:** {image.mode}")
                st.write(f"**Taille:** {len(uploaded_file.getvalue()) / 1024:.1f} KB")
            
            with col2:
                st.subheader("Résultats de la Classification")
                
                if st.button("🚀 Classifier l'image", type="primary"):
                    with st.spinner("Classification en cours..."):
                        # Convertir l'image en bytes
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format='JPEG')
                        img_bytes.seek(0)
                        
                        # Faire la prédiction
                        result = predict_image(img_bytes)
                        
                        if result:
                            # Afficher le résultat principal
                            predicted_class = result['predicted_class']
                            confidence = result['confidence']
                            
                            # Déterminer l'emoji et la couleur
                            if predicted_class == 'dandelion':
                                emoji = "🌼"
                                color = "#FFD700"
                            else:
                                emoji = "🌱"
                                color = "#32CD32"
                            
                            st.markdown(f"""
                            <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: {color}20; border: 2px solid {color};">
                                <h2>{emoji} {predicted_class.title()}</h2>
                                <h3>Confiance: {confidence:.1%}</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Graphique de confiance
                            st.plotly_chart(
                                create_confidence_chart(result['all_probabilities']),
                                use_container_width=True
                            )
                            
                            # Détails techniques
                            with st.expander("Détails techniques"):
                                st.json(result)
    
    with tab2:
        st.header("📈 Statistiques d'Utilisation")
        
        # Récupérer les statistiques
        stats = get_prediction_stats()
        
        if stats and stats['general']:
            general = stats['general']
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Prédictions (7j)",
                    general['total_predictions'] or 0
                )
            
            with col2:
                st.metric(
                    "Jours Actifs",
                    general['active_days'] or 0
                )
            
            with col3:
                st.metric(
                    "Temps Moyen (ms)",
                    f"{general['avg_prediction_time']:.0f}" if general['avg_prediction_time'] else "N/A"
                )
            
            with col4:
                st.metric(
                    "Confiance Moyenne",
                    f"{general['avg_confidence']:.1%}" if general['avg_confidence'] else "N/A"
                )
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                if stats['by_class']:
                    st.subheader("Prédictions par Classe")
                    df_class = pd.DataFrame(stats['by_class'])
                    
                    fig = px.pie(
                        df_class, 
                        values='count', 
                        names='predicted_class',
                        title="Distribution des Prédictions"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if stats['daily']:
                    st.subheader("Évolution Quotidienne")
                    df_daily = pd.DataFrame(stats['daily'])
                    
                    fig = px.line(
                        df_daily, 
                        x='date', 
                        y='predictions',
                        title="Prédictions par Jour"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée de prédiction disponible pour les 7 derniers jours.")
    
    with tab3:
        st.header("ℹ️ À propos du Projet")
        
        st.markdown("""
        ## 🎯 Objectif
        Ce projet MLOps démontre un pipeline complet de machine learning pour la classification d'images,
        distinguant les pissenlits de l'herbe.
        
        ## 🏗️ Architecture
        - **Données**: Images stockées dans MySQL et S3/Minio
        - **Modèle**: CNN basé sur FastAI avec transfer learning
        - **API**: FastAPI avec documentation Swagger
        - **Interface**: Application Streamlit interactive
        - **Orchestration**: Apache Airflow pour les pipelines
        - **Monitoring**: Prometheus + Grafana
        - **Déploiement**: Docker + Kubernetes
        
        ## 🚀 Fonctionnalités
        - ✅ Classification d'images en temps réel
        - ✅ API REST avec authentification
        - ✅ Interface web intuitive
        - ✅ Monitoring des performances
        - ✅ Pipeline de retraining automatique
        - ✅ Déploiement containerisé
        
        ## 📊 Métriques Surveillées
        - Précision du modèle
        - Temps de réponse API
        - Utilisation des ressources
        - Santé des services
        
        ## 🔧 Technologies Utilisées
        - **ML**: FastAI, PyTorch, MLflow
        - **Backend**: FastAPI, MySQL, Redis
        - **Frontend**: Streamlit
        - **Orchestration**: Apache Airflow
        - **Monitoring**: Prometheus, Grafana
        - **Containerisation**: Docker, Kubernetes
        - **CI/CD**: GitHub Actions
        """)
        
        # Informations techniques
        with st.expander("Informations Techniques"):
            st.code(f"""
            API URL: {Config.API_URL}
            Base de données: {Config.DB_HOST}:{Config.DB_PORT}
            Version: 1.0.0
            Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """)

if __name__ == "__main__":
    main()
