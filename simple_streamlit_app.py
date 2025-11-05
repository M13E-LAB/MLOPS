#!/usr/bin/env python3
"""
Application Streamlit simple pour tester le projet MLOps
"""

import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="🌼 MLOps Demo",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
class Config:
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_NAME = "mlops_db"
    DB_USER = "mlops_user"
    DB_PASSWORD = "mlops_password"
    MLFLOW_URL = "http://localhost:5001"
    MINIO_URL = "http://localhost:9001"
    PROMETHEUS_URL = "http://localhost:9090"
    GRAFANA_URL = "http://localhost:3000"

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

def check_services():
    """Vérifier l'état des services"""
    services = {
        "MySQL": {"url": f"mysql://{Config.DB_HOST}:{Config.DB_PORT}", "status": "unknown"},
        "MLflow": {"url": Config.MLFLOW_URL, "status": "unknown"},
        "Minio": {"url": Config.MINIO_URL, "status": "unknown"},
        "Prometheus": {"url": Config.PROMETHEUS_URL, "status": "unknown"},
        "Grafana": {"url": Config.GRAFANA_URL, "status": "unknown"}
    }
    
    # Test MySQL
    try:
        connection = get_db_connection()
        if connection and connection.is_connected():
            services["MySQL"]["status"] = "✅ En ligne"
            connection.close()
        else:
            services["MySQL"]["status"] = "❌ Hors ligne"
    except:
        services["MySQL"]["status"] = "❌ Hors ligne"
    
    # Test autres services
    for service_name in ["MLflow", "Minio", "Prometheus", "Grafana"]:
        try:
            url = services[service_name]["url"]
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                services[service_name]["status"] = "✅ En ligne"
            else:
                services[service_name]["status"] = "⚠️ Problème"
        except:
            services[service_name]["status"] = "❌ Hors ligne"
    
    return services

