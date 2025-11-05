# 📖 Documentation Technique MLOps

## 🎯 Vue d'ensemble du Projet

Ce projet implémente un pipeline MLOps complet pour la classification d'images binaire (pissenlit vs herbe) en utilisant les meilleures pratiques de l'industrie. L'architecture suit les principes DevOps appliqués au Machine Learning avec une approche cloud-native.

## 🏗️ Architecture Détaillée

### Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   INGRESS   │  │  SERVICES   │  │   VOLUMES   │             │
│  │             │  │             │  │             │             │
│  │ • API       │  │ • ClusterIP │  │ • PVC       │             │
│  │ • WebApp    │  │ • NodePort  │  │ • ConfigMap │             │
│  │ • Monitoring│  │ • LoadBalancer│ │ • Secrets   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                        DATA LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    MySQL    │  │    Minio    │  │   MLflow    │             │
│  │             │  │             │  │             │             │
│  │ • Metadata  │  │ • Models    │  │ • Tracking  │             │
│  │ • Users     │  │ • Artifacts │  │ • Registry  │             │
│  │ • Logs      │  │ • Data      │  │ • Experiments│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                      COMPUTE LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  FastAPI    │  │  Streamlit  │  │   Airflow   │             │
│  │             │  │             │  │             │             │
│  │ • REST API  │  │ • WebUI     │  │ • Scheduler │             │
│  │ • Swagger   │  │ • Dashboard │  │ • DAGs      │             │
│  │ • Metrics   │  │ • Monitoring│  │ • Workers   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                    MONITORING LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Prometheus  │  │   Grafana   │  │   Alerts    │             │
│  │             │  │             │  │             │             │
│  │ • Metrics   │  │ • Dashboards│  │ • Slack     │             │
│  │ • Targets   │  │ • Panels    │  │ • Email     │             │
│  │ • Rules     │  │ • Users     │  │ • PagerDuty │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration Technique

### Kubernetes Resources

#### Namespace Configuration
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mlops
  labels:
    name: mlops
    environment: production
