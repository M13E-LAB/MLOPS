"""
DAG Airflow pour l'extraction et le preprocessing des données
Pipeline MLOps - Classification Pissenlit vs Herbe
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import requests
import pandas as pd
from PIL import Image
import io
import hashlib
import logging
import os
from pathlib import Path

# Configuration par défaut du DAG
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Définition du DAG
dag = DAG(
    'data_extraction_pipeline',
    default_args=default_args,
    description='Pipeline d\'extraction et preprocessing des données d\'images',
    schedule_interval='@daily',  # Exécution quotidienne
    catchup=False,
    max_active_runs=1,
    tags=['mlops', 'data', 'preprocessing'],
)

def extract_data_from_db(**context):
    """Extraire les métadonnées des images depuis la base de données"""
    logging.info("🔍 Extraction des données depuis la base de données...")
    
    # Connexion à MySQL
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Requête pour récupérer les images non téléchargées
    query = """
    SELECT id, url_source, label, filename 
    FROM plants_data 
    WHERE download_status = 'pending' 
    ORDER BY id 
    LIMIT 50
    """
    
    df = mysql_hook.get_pandas_df(query)
    logging.info(f"📊 {len(df)} images à traiter")
    
    # Sauvegarder dans XCom pour les tâches suivantes
    return df.to_json(orient='records')

def download_and_process_images(**context):
    """Télécharger et traiter les images"""
    logging.info("📥 Téléchargement et traitement des images...")
    
    # Récupérer les données depuis XCom
    data_json = context['task_instance'].xcom_pull(task_ids='extract_data')
    if not data_json:
        logging.info("Aucune donnée à traiter")
        return
    
    import json
    data = json.loads(data_json)
    
    # Configuration S3/Minio
    s3_hook = S3Hook(aws_conn_id='minio_default')
    bucket_name = 'mlops-images'
    
    # Créer le bucket s'il n'existe pas
    if not s3_hook.check_for_bucket(bucket_name):
        s3_hook.create_bucket(bucket_name)
        logging.info(f"✅ Bucket {bucket_name} créé")
    
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    processed_count = 0
    failed_count = 0
    
    for item in data:
        try:
            # Télécharger l'image
            response = requests.get(item['url_source'], timeout=30)
            response.raise_for_status()
            
            # Vérifier que c'est bien une image
            image = Image.open(io.BytesIO(response.content))
            width, height = image.size
            file_size = len(response.content)
            
            # Générer le hash du fichier
            file_hash = hashlib.md5(response.content).hexdigest()
            
            # Chemin S3
            s3_key = f"{item['label']}/{item['filename']}"
            
            # Uploader vers S3/Minio
            s3_hook.load_bytes(
                bytes_data=response.content,
                key=s3_key,
                bucket_name=bucket_name,
                replace=True
            )
            
            # URL S3
            s3_url = f"s3://{bucket_name}/{s3_key}"
            
            # Mettre à jour la base de données
            update_query = """
            UPDATE plants_data 
            SET url_s3 = %s, 
                file_size = %s, 
                image_width = %s, 
                image_height = %s,
                download_status = 'downloaded',
                updated_at = NOW()
            WHERE id = %s
            """
            
            mysql_hook.run(update_query, parameters=[
                s3_url, file_size, width, height, item['id']
            ])
            
            processed_count += 1
            logging.info(f"✅ {item['filename']} traité avec succès")
            
        except Exception as e:
            logging.error(f"❌ Erreur avec {item['filename']}: {str(e)}")
            
            # Marquer comme échoué dans la DB
            error_query = """
            UPDATE plants_data 
            SET download_status = 'failed',
                updated_at = NOW()
            WHERE id = %s
            """
            mysql_hook.run(error_query, parameters=[item['id']])
            failed_count += 1
    
    logging.info(f"📊 Résumé: {processed_count} succès, {failed_count} échecs")
    return {'processed': processed_count, 'failed': failed_count}

def validate_data_quality(**context):
    """Valider la qualité des données téléchargées"""
    logging.info("🔍 Validation de la qualité des données...")
    
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Statistiques générales
    stats_query = """
    SELECT 
        label,
        download_status,
        COUNT(*) as count,
        AVG(file_size) as avg_file_size,
        AVG(image_width) as avg_width,
        AVG(image_height) as avg_height
    FROM plants_data 
    GROUP BY label, download_status
    """
    
    df_stats = mysql_hook.get_pandas_df(stats_query)
    logging.info("📊 Statistiques par classe et statut:")
    logging.info(df_stats.to_string())
    
    # Vérifications de qualité
    quality_checks = []
    
    # Check 1: Images trop petites
    small_images_query = """
    SELECT COUNT(*) as count 
    FROM plants_data 
    WHERE download_status = 'downloaded' 
    AND (image_width < 50 OR image_height < 50)
    """
    small_count = mysql_hook.get_first(small_images_query)[0]
    quality_checks.append(f"Images trop petites: {small_count}")
    
    # Check 2: Équilibre des classes
    balance_query = """
    SELECT label, COUNT(*) as count 
    FROM plants_data 
    WHERE download_status = 'downloaded' 
    GROUP BY label
    """
    balance_df = mysql_hook.get_pandas_df(balance_query)
    if len(balance_df) == 2:
        ratio = balance_df['count'].max() / balance_df['count'].min()
        quality_checks.append(f"Ratio déséquilibre classes: {ratio:.2f}")
    
    # Check 3: Taux de succès du téléchargement
    success_query = """
    SELECT 
        download_status,
        COUNT(*) as count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM plants_data), 2) as percentage
    FROM plants_data 
    GROUP BY download_status
    """
    success_df = mysql_hook.get_pandas_df(success_query)
    logging.info("📈 Taux de succès du téléchargement:")
    logging.info(success_df.to_string())
    
    # Retourner les résultats
    return {
        'quality_checks': quality_checks,
        'stats': df_stats.to_dict('records'),
        'success_rates': success_df.to_dict('records')
    }

def prepare_training_data(**context):
    """Préparer les données pour l'entraînement"""
    logging.info("🎯 Préparation des données d'entraînement...")
    
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Récupérer toutes les images téléchargées avec succès
    query = """
    SELECT id, url_s3, label, filename, image_width, image_height, file_size
    FROM plants_data 
    WHERE download_status = 'downloaded'
    ORDER BY label, id
    """
    
    df = mysql_hook.get_pandas_df(query)
    logging.info(f"📊 {len(df)} images disponibles pour l'entraînement")
    
    # Statistiques par classe
    class_stats = df.groupby('label').agg({
        'id': 'count',
        'file_size': ['mean', 'std'],
        'image_width': ['mean', 'std'],
        'image_height': ['mean', 'std']
    }).round(2)
    
    logging.info("📈 Statistiques par classe:")
    logging.info(class_stats.to_string())
    
    # Créer les splits train/validation/test (70/15/15)
    train_data = []
    val_data = []
    test_data = []
    
    for label in df['label'].unique():
        label_data = df[df['label'] == label].sample(frac=1, random_state=42)  # Mélanger
        n = len(label_data)
        
        train_end = int(0.7 * n)
        val_end = int(0.85 * n)
        
        train_data.extend(label_data.iloc[:train_end].to_dict('records'))
        val_data.extend(label_data.iloc[train_end:val_end].to_dict('records'))
        test_data.extend(label_data.iloc[val_end:].to_dict('records'))
    
    logging.info(f"📊 Splits créés: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")
    
    # Sauvegarder les métadonnées des splits
    splits_data = {
        'train': train_data,
        'validation': val_data,
        'test': test_data,
        'stats': class_stats.to_dict(),
        'total_images': len(df)
    }
    
    return splits_data

