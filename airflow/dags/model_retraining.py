"""
DAG Airflow pour le retraining automatique du modèle
Pipeline MLOps - Classification Pissenlit vs Herbe
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.sql import SqlSensor
import mlflow
import mlflow.fastai
import pandas as pd
import logging
import os
from pathlib import Path

# Configuration par défaut du DAG
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

# Définition du DAG
dag = DAG(
    'model_retraining_pipeline',
    default_args=default_args,
    description='Pipeline de retraining automatique du modèle',
    schedule_interval='@weekly',  # Retraining hebdomadaire
    catchup=False,
    max_active_runs=1,
    tags=['mlops', 'retraining', 'model'],
)

def check_retraining_triggers(**context):
    """Vérifier si le retraining doit être déclenché"""
    logging.info("🔍 Vérification des triggers de retraining...")
    
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Trigger 1: Nouvelles données disponibles
    new_data_query = """
    SELECT COUNT(*) as new_images
    FROM plants_data 
    WHERE download_status = 'downloaded' 
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    new_data_count = mysql_hook.get_first(new_data_query)[0]
    
    # Trigger 2: Performance du modèle en baisse
    performance_query = """
    SELECT AVG(confidence_score) as avg_confidence
    FROM api_predictions 
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    AND response_status = 200
    """
    avg_confidence = mysql_hook.get_first(performance_query)[0] or 0.9
    
    # Trigger 3: Volume de prédictions élevé
    volume_query = """
    SELECT COUNT(*) as prediction_count
    FROM api_predictions 
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """
    prediction_volume = mysql_hook.get_first(volume_query)[0]
    
    # Critères de déclenchement
    triggers = {
        'new_data': new_data_count >= 50,  # Au moins 50 nouvelles images
        'low_confidence': avg_confidence < 0.85,  # Confiance moyenne < 85%
        'high_volume': prediction_volume >= 1000,  # Plus de 1000 prédictions
        'scheduled': True  # Retraining programmé
    }
    
    logging.info(f"📊 Triggers de retraining:")
    logging.info(f"   Nouvelles données: {new_data_count} images (trigger: {triggers['new_data']})")
    logging.info(f"   Confiance moyenne: {avg_confidence:.3f} (trigger: {triggers['low_confidence']})")
    logging.info(f"   Volume prédictions: {prediction_volume} (trigger: {triggers['high_volume']})")
    
    # Décider si le retraining doit avoir lieu
    should_retrain = any(triggers.values())
    
    logging.info(f"🎯 Décision de retraining: {'OUI' if should_retrain else 'NON'}")
    
    return {
        'should_retrain': should_retrain,
        'triggers': triggers,
        'metrics': {
            'new_data_count': new_data_count,
            'avg_confidence': avg_confidence,
            'prediction_volume': prediction_volume
        }
    }

def prepare_retraining_data(**context):
    """Préparer les données pour le retraining"""
    logging.info("📊 Préparation des données de retraining...")
    
    # Vérifier si le retraining doit avoir lieu
    trigger_result = context['task_instance'].xcom_pull(task_ids='check_triggers')
    if not trigger_result['should_retrain']:
        logging.info("⏭️ Retraining non nécessaire, arrêt du pipeline")
        return False
    
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Récupérer toutes les données disponibles
    data_query = """
    SELECT id, url_s3, label, filename, image_width, image_height
    FROM plants_data 
    WHERE download_status = 'downloaded'
    ORDER BY created_at DESC
    """
    
    df = mysql_hook.get_pandas_df(data_query)
    logging.info(f"📈 {len(df)} images disponibles pour le retraining")
    
    # Statistiques par classe
    class_distribution = df['label'].value_counts()
    logging.info(f"📊 Distribution des classes:")
    for label, count in class_distribution.items():
        logging.info(f"   {label}: {count} images")
    
    # Vérifier l'équilibre des classes
    min_class_size = class_distribution.min()
    max_class_size = class_distribution.max()
    class_ratio = max_class_size / min_class_size if min_class_size > 0 else float('inf')
    
    if class_ratio > 3.0:
        logging.warning(f"⚠️ Déséquilibre des classes détecté: ratio {class_ratio:.2f}")
    
    # Créer les splits pour le retraining
    train_data = []
    val_data = []
    test_data = []
    
    for label in df['label'].unique():
        label_data = df[df['label'] == label].sample(frac=1, random_state=42)
        n = len(label_data)
        
        train_end = int(0.7 * n)
        val_end = int(0.85 * n)
        
        train_data.extend(label_data.iloc[:train_end].to_dict('records'))
        val_data.extend(label_data.iloc[train_end:val_end].to_dict('records'))
        test_data.extend(label_data.iloc[val_end:].to_dict('records'))
    
    retraining_data = {
        'train': train_data,
        'validation': val_data,
        'test': test_data,
        'total_images': len(df),
        'class_distribution': class_distribution.to_dict(),
        'class_ratio': class_ratio,
        'trigger_info': trigger_result
    }
    
    logging.info(f"✅ Données préparées: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test")
    
    return retraining_data

