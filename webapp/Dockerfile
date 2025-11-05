# Dockerfile pour l'application Streamlit
FROM python:3.9-slim

# Métadonnées
LABEL maintainer="MLOps Team"
LABEL description="Interface web Streamlit pour classification d'images"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Créer un utilisateur non-root
RUN groupadd -r streamlit && useradd -r -g streamlit streamlit

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
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

# Créer le fichier de configuration Streamlit
RUN mkdir -p /app/.streamlit && \
    echo '[server]\nport = 8501\naddress = "0.0.0.0"\nheadless = true\nenableCORS = false\nenableXsrfProtection = false\n[theme]\nbase = "light"\n' > /app/.streamlit/config.toml

# Changer les permissions
RUN chown -R streamlit:streamlit /app

# Passer à l'utilisateur non-root
USER streamlit

# Exposer le port
EXPOSE $STREAMLIT_SERVER_PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$STREAMLIT_SERVER_PORT/_stcore/health || exit 1

# Commande par défaut
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
