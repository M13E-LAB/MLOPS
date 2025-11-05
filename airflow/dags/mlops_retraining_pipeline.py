"""
DAG MLOps : Pipeline de Retraining Automatique
Auteur: M13E-LAB
Description: Pipeline complet de retraining avec monitoring et déploiement automatique
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago
import pandas as pd
import mlflow
import mlflow.pytorch
import requests
import logging
import os

# Configuration par défaut
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Configuration MLflow
MLFLOW_TRACKING_URI = "http://mlflow:5000"
MINIO_ENDPOINT = "http://minio:9000"
API_ENDPOINT = "http://mlops-api:8000"

# Définition du DAG
dag = DAG(
    'mlops_retraining_pipeline',
    default_args=default_args,
    description='Pipeline MLOps de retraining automatique',
    schedule_interval='@daily',  # Exécution quotidienne
    max_active_runs=1,
    tags=['mlops', 'retraining', 'production']
)

def check_model_performance(**context):
    """
    Vérifie les performances du modèle actuel
    Déclenche le retraining si les performances sont dégradées
    """
    logging.info("🔍 Vérification des performances du modèle...")
    
    try:
        # Simuler la vérification des métriques
        # Dans un vrai projet, on récupérerait les métriques de Prometheus
        response = requests.get(f"{API_ENDPOINT}/metrics", timeout=30)
        
        if response.status_code == 200:
            # Simuler une dégradation de performance
            current_accuracy = 0.92  # Récupérer depuis les métriques réelles
            threshold_accuracy = 0.95
            
            if current_accuracy < threshold_accuracy:
                logging.warning(f"⚠️ Performance dégradée: {current_accuracy} < {threshold_accuracy}")
                return "trigger_retraining"
            else:
                logging.info(f"✅ Performance OK: {current_accuracy}")
                return "skip_retraining"
        else:
            logging.error("❌ Impossible de récupérer les métriques")
            return "skip_retraining"
            
    except Exception as e:
        logging.error(f"❌ Erreur lors de la vérification: {str(e)}")
        return "skip_retraining"

def check_new_data(**context):
    """
    Vérifie s'il y a de nouvelles données disponibles pour le retraining
    """
    logging.info("📊 Vérification des nouvelles données...")
    
    # Simuler la vérification de nouvelles données
    # Dans un vrai projet, on vérifierait S3/Minio ou une base de données
    new_data_available = True  # Simulé pour la démo
    
    if new_data_available:
        logging.info("✅ Nouvelles données détectées")
        return "proceed_with_retraining"
    else:
        logging.info("ℹ️ Pas de nouvelles données")
        return "skip_retraining"

def prepare_training_data(**context):
    """
    Prépare les données pour l'entraînement
    """
    logging.info("🔄 Préparation des données d'entraînement...")
    
    try:
        # Simuler la préparation des données
        # Dans un vrai projet, on téléchargerait depuis S3/Minio
        
        # Créer un dataset factice pour la démo
        data_info = {
            'total_images': 1000,
            'dandelion_images': 500,
            'grass_images': 500,
            'train_split': 0.8,
            'val_split': 0.2,
            'data_version': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        
        logging.info(f"📊 Dataset préparé: {data_info}")
        
        # Stocker les infos dans XCom pour les tâches suivantes
        context['task_instance'].xcom_push(key='data_info', value=data_info)
        
        return "data_prepared_successfully"
        
    except Exception as e:
        logging.error(f"❌ Erreur lors de la préparation: {str(e)}")
        raise

def train_new_model(**context):
    """
    Entraîne un nouveau modèle avec MLflow tracking
    """
    logging.info("🤖 Démarrage de l'entraînement du nouveau modèle...")
    
    try:
        # Récupérer les infos des données
        data_info = context['task_instance'].xcom_pull(key='data_info')
        
        # Configuration MLflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        experiment_name = "automated_retraining"
        
        try:
            mlflow.create_experiment(experiment_name)
        except:
            pass  # L'expérience existe déjà
            
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run(run_name=f"retraining_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Simuler l'entraînement
            # Dans un vrai projet, on utiliserait FastAI ici
            
            # Paramètres d'entraînement
            params = {
                'learning_rate': 0.001,
                'batch_size': 32,
                'epochs': 10,
                'architecture': 'resnet34',
                'data_version': data_info['data_version']
            }
            
            # Log des paramètres
            mlflow.log_params(params)
            
            # Simuler les métriques d'entraînement
            for epoch in range(params['epochs']):
                train_loss = 0.5 - (epoch * 0.03)  # Simuler une amélioration
                val_accuracy = 0.85 + (epoch * 0.01)  # Simuler une amélioration
                
                mlflow.log_metrics({
                    'train_loss': train_loss,
                    'val_accuracy': val_accuracy,
                    'epoch': epoch
                }, step=epoch)
            
            # Métriques finales
            final_metrics = {
                'final_accuracy': 0.96,
                'final_loss': 0.15,
                'f1_score': 0.95,
                'precision': 0.94,
                'recall': 0.97
            }
            
            mlflow.log_metrics(final_metrics)
            
            # Simuler la sauvegarde du modèle
            model_path = f"models/model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            
            # Dans un vrai projet, on sauvegarderait le vrai modèle
            mlflow.log_artifact(__file__, "model_code")  # Log du code pour la démo
            
            # Enregistrer le modèle dans le Model Registry
            model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
            model_version = mlflow.register_model(
                model_uri=model_uri,
                name="dandelion_grass_classifier"
            )
            
            logging.info(f"✅ Modèle entraîné avec succès!")
            logging.info(f"📊 Accuracy finale: {final_metrics['final_accuracy']}")
            logging.info(f"🏷️ Version du modèle: {model_version.version}")
            
            # Stocker les infos du modèle pour la validation
            model_info = {
                'run_id': mlflow.active_run().info.run_id,
                'model_version': model_version.version,
                'accuracy': final_metrics['final_accuracy'],
                'model_path': model_path
            }
            
            context['task_instance'].xcom_push(key='model_info', value=model_info)
            
            return "model_trained_successfully"
            
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'entraînement: {str(e)}")
        raise

def validate_new_model(**context):
    """
    Valide le nouveau modèle avant déploiement
    """
    logging.info("🧪 Validation du nouveau modèle...")
    
    try:
        model_info = context['task_instance'].xcom_pull(key='model_info')
        
        # Critères de validation
        min_accuracy = 0.93
        current_accuracy = model_info['accuracy']
        
        if current_accuracy >= min_accuracy:
            logging.info(f"✅ Modèle validé: {current_accuracy} >= {min_accuracy}")
            return "model_validated"
        else:
            logging.warning(f"❌ Modèle rejeté: {current_accuracy} < {min_accuracy}")
            return "model_rejected"
            
    except Exception as e:
        logging.error(f"❌ Erreur lors de la validation: {str(e)}")
        raise

def deploy_new_model(**context):
    """
    Déploie le nouveau modèle en production
    """
    logging.info("🚀 Déploiement du nouveau modèle...")
    
    try:
        model_info = context['task_instance'].xcom_pull(key='model_info')
        
        # Dans un vrai projet, on mettrait à jour l'API avec le nouveau modèle
        # Ici on simule le déploiement
        
        # Transition du modèle vers "Production" dans MLflow
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = mlflow.tracking.MlflowClient()
        
        client.transition_model_version_stage(
            name="dandelion_grass_classifier",
            version=model_info['model_version'],
            stage="Production"
        )
        
        logging.info(f"✅ Modèle {model_info['model_version']} déployé en production!")
        
        # Notifier l'API du nouveau modèle (simulation)
        try:
            response = requests.post(
                f"{API_ENDPOINT}/reload_model",
                json={'model_version': model_info['model_version']},
                timeout=30
            )
            if response.status_code == 200:
                logging.info("✅ API mise à jour avec le nouveau modèle")
            else:
                logging.warning("⚠️ Impossible de notifier l'API")
        except:
            logging.warning("⚠️ API non disponible pour la notification")
        
        return "deployment_successful"
        
    except Exception as e:
        logging.error(f"❌ Erreur lors du déploiement: {str(e)}")
        raise

def send_notification(**context):
    """
    Envoie une notification de fin de pipeline
    """
    logging.info("📧 Envoi de la notification...")
    
    try:
        model_info = context['task_instance'].xcom_pull(key='model_info')
        
        # Dans un vrai projet, on enverrait un email/Slack
        notification = {
            'pipeline': 'mlops_retraining_pipeline',
            'status': 'SUCCESS',
            'model_version': model_info.get('model_version', 'N/A'),
            'accuracy': model_info.get('accuracy', 'N/A'),
            'timestamp': datetime.now().isoformat()
        }
        
        logging.info(f"📧 Notification: {notification}")
        
        return "notification_sent"
        
    except Exception as e:
        logging.error(f"❌ Erreur lors de la notification: {str(e)}")
        # Ne pas faire échouer le pipeline pour une notification
        return "notification_failed"

# Définition des tâches
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

check_performance_task = PythonOperator(
    task_id='check_model_performance',
    python_callable=check_model_performance,
    dag=dag
)

check_data_task = PythonOperator(
    task_id='check_new_data',
    python_callable=check_new_data,
    dag=dag
)

prepare_data_task = PythonOperator(
    task_id='prepare_training_data',
    python_callable=prepare_training_data,
    dag=dag
)

train_model_task = PythonOperator(
    task_id='train_new_model',
    python_callable=train_new_model,
    dag=dag
)

validate_model_task = PythonOperator(
    task_id='validate_new_model',
    python_callable=validate_new_model,
    dag=dag
)

deploy_model_task = PythonOperator(
    task_id='deploy_new_model',
    python_callable=deploy_new_model,
    dag=dag
)

notification_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag
)

skip_retraining_task = DummyOperator(
    task_id='skip_retraining',
    dag=dag
)

end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag
)

# Définition des dépendances
start_task >> [check_performance_task, check_data_task]

# Logique conditionnelle (simplifiée pour la démo)
check_performance_task >> prepare_data_task
check_data_task >> prepare_data_task

prepare_data_task >> train_model_task
train_model_task >> validate_model_task
validate_model_task >> deploy_model_task
deploy_model_task >> notification_task

# Tâches de fin
notification_task >> end_task
skip_retraining_task >> end_task
