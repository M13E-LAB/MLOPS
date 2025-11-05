#!/usr/bin/env python3
"""
Script simple pour lancer MLflow localement
"""
import os
import subprocess
import sys
from pathlib import Path

def install_mlflow():
    """Installer MLflow si nécessaire"""
    try:
        import mlflow
        print("✅ MLflow déjà installé")
        return True
    except ImportError:
        print("📦 Installation de MLflow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mlflow", "boto3"])
        return True

def setup_directories():
    """Créer les dossiers nécessaires"""
    mlflow_dir = Path("mlflow_local")
    mlflow_dir.mkdir(exist_ok=True)
    
    artifacts_dir = mlflow_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    return mlflow_dir, artifacts_dir

def run_mlflow_server(mlflow_dir, artifacts_dir):
    """Lancer le serveur MLflow"""
    print("🚀 Lancement de MLflow sur http://localhost:5001")
    
    # Variables d'environnement
    env = os.environ.copy()
    env.update({
        "MLFLOW_S3_ENDPOINT_URL": "http://localhost:9000",
        "AWS_ACCESS_KEY_ID": "minioadmin",
        "AWS_SECRET_ACCESS_KEY": "minioadmin123"
    })
    
    # Commande MLflow
    cmd = [
        sys.executable, "-m", "mlflow", "server",
        "--backend-store-uri", f"sqlite:///{mlflow_dir}/mlflow.db",
        "--default-artifact-root", str(artifacts_dir),
        "--host", "0.0.0.0",
        "--port", "5001"
    ]
    
    print(f"💻 Commande: {' '.join(cmd)}")
    subprocess.run(cmd, env=env)

def main():
    """Fonction principale"""
    print("🔧 Configuration de MLflow local...")
    
    if not install_mlflow():
        print("❌ Erreur lors de l'installation de MLflow")
        return 1
    
    mlflow_dir, artifacts_dir = setup_directories()
    print(f"📁 Dossier MLflow: {mlflow_dir.absolute()}")
    print(f"📁 Dossier artifacts: {artifacts_dir.absolute()}")
    
    try:
        run_mlflow_server(mlflow_dir, artifacts_dir)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de MLflow")
        return 0
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
