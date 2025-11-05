# Dockerfile pour l'API FastAPI
FROM python:3.9-slim

# Métadonnées
LABEL maintainer="MLOps Team"
LABEL description="API FastAPI pour classification d'images pissenlit vs herbe"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_PORT=8000

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r mlops && useradd -r -g mlops mlops

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p models logs && \
    chown -R mlops:mlops /app

# Passer à l'utilisateur non-root
USER mlops

# Exposer le port
EXPOSE $API_PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$API_PORT/health || exit 1

# Commande par défaut
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