def trigger_model_training(**context):
    """Déclencher l'entraînement du modèle si les données sont prêtes"""
    logging.info("🚀 Vérification si l'entraînement peut être déclenché...")
    
    # Récupérer les données des splits
    splits_data = context['task_instance'].xcom_pull(task_ids='prepare_training_data')
    
    if not splits_data:
        logging.warning("Aucune donnée d'entraînement disponible")
        return False
    
    train_size = len(splits_data['train'])
    val_size = len(splits_data['validation'])
    
    # Critères pour déclencher l'entraînement
    min_train_size = 100  # Minimum 100 images d'entraînement
    min_val_size = 20     # Minimum 20 images de validation
    
    if train_size >= min_train_size and val_size >= min_val_size:
        logging.info(f"✅ Critères remplis: Train={train_size}, Val={val_size}")
        logging.info("🎯 Déclenchement de l'entraînement du modèle...")
        
        # Ici, on pourrait déclencher un autre DAG pour l'entraînement
        # ou envoyer un signal à un service externe
        
        return True
    else:
        logging.warning(f"❌ Critères non remplis: Train={train_size}, Val={val_size}")
        return False

# Définition des tâches
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data_from_db,
    dag=dag,
)

download_task = PythonOperator(
    task_id='download_and_process_images',
    python_callable=download_and_process_images,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

prepare_task = PythonOperator(
    task_id='prepare_training_data',
    python_callable=prepare_training_data,
    dag=dag,
)

trigger_task = PythonOperator(
    task_id='trigger_model_training',
    python_callable=trigger_model_training,
    dag=dag,
)

# Tâche de nettoyage (optionnelle)
cleanup_task = BashOperator(
    task_id='cleanup_temp_files',
    bash_command='echo "🧹 Nettoyage des fichiers temporaires terminé"',
    dag=dag,
)

# Définition des dépendances
extract_task >> download_task >> validate_task >> prepare_task >> trigger_task >> cleanup_task
