#!/usr/bin/env python3
"""
Script pour télécharger les données du projet MLOps
Images de classification: pissenlit vs herbe
"""

import os
import requests
from pathlib import Path
import time
from tqdm import tqdm

def create_directories():
    """Créer la structure de dossiers pour les données"""
    base_dir = Path("data")
    dandelion_dir = base_dir / "dandelion"
    grass_dir = base_dir / "grass"
    
    # Créer les dossiers s'ils n'existent pas
    dandelion_dir.mkdir(parents=True, exist_ok=True)
    grass_dir.mkdir(parents=True, exist_ok=True)
    
    return dandelion_dir, grass_dir

def download_image(url, filepath, max_retries=3):
    """Télécharger une image avec gestion des erreurs"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"❌ Échec téléchargement {url}: {e}")
                return False
            time.sleep(1)  # Attendre avant de réessayer
    
    return False

def download_dataset():
    """Télécharger tout le dataset"""
    print("🚀 Début du téléchargement des données MLOps...")
    
    # Créer les dossiers
    dandelion_dir, grass_dir = create_directories()
    
    base_url = "https://raw.githubusercontent.com/btphan95/greenr-airflow/refs/heads/master/data"
    
    # Statistiques
    total_images = 400  # 200 pissenlits + 200 herbe
    downloaded = 0
    failed = 0
    
    # Télécharger les images de pissenlits
    print("🌼 Téléchargement des images de pissenlits...")
    for i in tqdm(range(200), desc="Pissenlits"):
        filename = f"{i:08d}.jpg"  # Format: 00000000.jpg
        url = f"{base_url}/dandelion/{filename}"
        filepath = dandelion_dir / filename
        
        if not filepath.exists():  # Éviter de retélécharger
            if download_image(url, filepath):
                downloaded += 1
            else:
                failed += 1
        else:
            downloaded += 1
        
        time.sleep(0.1)  # Petite pause pour éviter de surcharger le serveur
    
    # Télécharger les images d'herbe
    print("🌱 Téléchargement des images d'herbe...")
    for i in tqdm(range(200), desc="Herbe"):
        filename = f"{i:08d}.jpg"
        url = f"{base_url}/grass/{filename}"
        filepath = grass_dir / filename
        
        if not filepath.exists():
            if download_image(url, filepath):
                downloaded += 1
            else:
                failed += 1
        else:
            downloaded += 1
        
        time.sleep(0.1)
    
    # Résumé
    print(f"\n📊 Résumé du téléchargement:")
    print(f"✅ Images téléchargées: {downloaded}/{total_images}")
    print(f"❌ Échecs: {failed}")
    print(f"📁 Dossier de données: {Path('data').absolute()}")
    
    # Vérifier la structure
    dandelion_count = len(list(dandelion_dir.glob("*.jpg")))
    grass_count = len(list(grass_dir.glob("*.jpg")))
    
    print(f"\n📋 Structure finale:")
    print(f"   data/dandelion/: {dandelion_count} images")
    print(f"   data/grass/: {grass_count} images")
    
    if dandelion_count == 200 and grass_count == 200:
        print("🎉 Téléchargement complet réussi!")
    else:
        print("⚠️  Téléchargement incomplet. Relancez le script.")

if __name__ == "__main__":
    # Installer les dépendances nécessaires
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        print("📦 Installation des dépendances...")
        os.system("pip install requests tqdm")
        import requests
        from tqdm import tqdm
    
    download_dataset()
