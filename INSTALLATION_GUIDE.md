# 🚀 Guide d'Installation MLOps

## 📋 Prérequis Système

### Logiciels Requis

| Logiciel | Version Minimale | Installation |
|----------|------------------|--------------|
| **Docker Desktop** | 4.0+ | [Download](https://www.docker.com/products/docker-desktop) |
| **Kubernetes** | 1.25+ | Activé dans Docker Desktop |
| **kubectl** | 1.25+ | [Install Guide](https://kubernetes.io/docs/tasks/tools/) |
| **Python** | 3.9+ | [Download](https://www.python.org/downloads/) |
| **Git** | 2.30+ | [Download](https://git-scm.com/downloads) |

### Configuration Système

#### Ressources Minimales
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Stockage**: 20 GB libre
- **OS**: macOS 10.15+, Windows 10+, Ubuntu 20.04+

#### Configuration Docker Desktop
```bash
# Allouer les ressources suivantes dans Docker Desktop:
CPU: 4 cores
Memory: 6 GB
Swap: 2 GB
Disk: 60 GB
```

## 🔧 Installation Étape par Étape

### Étape 1: Vérification de l'Environnement

```bash
# Vérifier Docker
docker --version
docker-compose --version

# Vérifier Kubernetes
kubectl version --client
kubectl cluster-info

# Vérifier Python
python3 --version
pip3 --version
```

**Résultat Attendu:**
```
Docker version 24.0.0+
Docker Compose version v2.20.0+
Client Version: v1.28.0+
Kubernetes control plane is running at https://127.0.0.1:6443
Python 3.9.0+
pip 23.0.0+
```

### Étape 2: Clone du Repository

```bash
# Cloner le projet
git clone https://github.com/M13E-LAB/MLOPS.git
cd MLOPS

# Vérifier la structure
ls -la
```

**Structure Attendue:**
```
MLOPS/
├── api/                    # API FastAPI
├── webapp/                 # Application Streamlit  
├── k8s/                    # Manifests Kubernetes
├── airflow/                # DAGs Airflow
├── monitoring/             # Configuration monitoring
├── tests/                  # Tests automatisés
├── docker-compose.dev.yml  # Environnement dev
├── requirements.txt        # Dépendances Python
└── README.md              # Documentation
```

### Étape 3: Installation des Dépendances Python

```bash
# Créer un environnement virtuel (recommandé)
python3 -m venv mlops-env
source mlops-env/bin/activate  # Linux/macOS
# ou
mlops-env\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Vérifier l'installation
pip list | grep -E "(fastai|mlflow|fastapi)"
```

### Étape 4: Téléchargement des Données

```bash
# Télécharger le dataset d'images
python3 download_data.py

# Vérifier les données
ls -la data/
```

**Résultat Attendu:**
```
data/
├── dandelion/     # 200 images de pissenlits
└── grass/         # 200 images d'herbe
```

### Étape 5: Entraînement du Modèle Initial

```bash
# Entraîner le modèle FastAI
python3 model_training.py

# Vérifier le modèle généré
ls -la *.pkl
```

**Résultat Attendu:**
```
model.pkl          # Modèle entraîné FastAI
```

## ☸️ Déploiement Kubernetes

### Étape 6: Préparation de Kubernetes

```bash
# Vérifier que Kubernetes est actif
kubectl get nodes

# Créer le namespace MLOps
kubectl apply -f k8s/namespace.yaml

# Vérifier la création
kubectl get namespaces | grep mlops
```

### Étape 7: Déploiement de l'Infrastructure

```bash
# Déployer dans l'ordre suivant:

# 1. Base de données
kubectl apply -f k8s/mysql-deployment.yaml

# 2. Stockage S3
kubectl apply -f k8s/minio-deployment.yaml

# 3. Tracking ML
kubectl apply -f k8s/mlflow-simple-deployment.yaml

# 4. Monitoring
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana-deployment.yaml

# 5. Orchestration
kubectl apply -f k8s/airflow-deployment.yaml

# 6. Applications
kubectl apply -f k8s/api-simple-deployment.yaml
kubectl apply -f k8s/webapp-deployment.yaml
```

### Étape 8: Vérification du Déploiement

```bash
# Vérifier tous les pods
kubectl get pods -n mlops

# Attendre que tous soient "Running"
kubectl wait --for=condition=ready pod --all -n mlops --timeout=300s

# Vérifier les services
kubectl get services -n mlops
```

**État Final Attendu:**
```
NAME                                 READY   STATUS    RESTARTS   AGE
airflow-scheduler-xxx                1/1     Running   0          5m
airflow-webserver-xxx                1/1     Running   0          5m
grafana-xxx                          1/1     Running   0          5m
minio-xxx                            1/1     Running   0          5m
mlflow-simple-xxx                    1/1     Running   0          5m
mlops-api-xxx                        1/1     Running   0          5m
mysql-xxx                            1/1     Running   0          5m
prometheus-xxx                       1/1     Running   0          5m
```

## 🌐 Accès aux Services

### Étape 9: Configuration des Port-Forwards

```bash
# Créer les tunnels d'accès (dans des terminaux séparés)

# API FastAPI
kubectl port-forward -n mlops service/mlops-api 8000:8000 &

# MLflow Tracking
kubectl port-forward -n mlops service/mlflow-simple 5001:5000 &

# Prometheus Monitoring  
kubectl port-forward -n mlops service/prometheus 9090:9090 &

# Grafana Dashboards
kubectl port-forward -n mlops service/grafana 3000:3000 &

# Airflow Orchestration
kubectl port-forward -n mlops service/airflow-webserver 8080:8080 &

# Minio Console
kubectl port-forward -n mlops service/minio-console 9001:9001 &
```

### Étape 10: Tests de Connectivité

```bash
# Tester chaque service
curl http://localhost:8000/health     # API
curl http://localhost:5001/           # MLflow
curl http://localhost:9090/           # Prometheus
curl http://localhost:3000/api/health # Grafana
curl http://localhost:8080/health     # Airflow
```

## 🎯 Accès aux Interfaces Web

### URLs et Credentials

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **API Swagger** | http://localhost:8000/docs | - | Documentation API interactive |
| **MLflow UI** | http://localhost:5001 | - | Tracking des expériences ML |
| **Prometheus** | http://localhost:9090 | - | Métriques et monitoring |
| **Grafana** | http://localhost:3000 | admin/admin123 | Dashboards et visualisation |
| **Airflow** | http://localhost:8080 | admin/admin123 | Orchestration des pipelines |
| **Minio Console** | http://localhost:9001 | minioadmin/minioadmin | Gestion du stockage S3 |

### Première Connexion

#### Grafana Setup
1. Aller sur http://localhost:3000
2. Login: `admin` / Password: `admin123`
3. Le dashboard MLOps est pré-configuré
4. Vérifier la connexion à Prometheus

#### Airflow Setup
1. Aller sur http://localhost:8080
2. Login: `admin` / Password: `admin123`
3. Activer le DAG `mlops_retraining_pipeline`
4. Déclencher une exécution manuelle

## 🧪 Tests et Validation

### Test de l'API

```bash
# Test de santé
curl http://localhost:8000/health

# Test de prédiction avec une image
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/dandelion/00000001.jpg"
```

**Réponse Attendue:**
```json
{
  "prediction": "dandelion",
  "confidence": 0.95,
  "model_version": "simple-v1.0",
  "timestamp": "2025-11-05T15:30:00"
}
```

### Test du Pipeline Airflow

```bash
# Déclencher le DAG via API
curl -X POST "http://localhost:8080/api/v1/dags/mlops_retraining_pipeline/dagRuns" \
     -H "Content-Type: application/json" \
     -u "admin:admin123" \
     -d '{"conf": {}}'
```

### Test des Métriques

```bash
# Vérifier les métriques Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Vérifier les métriques de l'API
curl http://localhost:8000/metrics
```

## 🔧 Dépannage

### Problèmes Courants

#### 1. Pods en Status "Pending"
```bash
# Diagnostiquer
kubectl describe pod <pod-name> -n mlops

# Solutions courantes:
# - Vérifier les ressources disponibles
# - Vérifier les PersistentVolumeClaims
# - Vérifier les StorageClass
```

#### 2. Services Inaccessibles
```bash
# Vérifier les port-forwards
ps aux | grep "port-forward"

# Redémarrer les port-forwards
pkill -f "port-forward"
# Puis relancer les commandes de l'étape 9
```

#### 3. MLflow ne démarre pas
```bash
# Vérifier les logs
kubectl logs -n mlops deployment/mlflow-simple

# Redémarrer si nécessaire
kubectl rollout restart deployment/mlflow-simple -n mlops
```

#### 4. Airflow en erreur
```bash
# Vérifier les logs
kubectl logs -n mlops deployment/airflow-webserver
kubectl logs -n mlops deployment/airflow-scheduler

# Vérifier la base de données
kubectl exec -it -n mlops deployment/mysql -- mysql -u root -p
```

### Commandes de Diagnostic

```bash
# État général du cluster
kubectl get all -n mlops

# Utilisation des ressources
kubectl top nodes
kubectl top pods -n mlops

# Événements récents
kubectl get events -n mlops --sort-by='.lastTimestamp'

# Logs détaillés
kubectl logs -f -n mlops deployment/<service-name>
```

## 🔄 Mise à Jour et Maintenance

### Mise à Jour des Images

```bash
# Reconstruire les images locales
docker build -t mlops-api-simple:latest api/
docker build -t mlops-webapp:latest webapp/

# Redéployer
kubectl rollout restart deployment/mlops-api -n mlops
kubectl rollout restart deployment/mlops-webapp -n mlops
```

### Sauvegarde des Données

```bash
# Backup MySQL
kubectl exec -n mlops deployment/mysql -- mysqldump -u root -p mlops_db > backup.sql

# Backup Minio (si configuré avec volumes)
kubectl cp mlops/minio-pod:/data ./minio-backup/
```

### Nettoyage

```bash
# Supprimer tout le namespace (ATTENTION: Perte de données)
kubectl delete namespace mlops

# Supprimer seulement les applications
kubectl delete -f k8s/api-simple-deployment.yaml
kubectl delete -f k8s/webapp-deployment.yaml
```

## 📞 Support

### Ressources d'Aide

- **Documentation**: Voir `DOCUMENTATION_TECHNIQUE.md`
- **Issues GitHub**: [Repository Issues](https://github.com/M13E-LAB/MLOPS/issues)
- **Logs**: Utiliser `kubectl logs` pour diagnostiquer

### Contacts

- **Équipe MLOps**: Créer une issue GitHub
- **Support Technique**: Voir la documentation officielle des outils

---

**🎉 Félicitations !** Votre environnement MLOps est maintenant opérationnel !

Pour aller plus loin, consultez la `DOCUMENTATION_TECHNIQUE.md` pour les détails avancés.
