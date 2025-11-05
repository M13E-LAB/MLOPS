# 🚀 Guide de Démarrage Rapide - MLOps Image Classification

## 📋 Résumé du Projet

Vous avez maintenant un **pipeline MLOps complet** pour la classification d'images pissenlit vs herbe ! 

### ✅ Ce qui a été créé :

1. **🔄 Pipeline de données** - Extraction et preprocessing automatisés avec Airflow
2. **🤖 Modèle ML** - Classification avec FastAI et tracking MLflow  
3. **🌐 API REST** - FastAPI avec documentation Swagger
4. **📱 Interface web** - Application Streamlit interactive
5. **🐳 Containerisation** - Docker pour API et webapp
6. **☸️ Déploiement K8s** - Manifests Kubernetes complets
7. **🔧 CI/CD** - Pipeline GitHub Actions automatisé
8. **📊 Monitoring** - Prometheus + Grafana
9. **🧪 Tests** - Tests de charge avec Locust
10. **📚 Documentation** - README complet et guides

## 🏃‍♂️ Démarrage en 5 Minutes

### 1. Prérequis
```bash
# Vérifier que vous avez :
docker --version
docker-compose --version
python3 --version
```

### 2. Démarrer l'environnement
```bash
# Rendre le script exécutable
chmod +x start.sh

# Démarrer tous les services
./start.sh dev
```

### 3. Préparer les données
```bash
# Télécharger et explorer les données
./start.sh data
```

### 4. Entraîner le modèle
```bash
# Entraîner le modèle de classification
./start.sh train
```

### 5. Tester l'API
```bash
# Tests de charge
./start.sh test
```

## 🌐 Services Disponibles

Une fois démarré, vous aurez accès à :

| Service | URL | Credentials |
|---------|-----|-------------|
| 🔍 **API Docs** | http://localhost:8000/docs | - |
| 🌐 **WebApp** | http://localhost:8501 | - |
| 🔄 **Airflow** | http://localhost:8080 | admin/admin |
| 📊 **MLflow** | http://localhost:5000 | - |
| 💾 **Minio** | http://localhost:9001 | minioadmin/minioadmin123 |
| 📈 **Grafana** | http://localhost:3000 | admin/admin |
| 🎯 **Prometheus** | http://localhost:9090 | - |

## 📁 Structure du Projet

```
📦 MLOps Image Classification
├── 🔧 Configuration
│   ├── docker-compose.dev.yml    # Services développement
│   ├── requirements.txt          # Dépendances Python
│   └── start.sh                 # Script de démarrage
├── 🌐 API & WebApp
│   ├── api/                     # API FastAPI
│   │   ├── main.py             # Point d'entrée API
│   │   ├── Dockerfile          # Image Docker
│   │   └── requirements.txt    # Dépendances API
│   └── webapp/                 # Interface Streamlit
│       ├── streamlit_app.py    # Application web
│       ├── Dockerfile          # Image Docker
│       └── requirements.txt    # Dépendances webapp
├── 🔄 Pipelines
│   └── airflow/dags/           # DAGs Airflow
│       ├── data_pipeline.py    # Pipeline données
│       └── model_retraining.py # Retraining auto
├── ☸️ Déploiement
│   ├── k8s/                    # Manifests Kubernetes
│   └── .github/workflows/      # CI/CD GitHub Actions
├── 🧪 Tests
│   └── tests/
│       ├── unit/              # Tests unitaires
│       ├── integration/       # Tests intégration
│       └── load/              # Tests de charge
├── 📊 Monitoring
│   └── monitoring/
│       ├── prometheus.yml     # Config Prometheus
│       └── grafana/          # Dashboards Grafana
├── 🤖 ML
│   ├── model_training.py      # Entraînement modèle
│   ├── data_exploration.py    # Exploration données
│   └── download_data.py       # Téléchargement données
└── 📚 Documentation
    ├── README.md              # Documentation complète
    └── QUICKSTART.md          # Ce guide
```

## 🎯 Fonctionnalités Principales

### 🔍 Classification d'Images
- Upload et classification en temps réel
- Support JPG, PNG, BMP, TIFF
- Scores de confiance détaillés
- Interface web intuitive

### 📊 Tracking & Monitoring
- Versioning automatique des modèles
- Métriques de performance trackées
- Monitoring système complet
- Alertes automatiques

### 🔄 Pipeline Automatisé
- Extraction automatique des données
- Preprocessing et validation
- Retraining basé sur triggers
- Déploiement automatique

### 🚀 Production Ready
- Containerisation Docker
- Déploiement Kubernetes
- CI/CD automatisé
- Tests de charge

## 🛠️ Commandes Utiles

```bash
# Démarrer l'environnement de développement
./start.sh dev

# Préparer les données
./start.sh data

# Entraîner le modèle
./start.sh train

# Tests de charge
./start.sh test

# Arrêter tous les services
./start.sh stop

# Nettoyer complètement
./start.sh clean

# Aide
./start.sh help
```

## 🔧 Configuration Avancée

### Variables d'Environnement
Créer un fichier `.env` :
```bash
# Base de données
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mlops_db

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# API
API_VERSION=1.0.0
MAX_FILE_SIZE=10485760
```

### Déploiement Production
```bash
# Construire les images
docker build -t your-username/mlops-api:latest ./api
docker build -t your-username/mlops-webapp:latest ./webapp

# Pousser vers Docker Hub
docker push your-username/mlops-api:latest
docker push your-username/mlops-webapp:latest

# Déployer sur Kubernetes
kubectl apply -f k8s/
```

## 🧪 Tests

### Tests Unitaires
```bash
pytest tests/unit/ -v --cov=.
```

### Tests d'Intégration
```bash
pytest tests/integration/ -v
```

### Tests de Charge
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## 📈 Monitoring

### Métriques Surveillées
- **Modèle** : Accuracy, temps de prédiction, confiance
- **API** : Taux de requêtes, temps de réponse, erreurs
- **Système** : CPU, mémoire, disque, réseau

### Dashboards Grafana
- ML Model Performance
- API Performance  
- Infrastructure Monitoring
- Business Metrics

## 🚨 Troubleshooting

### Services ne démarrent pas
```bash
# Vérifier les logs
docker-compose -f docker-compose.dev.yml logs

# Redémarrer un service spécifique
docker-compose -f docker-compose.dev.yml restart mysql
```

### Problèmes de permissions
```bash
# Fixer les permissions
sudo chown -R $USER:$USER .
chmod +x start.sh
```

### Ports occupés
```bash
# Vérifier les ports utilisés
netstat -tulpn | grep :8000

# Arrêter les services conflictuels
./start.sh stop
```

## 📞 Support

- 🐛 **Issues** : [GitHub Issues](https://github.com/your-username/mlops-image-classification/issues)
- 📖 **Documentation** : [README.md](README.md)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/your-username/mlops-image-classification/discussions)

## 🎉 Prochaines Étapes

1. **Personnaliser** le modèle avec vos propres données
2. **Configurer** les notifications (Slack, email)
3. **Ajouter** des métriques métier spécifiques
4. **Optimiser** les performances du modèle
5. **Déployer** en production sur le cloud

---

**🌟 Félicitations ! Vous avez maintenant un pipeline MLOps complet et professionnel !**

Pour toute question, consultez le [README.md](README.md) complet ou créez une issue sur GitHub.