def main():
    # Titre principal
    st.title("🌼 MLOps Image Classification Demo")
    st.markdown("**Projet de classification automatique: Pissenlit vs Herbe**")
    
    # Sidebar avec état des services
    with st.sidebar:
        st.header("📊 État des Services")
        
        if st.button("🔄 Actualiser"):
            st.rerun()
        
        services = check_services()
        
        for service_name, service_info in services.items():
            st.write(f"**{service_name}**: {service_info['status']}")
            if service_info['status'] == "✅ En ligne":
                st.write(f"🔗 [{service_info['url']}]({service_info['url']})")
        
        st.markdown("---")
        st.markdown("### 🚀 Services Disponibles")
        st.markdown("- **MLflow**: http://localhost:5001")
        st.markdown("- **Minio Console**: http://localhost:9001")
        st.markdown("- **Grafana**: http://localhost:3000")
        st.markdown("- **Prometheus**: http://localhost:9090")
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Accueil", "📊 Base de Données", "🔍 Classification", "ℹ️ À propos"])
    
    with tab1:
        st.header("🎯 Bienvenue dans le projet MLOps")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Statut du Projet")
            
            # Vérifier si les données sont disponibles
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM plants_data")
                    total_images = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM plants_data WHERE download_status = 'downloaded'")
                    downloaded_images = cursor.fetchone()[0]
                    
                    st.metric("Images totales", total_images)
                    st.metric("Images téléchargées", downloaded_images)
                    
                    if total_images > 0:
                        progress = downloaded_images / total_images
                        st.progress(progress)
                        st.write(f"Progression: {progress:.1%}")
                    
                    connection.close()
                    
                except Exception as e:
                    st.error(f"Erreur base de données: {e}")
            else:
                st.warning("Base de données non accessible")
        
        with col2:
            st.subheader("🛠️ Actions Rapides")
            
            if st.button("📥 Télécharger les données", type="primary"):
                st.info("Pour télécharger les données, exécutez:")
                st.code("python download_data.py")
            
            if st.button("🤖 Entraîner le modèle"):
                st.info("Pour entraîner le modèle, exécutez:")
                st.code("python model_training.py")
            
            if st.button("🧪 Tests de charge"):
                st.info("Pour lancer les tests de charge, exécutez:")
                st.code("python -m locust -f tests/load/locustfile.py")
    
    with tab2:
        st.header("📊 Exploration de la Base de Données")
        
        connection = get_db_connection()
        if connection:
            try:
                # Statistiques générales
                st.subheader("📈 Statistiques Générales")
                
                query = """
                SELECT 
                    label,
                    download_status,
                    COUNT(*) as count
                FROM plants_data 
                GROUP BY label, download_status
                ORDER BY label, download_status
                """
                
                df = pd.read_sql(query, connection)
                
                if not df.empty:
                    # Graphique en barres
                    st.bar_chart(df.pivot(index='label', columns='download_status', values='count').fillna(0))
                    
                    # Tableau détaillé
                    st.subheader("📋 Détails par Classe")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Aucune donnée trouvée dans la base")
                
                # Dernières entrées
                st.subheader("🕒 Dernières Entrées")
                recent_query = """
                SELECT id, label, filename, download_status, created_at 
                FROM plants_data 
                ORDER BY created_at DESC 
                LIMIT 10
                """
                
                recent_df = pd.read_sql(recent_query, connection)
                if not recent_df.empty:
                    st.dataframe(recent_df, use_container_width=True)
                
                connection.close()
                
            except Exception as e:
                st.error(f"Erreur lors de la requête: {e}")
        else:
            st.error("Impossible de se connecter à la base de données")
    
    with tab3:
        st.header("🔍 Classification d'Images")
        
        st.info("🚧 Cette fonctionnalité sera disponible après l'entraînement du modèle")
        
        # Upload d'image (simulation)
        uploaded_file = st.file_uploader(
            "Choisissez une image à classifier",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="Formats supportés: JPG, PNG, BMP"
        )
        
        if uploaded_file is not None:
            # Afficher l'image
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Image uploadée: {uploaded_file.name}", use_column_width=True)
            
            # Simuler une prédiction
            if st.button("🚀 Classifier l'image"):
                with st.spinner("Classification en cours..."):
                    import time
                    import random
                    time.sleep(2)  # Simulation
                    
                    # Prédiction simulée
                    classes = ["dandelion", "grass"]
                    predicted_class = random.choice(classes)
                    confidence = random.uniform(0.7, 0.95)
                    
                    # Afficher le résultat
                    emoji = "🌼" if predicted_class == "dandelion" else "🌱"
                    color = "#FFD700" if predicted_class == "dandelion" else "#32CD32"
                    
                    st.markdown(f"""
                    <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: {color}20; border: 2px solid {color};">
                        <h2>{emoji} {predicted_class.title()}</h2>
                        <h3>Confiance: {confidence:.1%}</h3>
                        <p><em>⚠️ Prédiction simulée - Modèle non encore entraîné</em></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab4:
        st.header("ℹ️ À propos du Projet MLOps")
        
        st.markdown("""
        ## 🎯 Objectif
        Ce projet démontre un pipeline MLOps complet pour la classification d'images,
        distinguant automatiquement les pissenlits de l'herbe.
        
        ## 🏗️ Architecture Actuelle
        - ✅ **Base de données MySQL** - Stockage des métadonnées
        - ✅ **Minio S3** - Stockage des images et modèles
        - ✅ **MLflow** - Tracking des expériences ML
        - ✅ **Prometheus** - Collecte de métriques
        - ✅ **Grafana** - Visualisation et monitoring
        - ⏳ **Airflow** - Orchestration (à configurer)
        - ⏳ **API FastAPI** - Service de prédiction (à développer)
        
        ## 🚀 Prochaines Étapes
        1. **Télécharger les données** avec `python download_data.py`
        2. **Explorer les données** avec `python data_exploration.py`
        3. **Entraîner le modèle** avec `python model_training.py`
        4. **Déployer l'API** pour les prédictions en temps réel
        
        ## 📊 Services Disponibles
        - **MLflow UI**: [http://localhost:5001](http://localhost:5001)
        - **Minio Console**: [http://localhost:9001](http://localhost:9001) (minioadmin/minioadmin123)
        - **Grafana**: [http://localhost:3000](http://localhost:3000) (admin/admin)
        - **Prometheus**: [http://localhost:9090](http://localhost:9090)
        
        ## 🛠️ Technologies Utilisées
        - **ML**: FastAI, PyTorch, MLflow
        - **Backend**: MySQL, Minio, Redis
        - **Frontend**: Streamlit
        - **Monitoring**: Prometheus, Grafana
        - **Containerisation**: Docker
        """)
        
        # Informations système
        with st.expander("Informations Techniques"):
            st.code(f"""
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Services actifs: MySQL, Minio, MLflow, Prometheus, Grafana, Redis
            Base de données: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}
            MLflow: {Config.MLFLOW_URL}
            """)

if __name__ == "__main__":
    main()