def retrain_model(**context):
    """Retrainer le modèle avec les nouvelles données"""
    logging.info("🚀 Début du retraining du modèle...")
    
    # Récupérer les données de retraining
    retraining_data = context['task_instance'].xcom_pull(task_ids='prepare_data')
    if not retraining_data:
        logging.info("⏭️ Pas de données de retraining, arrêt")
        return False
    
    # Configuration MLflow
    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("dandelion-grass-retraining")
    
    with mlflow.start_run(run_name=f"retraining_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        # Logger les informations de retraining
        mlflow.log_params({
            'retraining_trigger': str(retraining_data['trigger_info']['triggers']),
            'total_images': retraining_data['total_images'],
            'train_size': len(retraining_data['train']),
            'val_size': len(retraining_data['validation']),
            'test_size': len(retraining_data['test']),
            'class_ratio': retraining_data['class_ratio'],
            'retraining_date': datetime.now().isoformat()
        })
        
        # Ici, on appellerait le script de training
        # Pour la démo, on simule le retraining
        import time
        import random
        
        logging.info("🎯 Simulation du retraining...")
        time.sleep(10)  # Simuler le temps d'entraînement
        
        # Simuler des métriques
        simulated_accuracy = random.uniform(0.88, 0.95)
        simulated_loss = random.uniform(0.1, 0.3)
        
        mlflow.log_metrics({
            'accuracy': simulated_accuracy,
            'loss': simulated_loss,
            'training_time_minutes': 10
        })
        
        # Simuler la sauvegarde du modèle
        model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = f"/tmp/model_{model_version}.pkl"
        
        # Créer un fichier modèle factice
        with open(model_path, 'w') as f:
            f.write(f"Model {model_version} - Accuracy: {simulated_accuracy:.4f}")
        
        # Logger le modèle
        mlflow.log_artifact(model_path)
        
        run_id = mlflow.active_run().info.run_id
        
        logging.info(f"✅ Retraining terminé - Run ID: {run_id}")
        logging.info(f"📊 Accuracy: {simulated_accuracy:.4f}")
        
        return {
            'model_version': model_version,
            'accuracy': simulated_accuracy,
            'loss': simulated_loss,
            'run_id': run_id,
            'model_path': model_path
        }

def evaluate_new_model(**context):
    """Évaluer le nouveau modèle par rapport à l'ancien"""
    logging.info("📊 Évaluation du nouveau modèle...")
    
    retraining_result = context['task_instance'].xcom_pull(task_ids='retrain_model')
    if not retraining_result:
        logging.info("⏭️ Pas de nouveau modèle à évaluer")
        return False
    
    # Récupérer les performances du modèle actuel en production
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    current_performance_query = """
    SELECT AVG(confidence_score) as avg_confidence
    FROM api_predictions 
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    AND response_status = 200
    """
    current_avg_confidence = mysql_hook.get_first(current_performance_query)[0] or 0.8
    
    # Comparer avec le nouveau modèle
    new_accuracy = retraining_result['accuracy']
    
    # Critères de validation
    improvement_threshold = 0.02  # Amélioration minimale de 2%
    min_accuracy_threshold = 0.85  # Accuracy minimale de 85%
    
    is_better = new_accuracy > (current_avg_confidence + improvement_threshold)
    meets_threshold = new_accuracy >= min_accuracy_threshold
    
    should_deploy = is_better and meets_threshold
    
    logging.info(f"📈 Évaluation du modèle:")
    logging.info(f"   Performance actuelle: {current_avg_confidence:.4f}")
    logging.info(f"   Nouveau modèle: {new_accuracy:.4f}")
    logging.info(f"   Amélioration: {new_accuracy - current_avg_confidence:.4f}")
    logging.info(f"   Déploiement recommandé: {'OUI' if should_deploy else 'NON'}")
    
    evaluation_result = {
        'should_deploy': should_deploy,
        'current_performance': current_avg_confidence,
        'new_performance': new_accuracy,
        'improvement': new_accuracy - current_avg_confidence,
        'meets_threshold': meets_threshold,
        'model_info': retraining_result
    }
    
    return evaluation_result

def deploy_new_model(**context):
    """Déployer le nouveau modèle si validé"""
    logging.info("🚀 Déploiement du nouveau modèle...")
    
    evaluation_result = context['task_instance'].xcom_pull(task_ids='evaluate_model')
    if not evaluation_result or not evaluation_result['should_deploy']:
        logging.info("⏭️ Nouveau modèle non validé pour le déploiement")
        return False
    
    model_info = evaluation_result['model_info']
    
    # Ici, on déploierait réellement le modèle
    # Pour la démo, on simule le déploiement
    logging.info(f"📦 Déploiement du modèle {model_info['model_version']}...")
    
    # Simuler le déploiement
    import time
    time.sleep(5)
    
    # Enregistrer le déploiement dans la base de données
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    deployment_query = """
    INSERT INTO model_deployments 
    (model_name, model_version, deployment_id, environment, deployment_status, deployed_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    mysql_hook.run(deployment_query, parameters=[
        'dandelion-grass-classifier',
        model_info['model_version'],
        deployment_id,
        'production',
        'active',
        datetime.now()
    ])
    
    logging.info(f"✅ Modèle déployé avec succès - ID: {deployment_id}")
    
    return {
        'deployment_id': deployment_id,
        'model_version': model_info['model_version'],
        'deployed_at': datetime.now().isoformat()
    }

def notify_retraining_results(**context):
    """Notifier les résultats du retraining"""
    logging.info("📧 Notification des résultats du retraining...")
    
    # Récupérer tous les résultats
    trigger_result = context['task_instance'].xcom_pull(task_ids='check_triggers')
    evaluation_result = context['task_instance'].xcom_pull(task_ids='evaluate_model')
    deployment_result = context['task_instance'].xcom_pull(task_ids='deploy_model')
    
    # Créer le rapport
    report = {
        'retraining_date': datetime.now().isoformat(),
        'triggers': trigger_result,
        'evaluation': evaluation_result,
        'deployment': deployment_result,
        'status': 'success' if deployment_result else 'no_deployment'
    }
    
    logging.info("📊 Rapport de retraining:")
    logging.info(f"   Statut: {report['status']}")
    if evaluation_result:
        logging.info(f"   Amélioration: {evaluation_result['improvement']:.4f}")
    if deployment_result:
        logging.info(f"   Modèle déployé: {deployment_result['model_version']}")
    
    # Ici, on pourrait envoyer des notifications par email, Slack, etc.
    
    return report

# Définition des tâches
check_triggers_task = PythonOperator(
    task_id='check_triggers',
    python_callable=check_retraining_triggers,
    dag=dag,
)

prepare_data_task = PythonOperator(
    task_id='prepare_data',
    python_callable=prepare_retraining_data,
    dag=dag,
)

retrain_model_task = PythonOperator(
    task_id='retrain_model',
    python_callable=retrain_model,
    dag=dag,
)

evaluate_model_task = PythonOperator(
    task_id='evaluate_model',
    python_callable=evaluate_new_model,
    dag=dag,
)

deploy_model_task = PythonOperator(
    task_id='deploy_model',
    python_callable=deploy_new_model,
    dag=dag,
)

notify_task = PythonOperator(
    task_id='notify_results',
    python_callable=notify_retraining_results,
    dag=dag,
)

# Tâche de nettoyage
cleanup_task = BashOperator(
    task_id='cleanup',
    bash_command='echo "🧹 Nettoyage des fichiers temporaires de retraining terminé"',
    dag=dag,
)

# Définition des dépendances
check_triggers_task >> prepare_data_task >> retrain_model_task >> evaluate_model_task >> deploy_model_task >> notify_task >> cleanup_task