```

#### Resource Quotas
- **CPU Total**: 4 cores
- **Memory Total**: 8Gi
- **Storage Total**: 50Gi
- **Pods Maximum**: 20

### Services Détaillés

#### 1. MySQL Database
- **Image**: `mysql:8.0`
- **Port**: `3306`
- **Storage**: `10Gi PVC`
- **Configuration**:
  - Root password: `rootpassword`
  - Database: `mlops_db`
  - User: `mlops_user`
  - Password: `mlops_password`

#### 2. Minio S3 Storage
- **Image**: `minio/minio:latest`
- **Ports**: `9000` (API), `9001` (Console)
- **Storage**: `20Gi PVC`
- **Buckets**:
  - `mlflow-artifacts`: Stockage des modèles
  - `data-lake`: Données brutes
  - `processed-data`: Données transformées

#### 3. MLflow Tracking
- **Image**: `python:3.9-slim` + MLflow 2.8.1
- **Port**: `5000`
- **Backend**: SQLite (production: MySQL)
- **Artifacts**: Local filesystem (production: S3)

#### 4. FastAPI Service
- **Image**: Custom `mlops-api-simple:latest`
- **Port**: `8000`
- **Endpoints**:
  - `GET /health`: Health check
  - `POST /predict`: Image prediction
  - `GET /metrics`: Prometheus metrics
  - `GET /docs`: Swagger documentation

#### 5. Airflow Orchestration
- **Images**: `apache/airflow:2.8.1-python3.9`
- **Components**:
  - Webserver (port 8080)
  - Scheduler
  - Workers (LocalExecutor)
- **DAGs**: Pipeline de retraining automatique

#### 6. Prometheus Monitoring
- **Image**: `prom/prometheus:latest`
- **Port**: `9090`
- **Scrape Targets**:
  - API metrics (`/metrics`)
  - Kubernetes nodes
  - Kubernetes pods

#### 7. Grafana Visualization
- **Image**: `grafana/grafana:latest`
- **Port**: `3000`
- **Credentials**: admin/admin123
- **Dashboards**: MLOps pipeline monitoring

## 🔄 Pipeline MLOps Détaillé

### 1. Data Pipeline (Airflow DAG)

```python
# Workflow automatique quotidien
start → check_performance → check_data → prepare_data → 
train_model → validate_model → deploy_model → notify → end
```

#### Étapes du Pipeline:

1. **Performance Check**
   - Récupération métriques Prometheus
   - Comparaison avec seuils définis
   - Déclenchement conditionnel du retraining

2. **Data Validation**
   - Vérification nouvelles données S3
   - Validation qualité des données
   - Calcul des statistiques

3. **Model Training**
   - Chargement des données depuis Minio
   - Entraînement FastAI/PyTorch
   - Tracking MLflow automatique
   - Sauvegarde des artefacts

4. **Model Validation**
   - Tests de performance
   - Validation croisée
   - Comparaison avec modèle actuel

5. **Deployment**
   - Transition vers "Production" dans MLflow
   - Mise à jour de l'API
   - Tests de fumée

### 2. CI/CD Pipeline (GitHub Actions)

#### Workflow Complet:
```yaml
Trigger: Push/PR → Tests → Security → Build → Deploy → Notify
```

#### Jobs Détaillés:

1. **Quality Assurance**
   ```bash
   - Code formatting (Black)
   - Import sorting (isort)
   - Linting (flake8)
   - Type checking (mypy)
   ```

2. **Testing Suite**
   ```bash
   - Unit tests (pytest)
   - Integration tests
   - API tests (httpx)
   - Coverage report
   ```

3. **Security Scanning**
   ```bash
   - Vulnerability scan (Trivy)
   - Dependency check
   - Secret detection
   - SARIF upload
   ```

4. **Docker Build**
   ```bash
   - Multi-architecture build
   - Layer caching
   - Security scanning
   - Registry push
   ```

5. **Kubernetes Deployment**
   ```bash
   - Manifest validation
   - Rolling update
   - Health checks
   - Smoke tests
   ```

## 📊 Monitoring et Observabilité

### Métriques Collectées

#### Application Metrics
- `predictions_total`: Nombre total de prédictions
- `prediction_duration_seconds`: Latence des prédictions
- `prediction_errors_total`: Erreurs de prédiction
- `model_info`: Informations sur le modèle actuel

#### Infrastructure Metrics
- CPU/Memory utilization
- Disk I/O et storage
- Network traffic
- Pod restarts et failures

#### Business Metrics
- Accuracy du modèle en temps réel
- Distribution des classes prédites
- Drift des données détecté
- Performance par période

### Alerting Rules

```yaml
# Exemple de règles Prometheus
groups:
  - name: mlops_alerts
    rules:
    - alert: ModelAccuracyDrop
      expr: model_accuracy < 0.90
      for: 5m
      annotations:
        summary: "Model accuracy dropped below 90%"
    
    - alert: APIHighLatency
      expr: prediction_duration_seconds > 1.0
      for: 2m
      annotations:
        summary: "API latency too high"
```

## 🔐 Sécurité et Bonnes Pratiques

### Kubernetes Security

1. **RBAC (Role-Based Access Control)**
   ```yaml
   - ServiceAccounts pour chaque service
   - ClusterRoles avec permissions minimales
   - NetworkPolicies pour isolation
   ```

2. **Secrets Management**
   ```yaml
   - Kubernetes Secrets pour credentials
   - ConfigMaps pour configuration
   - Pas de secrets dans le code
   ```

3. **Pod Security**
   ```yaml
   - Non-root containers
   - ReadOnlyRootFilesystem
   - Resource limits et requests
   ```

### Application Security

1. **API Security**
   - Authentication JWT (optionnel)
   - Rate limiting
   - Input validation
   - CORS configuration

2. **Data Security**
   - Encryption at rest (S3)
   - Encryption in transit (TLS)
   - Data anonymization
   - Audit logging

## 🧪 Testing Strategy

### Types de Tests

1. **Unit Tests**
   ```python
   # Tests des fonctions individuelles
   def test_image_preprocessing():
       assert preprocess_image(sample_image).shape == (224, 224, 3)
   
   def test_model_prediction():
       prediction = model.predict(test_image)
       assert prediction in ['dandelion', 'grass']
   ```

2. **Integration Tests**
   ```python
   # Tests des interactions entre composants
   def test_api_mlflow_integration():
       response = client.post("/predict", files={"file": test_image})
       assert response.status_code == 200
       # Vérifier que la prédiction est loggée dans MLflow
   ```

3. **End-to-End Tests**
   ```python
   # Tests du workflow complet
   def test_complete_pipeline():
       # Upload image → API prediction → MLflow logging → Metrics
       pass
   ```

4. **Load Tests**
   ```python
   # Tests de performance avec Locust
   class MLOpsUser(HttpUser):
       @task
       def predict_image(self):
           self.client.post("/predict", files={"file": sample_image})
   ```

## 📈 Performance et Scalabilité

### Optimisations Implémentées

1. **API Performance**
   - Async/await pour I/O non-bloquant
   - Connection pooling pour DB
   - Caching des modèles en mémoire
   - Compression des réponses

2. **Kubernetes Scaling**
   ```yaml
   # Horizontal Pod Autoscaler
   spec:
     minReplicas: 2
     maxReplicas: 10
     targetCPUUtilizationPercentage: 70
   ```

3. **Storage Optimization**
   - Persistent Volumes pour données
   - EmptyDir pour cache temporaire
   - S3 pour archivage long terme

### Métriques de Performance

- **Latence API**: < 100ms (p95)
- **Throughput**: > 100 req/sec
- **Availability**: > 99.9%
- **Model Accuracy**: > 95%

## 🔄 Disaster Recovery

### Backup Strategy

1. **Database Backups**
   ```bash
   # Backup quotidien MySQL
   kubectl exec mysql-pod -- mysqldump mlops_db > backup.sql
   ```

2. **Model Artifacts**
   ```bash
   # Synchronisation S3 vers backup
   aws s3 sync s3://mlflow-artifacts s3://mlflow-backup
   ```

3. **Configuration Backup**
   ```bash
   # Export des ConfigMaps et Secrets
   kubectl get configmaps -o yaml > configs-backup.yaml
   ```

### Recovery Procedures

1. **Service Recovery**
   - Rolling restart des pods
   - Rollback vers version précédente
   - Scaling horizontal temporaire

2. **Data Recovery**
   - Restauration depuis backup S3
   - Point-in-time recovery MySQL
   - Reconstruction des index

## 🚀 Déploiement en Production

### Checklist Pré-Production

- [ ] Tests de sécurité passés
- [ ] Performance benchmarks validés
- [ ] Monitoring configuré
- [ ] Alertes testées
- [ ] Documentation à jour
- [ ] Runbooks créés
- [ ] Backup strategy testée
- [ ] Disaster recovery testé

### Stratégie de Déploiement

1. **Blue-Green Deployment**
   - Environnement parallèle
   - Switch instantané
   - Rollback rapide

2. **Canary Deployment**
   - Déploiement progressif
   - Monitoring des métriques
   - Validation automatique

3. **Rolling Updates**
   - Mise à jour pod par pod
   - Zero-downtime deployment
   - Health checks continus

## 📚 Ressources et Références

### Documentation Officielle
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### Best Practices
- [12-Factor App Methodology](https://12factor.net/)
- [MLOps Principles](https://ml-ops.org/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

### Troubleshooting Guides
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [MLflow Troubleshooting](https://mlflow.org/docs/latest/tracking.html#troubleshooting)
- [Prometheus Troubleshooting](https://prometheus.io/docs/prometheus/latest/troubleshooting/)

---

**📧 Support**: Pour toute question technique, créer une issue sur le repository GitHub ou contacter l'équipe MLOps.
